from mongoengine import ValidationError

import util
from errors import *
from manager import exam_manager, report_manager
from exam.ttypes import *
from model.exam import HistoryTestModel, CurrentTestModel


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
