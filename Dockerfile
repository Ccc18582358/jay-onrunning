# syntax = docker/dockerfile:1.1-experimental
FROM python:3.6
RUN mkdir -p /app/onrunning /app/jay
RUN mkdir -p -m 0600 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts
RUN --mount=type=ssh git clone git@github.com:jinanlongen/jay.git /app/jay
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip3 install certifi 
RUN pip3 install Twisted==18.4.0 
RUN pip3 install scrapy==2.4.1 
RUN pip3 install kafka-python==1.4.3 
RUN pip3 install requests==2.19.1 
RUN pip3 install redis==3.3.8 
RUN pip3 install bs4 
RUN pip3 install bottle==0.12.13 
RUN pip3 install influxdb==5.2.0 
RUN pip3 install psutil==5.6.2 
RUN pip3 install toolkity==1.7.4 
RUN pip3 install twine==3.1.1 
RUN pip3 install scrapy_redis
RUN pip3 install psycopg2

WORKDIR /app
COPY onrunning /app/newegg
COPY onrunning/scrapy.cfg /app
COPY onrunning/run.sh /app
RUN cd /app/jay && python3 setup.py install

RUN rm -f /etc/localtime \
&& ln -sv /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
&& echo "Asia/Shanghai" > /etc/timezone

CMD bash run.sh ${spider} ${crawlid} ${callback} ${type} ${priority} ${full} ${extended} ${force} ${meta} ${urls} ${delay} ${repeated}

