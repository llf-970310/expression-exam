from mongoengine import ValidationError

from errors import *
from manager import exam_manager, report_manager
from exam.ttypes import *


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
