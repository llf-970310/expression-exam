import datetime
import logging
import random
import time

import util
from client import user_client, user_thrift
from config import ReportConfig, ExamConfig
from errors import InternalError
from exam.ttypes import ExamScore, ExamType
from model.exam import CurrentTestModel, HistoryTestModel, CurrentQuestionEmbed

# 先从 current 中找，current 不存在到 history 中找
from model.paper_template import PaperTemplate
from model.question import QuestionModel


def get_exam_by_id(test_id):
    test = CurrentTestModel.objects(id=test_id).first()
    if test is None:
        test = HistoryTestModel.objects(current_id=test_id).first()
    return test


# 筛选出 score 和 feature 中的有用数据
def get_score_and_feature(question_list):
    score = {}  # {1:{'quality': 80}, 2:{'key':100,'detail':xx}, ...}
    feature = {}
    handling = False  # 是否还在处理中

    # 遍历 test 对应的 questions，将需要的 score 和 feature 抽取出来，用于后续分析
    for i in range(len(question_list), 0, -1):
        if question_list[str(i)]['status'] == 'finished':
            score[i] = question_list[str(i)]['score']
            feature[i] = feature_filter(question_list[str(i)]['feature'], question_list[str(i)]['q_type'])
        else:
            score[i] = {"quality": 0, "key": 0, "detail": 0, "structure": 0, "logic": 0}
            feature[i] = {}
            if question_list[str(i)]['status'] == 'handling':
                handling = True

    return handling, score, feature


# 提取生成报告时会用到的 feature
# 2、5、6、7 等转述题不需要提取 feature，根据分数生成报告
def feature_filter(feature_dict, q_type):
    ret = {}
    if q_type == 1:
        ret['clr_ratio'] = feature_dict['clr_ratio']
        ret['ftl_ratio'] = feature_dict['ftl_ratio']
        ret['interval_num'] = feature_dict['interval_num']
        ret['speed'] = feature_dict['speed']
    elif q_type == 3:
        ret['structure_hit'], ret['structure_not_hit'] = [], []
        ret['logic_hit'], ret['logic_not_hit'] = [], []
        for item in ReportConfig.structure_list:
            if feature_dict[item + '_num'] > 0:
                ret['structure_hit'].append(item)
            else:
                ret['structure_not_hit'].append(item)
        for item in ReportConfig.logic_list:
            if feature_dict[item + '_num'] > 0:
                ret['logic_hit'].append(item)
            else:
                ret['logic_not_hit'].append(item)

    return ret


# 判断是否有题目还在处理中
def question_all_finished(question_dict) -> bool:
    for value in question_dict.values():
        if value['status'] != 'finished' and value['status'] != 'error':
            return False
    return True


# 根据每道题目的成绩信息计算总成绩
def compute_exam_score(question_score_dict: dict, question_type_list: list) -> dict:
    """
    :param question_score_dict: 各题成绩信息 {1: score, 2: score, 3: score....}
    :param question_type_list: 试题类型列表 [q_type, q_type, ...]
    :return: 考试各维度成绩和总成绩
    """
    logging.info("[compute_exam_score] question_score_dict: %r" % question_score_dict)

    q_dimensions = {
        1: ['quality'],
        2: ['key', 'detail'],
        3: ['structure', 'logic'],
        4: [],
        5: ['key', 'detail'],
        6: ['key', 'detail']
    }
    tmp_total = {'quality': 0, 'key': 0, 'detail': 0, 'structure': 0, 'logic': 0}
    cnt_total = {'quality': 0, 'key': 0, 'detail': 0, 'structure': 0, 'logic': 0}  # 求平均分时的除数
    avg_total = {}  # 平均分
    for i, q_type in enumerate(question_type_list):
        dimensions = q_dimensions.get(q_type)
        q_score = question_score_dict[i + 1]
        for dim in dimensions:
            tmp_total[dim] += q_score.get(dim, 0)
            cnt_total[dim] += 1
    for dim in tmp_total:
        if cnt_total[dim]:
            avg_total[dim] = tmp_total[dim] / cnt_total[dim]
        else:
            avg_total[dim] = 0

    total = round(avg_total["quality"] * 0.3 + avg_total["key"] * 0.35 + avg_total["detail"] * 0.15 +
                  avg_total["structure"] * 0.1 + avg_total["logic"] * 0.1, 6)
    result = {"音质": avg_total['quality'], "结构": avg_total['structure'], "逻辑": avg_total['logic'],
              "细节": avg_total['detail'], "主旨": avg_total['key'], "total": total}
    logging.info("[compute_exam_score] score_result: %r" % result)

    return result


# 生成文件上传路径
def generate_upload_path(exam_type: ExamType, user_id: str) -> str:
    # upload file path: 相对目录(audio)/日期/用户id/时间戳+后缀(.wav)
    file_dir = ""
    if exam_type == ExamType.AudioTest:
        file_dir = '/'.join((ExamConfig.audio_test_basedir, util.get_server_date_str('-'), user_id))
    elif exam_type == ExamType.RealExam:
        file_dir = '/'.join((ExamConfig.audio_save_basedir, util.get_server_date_str('-'), user_id))

    _temp_str = "%sr%s" % (int(time.time()), random.randint(100, 1000))
    file_name = "%s%s" % (_temp_str, ExamConfig.audio_extension)

    return file_dir + '/' + file_name


