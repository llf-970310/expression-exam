class ErrorWithCode(Exception):
    def __init__(self, code=-1, msg=""):
        self.status_code = code
        self.status_msg = msg

    def get_status_code(self):
        return self.status_code

    def get_status_msg(self):
        return self.status_msg


class InvalidParam(ErrorWithCode):
    def __init__(self):
        ErrorWithCode.__init__(self, 4000, "请求参数错误")


class ExamNotExist(ErrorWithCode):
    def __init__(self):
        ErrorWithCode.__init__(self, 4001, "测试不存在")


class InProcessing(ErrorWithCode):
    def __init__(self):
        ErrorWithCode.__init__(self, 5104, "正在处理")


def fill_status_of_resp(resp, error: ErrorWithCode = None):
    if error:
        resp.statusCode = error.get_status_code()
        resp.statusMsg = error.get_status_msg()
    else:
        resp.statusCode = 0
        resp.statusMsg = ""
