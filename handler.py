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


def compute_exam_score(request: ComputeExamScoreRequest) -> ComputeExamScoreResponse:
    resp = ComputeExamScoreResponse()
    exam_id = request.examId
    if not exam_id:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        score = service.compute_exam_score(exam_id)
        resp.score = score
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


def get_exam_record(request: GetExamRecordRequest) -> GetExamRecordResponse:
    resp = GetExamRecordResponse()
    user_id = request.userId
    template_id = request.templateId

    if not user_id:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        record_list = service.get_exam_record(user_id, template_id)
        resp.examList = record_list
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp
