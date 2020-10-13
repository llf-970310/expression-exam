import logging

from config import ReportConfig
from exam.ttypes import ExamScore
from model.exam import CurrentTestModel, HistoryTestModel


# 先从 current 中找，current 不存在到 history 中找
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
