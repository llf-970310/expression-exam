import datetime

from mongoengine import *


"""

参考资料：http://docs.mongoengine.org/guide/index.html , http://docs.mongoengine.org/apireference.html
中文资料：https://segmentfault.com/a/1190000008025156#articleHeader8

注意：
    1. 选取字段名称一定要慎重再慎重！！应该由良好的自解释性，不要引起歧义！！
    2. 合理拆分文件，不要一股脑把所有东西全写在一起！！（当然也不要胡乱拆分！）
    3. 最好保持类的属性名和数据库字段名一致，不用db_field指定，以便于理解使用

"""


class WavPretestModel(DynamicDocument):
    """
    用户的音频测试 wav+test
    """
    text = StringField(max_length=512)
    user_id = StringField(max_length=32)
    test_time = DateTimeField(default=lambda: datetime.datetime.utcnow())
    file_location = StringField(max_length=32, default='local')
    wav_upload_url = StringField(max_length=256)
    result = DictField(default={'status': 'none', 'feature': {}})
    meta = {'collection': 'wav_test'}


class CurrentQuestionEmbed(EmbeddedDocument):
    """
    用户做题的题目 current.question[x]
    """
    q_id = StringField(max_length=32)
    q_type = IntField(min_value=1, max_value=3)
    q_text = StringField(max_length=512)
    file_location = StringField(max_length=32)
    wav_upload_url = StringField(max_length=256)
    wav_temp_url = StringField(max_length=256)
    # status: "none|question_fetched|url_fetched|handling|finished",finished 由docker设置
    status = StringField(max_length=32, default="none")
    analysis_start_time = DateTimeField()
    feature = DictField(default={})
    score = DictField(default={})  # score field may has a set of scores
    analysis_end_time = DateTimeField()
    stack = StringField(max_length=1024)
    analysed = BooleanField()  # 这个回答是否被分析过

    # 默认没有get函数，手动添加支持
    def get(self, key, default=None):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return default


class CurrentTestModel(DynamicDocument):
    """
    current
    """
    user_id = StringField(max_length=32, default=None)
    openid = StringField(max_length=64, default=None)  # wx_christmas2019活动使用
    test_start_time = DateTimeField()
    test_expire_time = DateTimeField(default=datetime.datetime.utcnow())  # default只为兼容之前字段为空的情况
    paper_type = ListField()
    paper_tpl_id = StringField(max_length=24, default=None)
    current_q_num = IntField(min_value=1, default=1)
    score_info = DictField(default={})
    questions = DictField(default={})
    all_analysed = BooleanField()  # 这个考试中的所有回答是否都被分析过
    # make questions a dict rather than a list so as to be able update one question w/o affecting other questions

    meta = {'collection': 'current'}


class HistoryTestModel(DynamicDocument):
    """
    history
    TODO: 大部分内容和CurrentTestMode相同，是否可直接继承CurrentTestModel??
    """
    current_id = StringField(max_length=32, default=None)
    user_id = StringField(max_length=32, default=None)
    openid = StringField(default=None)
    test_start_time = DateTimeField()
    test_expire_time = DateTimeField()
    paper_type = ListField()
    paper_tpl_id = StringField(max_length=24, default=None)
    current_q_num = IntField(min_value=1, default=1)
    score_info = DictField(default={})
    questions = DictField(default={})
    all_analysed = BooleanField(default=False)  # 这个考试中的所有回答是否都被分析过

    meta = {'collection': 'history'}