# 初始化试卷
def init_paper(user_id: str, template_id: str) -> str:
    paper_tpl = PaperTemplate.objects(id=template_id).first()  # TODO: cache in redis
    if not paper_tpl:
        logging.error('[init_paper] paper template not found, tpl_id: %s' % template_id)
        return ""

    current_test = CurrentTestModel()
    current_test.paper_tpl_id = template_id
    current_test.user_id = user_id
    _start_time = datetime.datetime.utcnow()
    current_test.test_start_time = _start_time
    current_test.test_expire_time = _start_time + datetime.timedelta(seconds=paper_tpl.duration)

    # 一次性取出全部试题（按使用次数倒序）
    # 选题条件：题号<=10000(大于10000的题目用作其他用途)
    d = {'index': {'$lte': 10000}}
    questions = QuestionModel.objects(__raw__=d).order_by('used_times')

    # 生成 question_type_list 和 questions
    question_type_list = []
    temp_all_q_lst = []
    q_chosen = set()  # 存放选中题目的id字符串
    use_backup = {}  # 避免每次选题都遍历数据库
    for q_needed in paper_tpl.questions:
        q_type = q_needed['q_type']
        q_id = q_needed['dbid']
        question_type_list.append(q_type)  # 记入 question_type_list

        # 选题
        if isinstance(q_id, str) and len(q_id) in [24, 12]:  # 指定id
            q = QuestionModel.objects(id=q_id).first()
            temp_all_q_lst.append(q)
            q_chosen.add(q_id)
        else:  # 未指定id，按约定方案选题
            resp = user_client.getUserInfo(user_thrift.GetUserInfoRequest(
                userId=user_id
            ))
            if resp is None or resp.statusCode != 0:
                logging.error("[init_paper] user_client.getUserInfo failed")
                raise InternalError

            q_history = set(resp.userInfo.questionHistory)
            q_backup_1 = None  # 记录已做过但未选中的指定类型题目,优先备选
            q_backup_2 = None  # 记录已选中的指定类型题目,最差的备选
            count_before = len(q_chosen)

            tactic = use_backup.get(q_type)
            if q_id == 0:  # 按最少使用次数选取指定类型的题目
                # questions = get_cached_questions(q_type)  # TODO: 完善缓存处理机制
                for q in questions:
                    if q.q_type != q_type:
                        continue
                    flag_add = False
                    qid_str = str(q.id)
                    if qid_str in q_chosen:
                        if tactic == 2:
                            flag_add = True
                        q_backup_2 = q if q_backup_2 is None else None
                    else:
                        if qid_str not in q_history:
                            flag_add = True
                        else:
                            if tactic == 1:
                                flag_add = True
                            q_backup_1 = q if q_backup_1 is None else None
                    if flag_add:
                        temp_all_q_lst.append(q)
                        q_chosen.add(qid_str)
                        break
            # elif q_id == 1:  # 随机选取指定类型的题目
            #     pipeline = [{"$match": d}, {"$sample": {"size": 1}}]
            #     for _ in range(DefaultValue.max_random_try):
            #         rand_q = QuestionModel.objects.aggregate(*pipeline)
            #         qid_str = str(rand_q.id)
            #         if qid_str in q_chosen:
            #             q_backup_2 = rand_q if q_backup_2 is None else None
            #         else:
            #             if qid_str not in q_history:
            #                 temp_all_q_lst.append(rand_q)
            #                 q_chosen.add(qid_str)
            #                 break
            #             else:
            #                 q_backup_1 = rand_q if q_backup_1 is None else None

            # 如果题目数量不够，用重复的题目补够
            if len(q_chosen) == count_before:
                if q_backup_1:
                    use_backup.update({q_type: 1})
                    temp_all_q_lst.append(q_backup_1)
                    q_chosen.add(str(q_backup_1.id))
                else:  # 所有该类型题目不够组卷,使用相同题目组卷
                    if q_backup_2:
                        use_backup.update({q_type: 2})
                        temp_all_q_lst.append(q_backup_2)
                        q_chosen.add(str(q_backup_2.id))
                    else:  # 根本没有指定类型的题目
                        return ""

    questions_chosen = {}
    for i in range(len(temp_all_q_lst)):  # TODO: 加缓存，异步刷入数据库?
        q = temp_all_q_lst[i]
        q_current = CurrentQuestionEmbed(q_id=str(q.id), q_type=q.q_type, q_text=q.text, wav_upload_url='')
        questions_chosen.update({str(i + 1): q_current})
        q.update(inc__used_times=1)  # 更新使用次数
    current_test.questions = questions_chosen
    current_test.paper_type = question_type_list
    current_test.save()
    return str(current_test.id)
