import datetime
import json
import logging
import random
import time

import Levenshtein
from mongoengine import ValidationError

import util
from config import ExamConfig
from errors import *
from manager import exam_manager, report_manager
from exam.ttypes import *
from manager.exam_manager import ExamType
from model.exam import HistoryTestModel, CurrentTestModel, WavPretestModel
from model.paper_template import PaperTemplate


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

    score = exam_manager.get_exam_score(test)
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
                scoreInfo=exam_manager.get_exam_score(history)
            ))
        except InProcessing:
            pass

    for current in current_scores_origin:
        try:
            exam_list.append(ExamRecord(
                examStartTime=util.datetime_to_str(current["test_start_time"]),
                templateId=current["paper_tpl_id"],
                examId=str(current["id"]),
                scoreInfo=exam_manager.get_exam_score(current)
            ))
        except InProcessing:
            pass

    return exam_list


def init_new_audio_test(user_id: str) -> QuestionInfo:
    return QuestionInfo(
        content=ExamConfig.audio_test["content"],
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


def get_file_upload_path(exam_id: str = "audio_test", user_id: str = None, question_num: int = None) -> str:
    if question_num:  # real_exam
        exam = CurrentTestModel.objects(id=exam_id).first()
        if not exam:
            logging.error("[get_file_upload_path] no such test! test id: %s" % exam_id)
            raise ExamNotExist
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
        exam.save()
    else:  # audio_test
        upload_path = exam_manager.generate_upload_path(ExamType.AudioTest, user_id)

    logging.info("[get_file_upload_path] exam_id: %s, upload_path: %s, user_id: %s" % (exam_id, upload_path, user_id))

    return upload_path


def init_new_exam(user_id: str, template_id: str) -> str:
    exam_id = exam_manager.init_paper(user_id, template_id)
    logging.debug('[init_new_exam] user_id: %s, exam_id: %s' % (user_id, exam_id))
    if not exam_id:
        logging.error('[init_new_exam] init new exam failed. user_id: %s, tpl_id: %s' % (user_id, template_id))
        raise InitExamFailed

    return exam_id


def get_paper_template(template_id: str) -> list:
    if template_id is None:
        all_templates = PaperTemplate.objects()
        tpl_lst = []
        for tpl in all_templates:
            d = ExamTemplate(
                id=str(tpl.id),
                name=tpl.name,
                description=json.dumps(tpl.questions),
                questionCount=len(tpl.questions),
                isDeprecated=tpl.deprecated,
                duration=tpl.duration
            )
            tpl_lst.append(d)
        return tpl_lst
    else:
        template_item = PaperTemplate.objects(id=template_id).first()
        tmp = ExamTemplate(
            id=str(template_item.id), name=template_item.name,
            description=template_item.desc, questionCount=len(template_item.questions)
        )
        return [tmp]


def get_audio_test_result(exam_id: str) -> (bool, float):
    audio_test = WavPretestModel.objects(id=exam_id).first()
    if audio_test is None:
        raise ExamNotExist
    status = audio_test['result']['status']
    if status == 'handling':
        raise InProcessing
    elif status == 'finished':
        rcg_text = audio_test['result']['feature']['rcg_text']
        lev_ratio = Levenshtein.ratio(rcg_text, audio_test['text'])
        return True, lev_ratio
    else:
        return False, 0


def get_exam_result(exam_id: str) -> (ExamScore, ExamReport):
    try:
        test = exam_manager.get_exam_by_id(exam_id)
        if test is None:
            raise ExamNotExist
    except ValidationError:
        raise InvalidParam

    questions = test['questions']
    handling, score, feature = exam_manager.get_score_and_feature(questions)

    # 判断该测试是否已经超时
    is_exam_expire = datetime.datetime.utcnow() > test.test_expire_time
    logging.info("[get_exam_result] is_exam_expire: %s, exam_id: %s" % (str(is_exam_expire), exam_id))

    # 如果回答完问题或超时但已处理完，则计算得分，否则返回正在处理
    if (len(score) == len(questions)) or (is_exam_expire and not handling):
        if not test['score_info']:
            logging.info("[get_exam_result] first compute score. exam_id: %s" % exam_id)
            test['score_info'] = exam_manager.compute_exam_score(score, test.paper_type)
            test.save()
        else:
            logging.info("[get_exam_result] use computed score. exam_id: %s" % exam_id)

        exam_score = ExamScore(
            total=test['score_info']['total'], quality=test['score_info']['音质'], key=test['score_info']['主旨'],
            detail=test['score_info']['细节'], structure=test['score_info']['结构'], logic=test['score_info']['逻辑']
        )
        exam_report = report_manager.generate_report(feature, score, test.paper_type)

        return exam_score, exam_report
    else:
        return InProcessing


def save_paper_template(new_template: ExamTemplate):
    # modify
    if new_template.id:
        template = PaperTemplate.objects(id=new_template.id).first()
        if not template:
            raise TemplateNotExist

        # 禁用模板
        if new_template.isDeprecated is not None:
            template.update(deprecated=new_template.isDeprecated)
        # 修改信息
        else:
            try:
                question_list = json.loads(new_template.description)
            except Exception:
                logging.error(
                    "[save_paper_template] json.loads() failed. paper template desc: " + new_template.description)
                raise InternalError

            template.update(
                name=new_template.name,
                duration=new_template.duration,
                questions=question_list
            )
    # add
    else:
        try:
            question_list = json.loads(new_template.description)
        except Exception:
            logging.error("[save_paper_template] json.loads() failed. paper template desc: " + new_template.description)
            raise InternalError

        new_template = PaperTemplate(
            name=new_template.name,
            deprecated=False,
            duration=new_template.duration,
            questions=question_list
        )
        new_template.save()
