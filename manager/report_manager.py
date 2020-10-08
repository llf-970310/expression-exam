from config import ReportConfig
from exam.ttypes import *


def generate_report(features: dict, scores: dict, paper_type: list) -> ExamReport:
    # print(features)
    # print(scores)

    report = ExamReport()
    processed_data = data_processing(features, paper_type, scores)

    quality = generate_quality_report(processed_data)
    report.ftlRatio = quality["无效表达率"]
    report.clearRatio = quality["清晰度"]
    report.speed = quality["语速"]
    report.interval = quality["间隔"]

    key_and_detail = generate_key_and_detail_report(processed_data)
    report.key = key_and_detail["key"]
    report.detail = key_and_detail["detail"]

    report.structure = generate_structure_report(processed_data)
    report.logic = generate_logic_report(processed_data)

    return report


def data_processing(features, paper_type, scores):
    sum_total = {'clr_ratio': 0, 'ftl_ratio': 0, 'interval_num': 0, 'speed': 0,
                 'key': 0, 'detail': 0}
    cnt_total = {'clr_ratio': 0, 'ftl_ratio': 0, 'interval_num': 0, 'speed': 0,
                 'key': 0, 'detail': 0}
    avg_total = {'structure_hit': set(), 'logic_hit': set(), 'structure_not_hit': set(), 'logic_not_hit': set()}

    # enumerate 下标从 0 开始，features 和 scores 下标从 1 开始
    # 如果有多种同类型题目，累加求和
    for i, q_type in enumerate(paper_type):
        q_score = scores[i + 1]
        q_feature = features[i + 1]

        if q_type in [3] and len(q_feature) == 0:
            continue

        if q_type in [2, 5, 6, 7]:
            for dim in ['key', 'detail']:
                sum_total[dim] += q_score.get(dim, 0)
                cnt_total[dim] += 1
        elif q_type in [1]:
            for dim in ['clr_ratio', 'ftl_ratio', 'interval_num', 'speed']:
                sum_total[dim] += q_feature.get(dim, 0)
                cnt_total[dim] += 1
        elif q_type in [3]:
            for dim in ['structure_hit', 'logic_hit', 'structure_not_hit', 'logic_not_hit']:
                avg_total[dim].update(q_feature.get(dim))
        else:
            pass

    # 平均
    for element in sum_total:
        if cnt_total[element]:
            avg_total[element] = sum_total[element] / cnt_total[element]
        else:
            avg_total[element] = 0

    return avg_total


