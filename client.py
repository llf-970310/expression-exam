import thriftpy2
from thriftpy2.rpc import make_client

user_thrift = thriftpy2.load("https://raw.githubusercontent.com/llf-970310/expression-api/master/thrift_idl/user.thrift", module_name="user_thrift")
user_client = make_client(user_thrift.UserService, '81.68.117.198', 9092)
