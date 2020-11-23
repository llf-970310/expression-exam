import os
import sys

project_folder = os.path.abspath(__file__).split('/server.py')[0]
sys.path.append(os.path.join(project_folder, 'expression'))
sys.path.append(os.path.join(project_folder, 'gen-py'))

import logging

import mongoengine
from config import MongoConfig
from exam import ExamService
from exam.ttypes import *
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer
import handler


class ExamServiceHandler:
    def __init__(self):
        self.log = {}

    def getExamReport(self, request: GetExamReportRequest) -> GetExamReportResponse:
        return handler.get_exam_report(request)

    def computeExamScore(self, request: ComputeExamScoreRequest) -> ComputeExamScoreResponse:
        return handler.compute_exam_score(request)

    def getExamRecord(self, request: GetExamRecordRequest) -> GetExamRecordResponse:
        return handler.get_exam_record(request)

    def initNewAudioTest(self, request: InitNewAudioTestRequest) -> InitNewAudioTestResponse:
        return handler.init_new_audio_test(request)

    def getQuestionInfo(self, request: GetQuestionInfoRequest) -> GetQuestionInfoResponse:
        return handler.get_question_info(request)

    def getFileUploadPath(self, request: GetFileUploadPathRequest) -> GetFileUploadPathResponse:
        return handler.get_file_upload_path(request)

    def initNewExam(self, request: InitNewExamRequest) -> InitNewExamResponse:
        return handler.init_new_exam(request)

    def getPaperTemplate(self, request: GetPaperTemplateRequest) -> GetPaperTemplateResponse:
        return handler.get_paper_template(request)

    def getAudioTestResult(self, request: GetAudioTestResultRequest) -> GetAudioTestResultResponse:
        return handler.get_audio_test_result(request)

    def getExamResult(self, request: GetExamResultRequest) -> GetExamResultResponse:
        return handler.get_exam_result(request)


if __name__ == '__main__':
    # init mongo
    mongoengine.connect(
        db=MongoConfig.db,
        host=MongoConfig.host,
        port=MongoConfig.port,
        username=MongoConfig.user,
        password=MongoConfig.password
    )

    # init logging
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y/%m/%d %H:%M:%S"
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    # init thrift server
    exam_handler = ExamServiceHandler()
    processor = ExamService.Processor(exam_handler)
    transport = TSocket.TServerSocket(host='0.0.0.0', port=9091)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()

    # server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    # You could do one of these for a multithreaded server
    server = TServer.TThreadedServer(processor, transport, tfactory, pfactory)
    server.serve()
