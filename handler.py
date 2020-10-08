import time

import jwt

from exam.ttypes import *
import service
from errors import *


def get_exam_report(request: GetExamReportRequest) -> GetExamReportResponse:
    resp = GetExamReportResponse()
    exam_id = request.examId
    if exam_id == "" or exam_id is None:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        report, score = service.get_exam_report(exam_id)
        resp.report = report
        resp.score = score
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp
