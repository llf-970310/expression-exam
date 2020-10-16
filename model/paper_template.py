#!/usr/bin/env python3
# coding: utf-8
#
# Created by dylanchu on 2020-05-10

from mongoengine import *


"""
...
questions: [
    {q_type: int, dbid: ObjectId or 0},
    {q_type: int, dbid: ObjectId or 0}
]
"""

# dbid 可直接指定数据库中题目id（24位长度），或按规则出题：
#   0: 最少使用次数


class PaperTemplate(Document):

    meta = {'collection': 'paper_tpl'}

    deprecated = BooleanField(default=False)  # 是否废弃不用
    need_auth = BooleanField(default=False)
    password = StringField(max_length=128, default=None)
    duration = IntField(min=1, default=1800)  # 考试时长,seconds

    name = StringField(max_length=128, required=True)
    desc = StringField(max_length=512, default=None)
    questions = ListField(required=True)

    def total_question_num(self):
        return len(self.questions)


# def init_db():
#     """
#     将扰乱生产数据，请勿运行，除非你明确知道你在干什么
#     """
#     paper_tpl = PaperTemplate()
#     paper_tpl.time_limit = 1800
#     paper_tpl.name = '含英语题目的表达能力测试'
#     paper_tpl.questions = [
#         {'q_type': 1, 'dbid': 0},
#         {'q_type': 3, 'dbid': 0},
#         {'q_type': 5, 'dbid': 0},
#         {'q_type': 5, 'dbid': 0},
#         {'q_type': 6, 'dbid': 0},
#         {'q_type': 6, 'dbid': 0}
#     ]
#     paper_tpl.save()
#
#     paper_tpl = PaperTemplate()
#     paper_tpl.time_limit = 1800
#     paper_tpl.name = '原始表达能力测试'
#     paper_tpl.questions = [
#         {'q_type': 1, 'dbid': 0},
#         {'q_type': 2, 'dbid': 0},
#         {'q_type': 2, 'dbid': 0},
#         {'q_type': 2, 'dbid': 0},
#         {'q_type': 2, 'dbid': 0},
#         {'q_type': 3, 'dbid': 0}
#     ]
#     paper_tpl.save()
#
#     paper_tpl = PaperTemplate()
#     paper_tpl.time_limit = 1800
#     paper_tpl.name = '2019圣诞小程序测试'
#     paper_tpl.questions = [
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 4, 'dbid': 1},
#         {'q_type': 1, 'dbid': 1},
#         {'q_type': 3, 'dbid': 1}
#     ]
#     paper_tpl.save()
#
#
# if __name__ == '__main__':
#     from mongoengine import connect
#     from app_config import MongoConfig
#
#     connect(MongoConfig.db, host=MongoConfig.host, port=MongoConfig.port,
#             username=MongoConfig.user, password=MongoConfig.password, authentication_source=MongoConfig.db,
#             authentication_mechanism=MongoConfig.auth)
#