def generate_quality_report(processed_data) -> dict:
    report = {}

    # 清晰度
    clr = processed_data['clr_ratio']
    if clr > 0.95:
        clr_text = "你的表达十分精准，朗读流畅，语音标准，吐字清晰。"
    elif 0.8 < clr <= 0.95:
        clr_text = "你的口语表达能力良好，不过有个别词卡顿、咬字不清的情况。"
    elif 0.75 < clr <= 0.8:
        clr_text = "你能够完整朗读全文，但准确性不够，有一定的错读，增读，漏读，吞音的情况。"
    elif 0.7 < clr <= 0.75:
        clr_text = "你的朗读全文的正确性偏低，表达不够流畅。建议在朗读过程中集中精力，放慢速度，以词组为单位进行朗读。" \
                   "也需要平时多读，增强文字转化成语言的能力。"
    elif 0.5 < clr <= 0.7:
        clr_text = "你的朗读碎片化严重，语言表述不准确，用词不恰当。朗读的目的是理顺段落大意，不要被一些小词所羁绊，" \
                   "打断了完整句意，也打断了思路。可以尝试先通读一遍全文，再进行测试。"
    else:
        clr_text = "你在朗读的过程中有停顿，容易卡壳，表达方式很不规范。这个问题的原因在于你的内部思维和外部表达直接的通道没有打开。" \
                   "朗读的时候大脑中只有模糊的意义团，是一些不成型的词汇的叠加和堆砌。建议平时练习多增加阅读，以及流畅的复述。"
    report["清晰度"] = clr_text

    # 无效表达率
    ftl = processed_data['ftl_ratio']
    if ftl >= 0.7:
        ftl_text = "请按照规定文本测试。"
    else:
        ftl_text = ""
    report["无效表达率"] = ftl_text

    # 语速
    speed = processed_data['speed'] - 4.3
    if -0.1 < speed <= 0.1:
        speed_text = "你的语速接近播音员的标准，240字/分钟。快慢得体，富有节奏感。良好的朗读节奏能增强语言的表现力。"
    elif 0.1 < speed <= 0.3:
        speed_text = "你的语速快于标准的语速，较快的语速会导致听众的观感不佳，与人交流会带来急迫感，气息不稳定，不容易产生权威感。" \
                     "建议可以刻意的放慢一些语速，已到达放缓节奏的作用。"
    elif 0.3 < speed <= 0.6:
        speed_text = "你的语速快于播音员的标准（240字/分钟），在250-270/字分钟，过快的语速会影响听众的理解，阻碍你观点的有效传达。"
    elif speed > 0.6:
        speed_text = "你的语速特别快，超过300字/分钟，远远快于播音员的标准（240字/分钟）。容易产生信息量过载的情况，" \
                     "会导致听众抓不住重点，在平时讲话过程中，应该刻意的训练放慢自己的语速。"
    elif -0.3 < speed <= -0.1:
        speed_text = "你的语速慢于标准的播音员语速。较慢的语速，会导致信息量不足，影响他人的情绪，让人听的很吃力，甚至产生不耐烦的负面情绪。"
    elif -0.6 < speed <= -0.3:
        speed_text = "你的语速较慢，低于播音员平均240字/分钟的标准。较慢的语速会导致信息量偏少，难以形成适当的语境气场。" \
                     "建议在平时的训练中可以适当的加快语速，并赋予情感节奏变化。"
    elif speed <= -0.6:
        speed_text = "你的语速特别慢，远远低于播音员平均240字/分钟的标准。特别慢的语速会使得信息量严重不足，难以形成流畅的理解环境。" \
                     "建议在平时的训练中可以适当的加快语速，并赋予情感节奏变化。"
    else:
        speed_text = ""
    report["语速"] = speed_text

    # 间隔
    interval = processed_data['interval_num']
    if interval == 0:
        interval_text = "你的语句连贯，连贯的表达会让你说的更有说服力。"
    elif interval == 1:
        interval_text = "你的语言习惯中，有一些停顿。要注意朗读和交流的连贯性。"
    else:
        interval_text = "你的表达中有较多的停顿，会打断交流的连贯性。也有可能是比较紧张和着急。可以稍慢些语速，注意内容的连贯性。"
    report["间隔"] = interval_text

    return report


