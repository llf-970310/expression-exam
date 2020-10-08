from config import ReportConfig
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
