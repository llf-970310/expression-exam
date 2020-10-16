import datetime
import logging
import random
import time

from mongoengine import ValidationError

import util
from config import ExamConfig
from errors import *
from manager import exam_manager, report_manager
from exam.ttypes import *
from manager.exam_manager import ExamType
from model.exam import HistoryTestModel, CurrentTestModel, WavPretestModel


def get_exam_report(exam_id) -> (ExamReport, ExamScore):
    try:
        test = exam_manager.get_exam_by_id(exam_id)
        if test is None:
            raise ExamNotExist
    except ValidationError:
        raise InvalidParam

    questions = test['questions']
    handling, score, feature = exam_manager.get_score_and_feature(questions)
    if handling:
        raise InProcessing
    else:
        report = report_manager.generate_report(feature, score, test.paper_type)
        score = ExamScore(
            total=test['score_info']['total'],
            quality=test['score_info']['音质'],
            key=test['score_info']['主旨'],
            detail=test['score_info']['细节'],
            structure=test['score_info']['结构'],
            logic=test['score_info']['逻辑']
        )
        return report, score


def compute_exam_score(exam_id) -> ExamScore:
    try:
        test = exam_manager.get_exam_by_id(exam_id)
        if test is None:
            raise ExamNotExist
    except ValidationError:
        raise InvalidParam

    if test["score_info"]:  # 数据库有成绩信息 => 直接返回
        score = ExamScore(
            total=test['score_info']['total'], quality=test['score_info']['音质'], key=test['score_info']['主旨'],
            detail=test['score_info']['细节'], structure=test['score_info']['结构'], logic=test['score_info']['逻辑']
        )
    elif isinstance(test, HistoryTestModel):  # 没成绩信息，但是 history test => 返回 0
        score = ExamScore(total=0, quality=0, key=0, detail=0, structure=0, logic=0)
    elif exam_manager.question_all_finished(test["questions"]):  # 没成绩信息，是 current test，题目全部结束 => 计算成绩
        tmp_dict = {}
        for k, v in test["questions"].items():
            tmp_dict[int(k)] = v['score']
        test['score_info'] = exam_manager.compute_exam_score(tmp_dict, test.paper_type)
        test.save()

        score = ExamScore(
            total=test['score_info']['total'], quality=test['score_info']['音质'], key=test['score_info']['主旨'],
            detail=test['score_info']['细节'], structure=test['score_info']['结构'], logic=test['score_info']['逻辑']
        )
    else:  # 没成绩信息，是 current test，还有题目在处理中 => 抛出异常
        raise InProcessing

    return score


def get_exam_record(user_id: str, template_id: str) -> list:
    if not template_id:  # 全部历史成绩
        history_scores_origin = HistoryTestModel.objects(user_id=user_id).order_by("test_start_time")
        current_scores_origin = CurrentTestModel.objects(user_id=user_id).order_by("test_start_time")
    else:  # 查看指定模板的历史成绩
        history_scores_origin = HistoryTestModel.objects(user_id=user_id, paper_tpl_id=template_id).order_by(
            "test_start_time")
        current_scores_origin = CurrentTestModel.objects(user_id=user_id, paper_tpl_id=template_id).order_by(
            "test_start_time")

    exam_list = []
    for history in history_scores_origin:
        try:
            exam_list.append(ExamRecord(
                examStartTime=util.datetime_to_str(history["test_start_time"]),
                templateId=history["paper_tpl_id"],
                examId=history["current_id"],
                scoreInfo=compute_exam_score(history["current_id"])
            ))
        except InProcessing:
            pass

    for current in current_scores_origin:
        try:
            exam_list.append(ExamRecord(
                examStartTime=util.datetime_to_str(current["test_start_time"]),
                templateId=current["paper_tpl_id"],
                examId=str(current["id"]),
                scoreInfo=compute_exam_score(str(current["id"]))
            ))
        except InProcessing:
            pass

    return exam_list


def init_new_audio_test(user_id: str) -> QuestionInfo:
    wav_test = WavPretestModel()
    wav_test['text'] = ExamConfig.audio_test["content"]
    wav_test['user_id'] = user_id
    wav_test.save()

    return QuestionInfo(
        id=str(wav_test.id),
        content=wav_test['text'],
        type=0,
        readLimitTime=ExamConfig.question_prepare_time[0],
        answerLimitTime=ExamConfig.question_limit_time[0],
        questionTip={
            "detail": ExamConfig.audio_test['detail'],
            "tip": ExamConfig.audio_test['tip'],
        }
    )


def get_question_info(exam_id: str, question_num: int) -> QuestionInfo:
    # get test
    test = CurrentTestModel.objects(id=exam_id).first()
    if test is None:
        raise ExamNotExist

    # 如果超出最大题号
    if question_num > len(test.questions):
        raise ExamFinished

    question = test.questions[str(question_num)]

    result = QuestionInfo(
        id=question.q_id,
        content=question.q_text,
        type=question.q_type,
        readLimitTime=ExamConfig.question_prepare_time[question.q_type],
        answerLimitTime=ExamConfig.question_limit_time[question.q_type],
        questionTip=ExamConfig.question_type_tip[question.q_type],
        questionNum=question_num,
        isLastQuestion=(question_num == len(test.questions)),
        examTime=(test.test_expire_time - test.test_start_time).seconds,
        examLeftTime=(test.test_expire_time - datetime.datetime.utcnow()).total_seconds()
    )

    # update and save
    question.status = 'question_fetched'
    test.current_q_num = question_num
    test.save()

    return result


def get_file_upload_path(exam_id: str, user_id: str, question_num: int = None) -> str:
    if question_num:  # real_exam
        exam = CurrentTestModel.objects(id=exam_id).first()
    else:  # audio_test
        exam = WavPretestModel.objects(id=exam_id).first()

    if not exam:
        logging.error("[get_file_upload_path] no such test! test id: %s" % exam_id)
        raise ExamNotExist

    if question_num:
        try:
            question = exam.questions[str(question_num)]
        except Exception as e:
            logging.error("[get_file_upload_path] GetEmbeddedQuestionException. question_num: "
                          "%s, exam_id: %s. exception:\n%s" % (question_num, exam_id, repr(e)))
            raise GetQuestionFailed

        upload_path = question.wav_upload_url if question.wav_upload_url \
            else exam_manager.generate_upload_path(ExamType.RealExam, user_id)
        question.wav_upload_url = upload_path
        question.file_location = 'BOS'
        question.status = 'url_fetched'
    else:
        upload_path = exam_manager.generate_upload_path(ExamType.AudioTest, user_id)
        exam.wav_upload_url = upload_path
        exam.file_location = 'BOS'

    exam.save()
    logging.info("[get_file_upload_path] exam_id: %s, upload_path: %s, user_id: %s" % (exam_id, upload_path, user_id))

    return upload_path
