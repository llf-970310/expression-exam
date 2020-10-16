import thriftpy2
from thriftpy2.rpc import make_client

user_thrift = thriftpy2.load("../expression-api/thrift_idl/user.thrift", module_name="user_thrift")
user_client = make_client(user_thrift.UserService, '127.0.0.1', 9092)
