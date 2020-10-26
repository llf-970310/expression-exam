FROM ubuntu:18.04
MAINTAINER lilf <lf97310@gmail.com>

ENV TZ=Asia/Shanghai

RUN sed -i s@/archive.ubuntu.com/@/mirrors.tuna.tsinghua.edu.cn/@g /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update -y && \
    apt-get install -y python3.6 python3-pip python3.6-dev

# 并更新pip
RUN python3.6 -m pip install pip --upgrade -i https://pypi.douban.com/simple && \
    python3.6 -m pip install wheel -i https://pypi.douban.com/simple

# 设置pip源
RUN pip3 config set global.index-url http://mirrors.aliyun.com/pypi/simple/ && \
    pip3 config set global.trusted-host mirrors.aliyun.com

RUN pip3 install --no-cache-dir thrift thriftpy2 && \
    pip3 install --no-cache-dir mongoengine PyJWT requests && \
    pip3 install --no-cache-dir python-Levenshtein

EXPOSE 9091

WORKDIR /expression-exam
COPY ./ /expression-exam

ENTRYPOINT ["python3.6", "server.py"]