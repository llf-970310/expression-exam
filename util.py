import time
from datetime import timedelta


def datetime_to_str(dt, date_separator='-', only_date=False) -> str:
    """将datetime对象转换为形如 '2020-01-01 12:00:00'的字符串,可指定only_date只包含日期

    如果指定date_separator则按指定分隔符格式化日期部分，如 '2020.01.01 12:00:00'

    dt 为 UTC 时间，在该函数中应转换为东八区时间

    Args:
        dt: datetime对象
        date_separator: 日期间隔符
        only_date: 是否只返回日期字符串

    Returns:
        datetime字符串
    """
    dt = dt + timedelta(hours=8)
    if not dt:
        return ''
    if only_date:
        return dt.strftime("%%Y%s%%m%s%%d" % (date_separator, date_separator))
    else:
        return dt.strftime("%%Y%s%%m%s%%d %%H:%%M:%%S" % (date_separator, date_separator))


def get_server_date_str(separator='') -> str:
    """
    Desc:   获得当前日期格式化字符串，可指定分隔符，如: 20181009(默认), 2018-10-31(输入为-), 2018===10===31(输入为===)
    """
    return time.strftime("%%Y%s%%m%s%%d" % (separator, separator), time.localtime(time.time()))
