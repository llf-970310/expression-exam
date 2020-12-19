import time

import jwt

from exam.ttypes import *
import service
from errors import *
from util import func_log


@func_log
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


@func_log
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


@func_log
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


@func_log
def init_new_audio_test(request: InitNewAudioTestRequest) -> InitNewAudioTestResponse:
    resp = InitNewAudioTestResponse()
    user_id = request.userId

    if not user_id:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        audio_test_info = service.init_new_audio_test(user_id)
        resp.question = audio_test_info
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def get_question_info(request: GetQuestionInfoRequest) -> GetQuestionInfoResponse:
    resp = GetQuestionInfoResponse()
    exam_id = request.examId
    question_num = request.questionNum

    if not exam_id or question_num <= 0:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        question_info = service.get_question_info(exam_id, question_num)
        resp.question = question_info
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def get_file_upload_path(request: GetFileUploadPathRequest) -> GetFileUploadPathResponse:
    resp = GetFileUploadPathResponse()
    exam_id = request.examId
    user_id = request.userId
    exam_type = request.type

    if not user_id or (exam_type == ExamType.RealExam and not exam_id):
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        if exam_type == ExamType.AudioTest:
            upload_path = service.get_file_upload_path(user_id=user_id)
        elif exam_type == ExamType.RealExam:
            upload_path = service.get_file_upload_path(exam_id, user_id, request.questionNum)
        else:
            fill_status_of_resp(resp, InvalidParam())
            return resp

        resp.path = upload_path
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def init_new_exam(request: InitNewExamRequest) -> InitNewExamResponse:
    resp = InitNewExamResponse()
    user_id = request.userId
    template_id = request.templateId

    if not user_id or not template_id:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        exam_id = service.init_new_exam(user_id, template_id)
        resp.examId = exam_id
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def get_paper_template(request: GetPaperTemplateRequest) -> GetPaperTemplateResponse:
    resp = GetPaperTemplateResponse()
    template_id = request.templateId

    try:
        template_list = service.get_paper_template(template_id)
        resp.templateList = template_list
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def get_audio_test_result(request: GetAudioTestResultRequest) -> GetAudioTestResultResponse:
    resp = GetAudioTestResultResponse()
    exam_id = request.examId

    if not exam_id:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        can_recognize, lev_ratio = service.get_audio_test_result(exam_id)
        resp.canRecognize = can_recognize
        resp.levenshteinRatio = lev_ratio
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def get_exam_result(request: GetExamResultRequest) -> GetExamResultResponse:
    resp = GetExamResultResponse()
    exam_id = request.examId

    if not exam_id:
        fill_status_of_resp(resp, InvalidParam())
        return resp

    try:
        score, report = service.get_exam_result(exam_id)
        resp.report = report
        resp.score = score
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp


@func_log
def save_paper_template(request: SavePaperTemplateRequest) -> SavePaperTemplateResponse:
    resp = SavePaperTemplateResponse()
    new_template = request.newTemplate

    try:
        service.save_paper_template(new_template)
        fill_status_of_resp(resp)
    except ErrorWithCode as e:
        fill_status_of_resp(resp, e)

    return resp