def generate_key_and_detail_report(processed_data) -> dict:
    report = {}

    key = processed_data['key']
    if 90 < key <= 100:
        key_text = "你的表达中擅长提炼主旨，概括内容清晰、准确。在日常交流中，注意主旨和细节交融，可以丰富表达的情境感感。" \
                   "表达力的主旨体现在输入和输出两个方向。输入方面，带着主旨意识来看文章和内容，可以更快的领会到要点，" \
                   "对于快速阅读、整理信息、关注重点有重要帮助。输出方面，在段前和段尾加入经过概括的主旨，" \
                   "相当于为接受信息的对方安排好了接收的优先级，可以更有条理和结构感的接收内容。需要注意的是，" \
                   "过于强烈的主旨感容易产生命令感，在组织复述和日常交流中，可以加入更多细节来丰富场景感，加入可知可感的因素。"
    elif 83 < key <= 90:
        key_text = "有明确的主旨意识，会在段前和段尾提纲挈领的概括内容，清晰明确。清晰的指向给表达带来了明确的方向。" \
                   "表达力的主旨体现在输入和输出两个方向。输入方面，带着主旨意识来看文章和内容，可以更快的抓住到要点，对于快速阅读、" \
                   "整理信息、关注重点有重要帮助。输出方面，在段前和段尾加入经过概括的主旨，相当于为接受信息的对方安排好了接收的优先级，" \
                   "可以更有条理和结构感的接收内容。需要注意的是，过于强烈的主旨感容易产生命令感，在组织复述和日常交流中，可以加入更多细节来丰富场景感，加入可知可感的因素。"
    elif 80 < key <= 83:
        key_text = "你在表达时，有主旨意识，能较全面和鲜明的把握内容和观点。要注意主旨的准确和完整。表达力的主旨能力体现在输入和输出两个方向。" \
                   "输入方面，带着主旨意识来看文章和内容，可以更快的领会到要点，对于快速阅读、整理信息、关注重点有重要帮助。" \
                   "输出方面，提升主旨意识，有助于结构化内容，明确交流和表达的目的，也有助于对方更好的接收你的信息，觉得你的条理清晰。"
    elif 75 < key <= 80:
        key_text = "你在表达时，有主旨意识，概括能力较强。主旨放在开头或结尾，更能有效表达。要注意主旨各元素间的逻辑，需要有条理的构建。" \
                   "表达力的主旨能力体现在输入和输出两个方向。输入方面，带着主旨意识来看文章和内容，可以更快的领会到要点，" \
                   "对于快速阅读、整理信息、关注重点有重要帮助。输出方面，提升主旨意识，有助于结构化内容，明确交流和表达的目的，也有助于对方更好的接收你的信息，觉得你的条理清晰。"
    elif 70 < key <= 75:
        key_text = "你在表达时，有主旨意识，有概括能力。能够清楚把握段落的意思，大致概括出要点。但是要注意概括的全面性，" \
                   "漏掉关键内容会影响主旨的传达。表达力的主旨能力体现在输入和输出两个方向。输入方面，带着主旨意识来看文章和内容，" \
                   "可以更快的领会到要点，对于快速阅读、整理信息、关注重点有重要帮助。输出方面，提升主旨意识，有助于结构化内容，明确交流和表达的目的，也有助于对方更好的接收你的信息，觉得你的条理清晰。"
    elif 60 < key <= 70:
        key_text = "你在表达时，有主旨意识和一定的概括能力，能大致概括出要点。但要注意主旨的指向是否明确，建议把主旨内容放在开头或者结尾。" \
                   "表达力的主旨能力体现在输入和输出两个方向。输入方面，带着主旨意识来看文章和内容，可以更快的领会到要点，对于快速阅读、" \
                   "整理信息、关注重点有重要帮助。输出方面，提升主旨意识，有助于结构化内容，明确交流和表达的目的，也有助于对方更好的接收你的信息，觉得你的条理清晰。"
    elif 40 < key <= 60:
        key_text = "你在表达时缺少主旨意识。阅读内容时应有意识的提取要点，提升概括能力。在输出时，要主旨意识先行，再去组织内容。" \
                   "一段文字的主旨是最重要的指向信息，有助于清晰的表达意思，也有助于对方的接收。只要建立主旨意识，在段前或段尾加上主旨句，就是提升表达力的重要指标。"
    else:
        key_text = "你在表达时缺少主旨意识。在复述时，没有提纲挈领地概括内容，会让人不明白表达所传递的要点。在阅读和交流中，" \
                   "提升获取要点和总结概括的能力，有助于高效的传递信息。一段文字的主旨是最重要的指向信息，有助于清晰的表达意思，" \
                   "也有助于对方的接收。只要建立主旨意识，在段前或段尾加上概括性句子，能够有效提升你的表达效率。"
    report["key"] = key_text

    detail = processed_data['detail']
    if detail > 85:
        detail_text = "你在表达中准确的给出了完整的细节，巧妙的运用了各种修辞，很好的调动了听众的感官，有精准的针对性。这些细节支撑和表达了你的观点，增强了你对内容表达的清晰度，是表达中的绝对亮点。"
    elif 70 < detail <= 85:
        detail_text = "你在表达中有意识的给出了相对完整的细节，很好的运用了各种修辞，能够调动起听众的感官，有针对性的表达了细节，这也帮助你表达了自己的观点。注意过多的细节描述，会影响主旨的清晰传达。"
    elif 60 < detail <= 70:
        detail_text = "你在表达中，有意识通过具象化的细节，来传达支撑你的观点。适当的调取细节信息，可以调动起听众的兴趣，让你的讲述更生动。" \
                      "在细节的表达中，可给出更完整和严谨的细节内容，去调动听众的各项感官，为表达增加更多的支撑和亮点，帮助听众更有效的接纳你的信息重点，" \
                      "但也要注意过多的细节表述，会影响主旨的清晰传达，要保证针对性和均衡性。"
    elif 50 < detail <= 60:
        detail_text = "你在表达中，有细节表达意识，能运用修辞，可以调动起听众的一些兴趣，对观点的表达有了支撑。" \
                      "可以试着给出更多精准和典型的细节，运用更多的修辞去调动听众的感官，传达你的重要信息。"
    elif 30 < detail <= 50:
        detail_text = "你在表达中，会有意识要给出细节，但还不够。运用了一部分修辞，适当使用具象化的细节信息，能够调动起听众的兴趣，有效支撑观点。" \
                      "在细节的表达中给出适当的例子和类比，能够更好的支撑或强调你要表达者的观点，增强说服力，并且能更好的调动听众的兴趣，使你的观点能够有更多的有效信息让听众接收到。"
    else:
        detail_text = "你在表达中对细节的表达意识比较薄弱，能够给出细节但不够完整和严谨，在细节的表达中适当添加过渡衔接词句和要点扩展信息，" \
                      "对观点的表达有着增强说服力的作用，也能够给听众创造良好的感受，并能帮助听众更好、更清晰的接收到你的观点。"
    report["detail"] = detail_text

    return report


def generate_structure_report(processed_data) -> list:
    structure_text = []

    structure_hit = processed_data['structure_hit']
    structure_not_hit = processed_data['structure_not_hit']

    if len(structure_hit) == 2:
        structure_text.append("在交流及表达观点中，你能够利用多种逻辑结构，条理清晰的表达。")
    elif len(structure_hit) == 3:
        structure_text.append("在工作与学习中，你能较顺利的进行有一定专门性的交流与沟通，语言简明，重点突出，条理清晰。"
                              "同时，你还能分析复杂话题的思路线索和层次关系，能归纳说话的核心内容，抓住关键词句。")

    for hit in structure_hit:
        structure_text.append(ReportConfig.hit_dict[hit])
    for not_hit in structure_not_hit:
        structure_text.append(ReportConfig.not_hit_dict[not_hit])

    return structure_text


def generate_logic_report(processed_data) -> list:
    logic_text = []

    logic_hit = processed_data['logic_hit']
    logic_not_hit = processed_data['logic_not_hit']

    if len(logic_hit) == 1:
        logic_text.append("在进行表达和论述时，你的语言较明了， 描述较连贯流畅，条理尚清楚。")
    elif len(logic_hit) == 2:
        logic_text.append("在进行表达和论述时，你能就日常生活和工作，学习中的特定问题，与人进行交流沟通，话题击中，意思明了。")
    elif len(logic_hit) == 3:
        logic_text.append("在进行表达和论述时，你能有效的参与多方交流，文明、得体的展开陈述，能将信息与论点有逻辑的排序，进行沟通和协调。"
                          "能运用丰富的词语，灵活的表达方式以及严谨的逻辑，叙述复杂的事件，阐明立场，提出适当的处理办法。"
                          "能有效的参与多方交流，文明、得体的展开陈述，进行沟通和协调。能将信息与论点有逻辑的排序。")

    logic_text.append("当我们在表达观点或进行论述时，通常会使用两种逻辑推理方式，一种是演绎推理，一种是归纳推理。演绎是一种线性的推理方式，"
                      "每一个观点，均由上一个观点推倒得出。归纳推理，是将一组具有共同点的事实，思想活观点归类分组，并概括其共同性。")
    logic_text.append("在论述观点时，合理的利用逻辑推理，能让你更清晰准确的展现的你的观点，同时，也让对方充分理解你的观点。"
                      "为了更好的展现逻辑，在表达时，可以适当使用因果，转折，并列，递进等连词，来帮助你更精准的组织语言，以更有逻辑，"
                      "更易懂的方式排布内容。比如说，在演绎逻辑里，所有的论点，都导向最终的结论。这个时候，恰当的使用了因果逻辑，"
                      "用“因此”来导出最终观点，就能更突出在此逻辑关系中的结论。")

    return logic_text
