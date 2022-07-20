import os
from jay.downloadermiddlewares import *
from jay.pipelines import *

"""
---------------------------------------------基础设置---------------------------------------------
"""
# 基础配置 bot_name换成爬虫名字
BOT_NAME = 'jay'
SPIDER_MODULES = [f'{BOT_NAME}.spiders']
NEWSPIDER_MODULE = f'{BOT_NAME}.spiders'
STATS_CLASS = 'jay.statscollectors.RocStatsCollector'
ITEM_PIPELINES = {
    AdaptPipeline: 50,
    AssertPipeline: 60,
    KafkaPipeline: 70
}
DOWNLOADER_MIDDLEWARES = {
    # CustomRetryMiddleware: 555,
    # CustomProxyMiddleware: 666,
    # ScyllaProxyMiddleware: 667,
    # CustomRedirectMiddleware: 600,
    # RemoteChromeMiddleware: 800,
    # ZenscrapeMiddleware: 600,
    # ZyteSmartProxyMiddleware: 666
}
# used by scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware
DEFAULT_REQUEST_HEADERS = {
    b'Accept': b'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    b'Accept-Language': b'en',
    b'Accept-Encoding': b'gzip, deflate'
}
# 图片数量
IMAGE_QUANTITY_MIN = int(os.getenv('IMAGE_QUANTITY_MIN', 1))
IMAGE_QUANTITY_MAX = int(os.getenv('IMAGE_QUANTITY_MAX', 10))
"""
---------------------------------------------统计设置---------------------------------------------
"""
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
LOG_ENABLED = eval(os.environ.get('LOG_ENABLED', "True"))
# 数据统计间隔 fetch使用websocket,大于等于60s就会超时
LOGSTATS_INTERVAL = 30
# 深度信息统计
DEPTH_STATS_VERBOSE = False
"""
---------------------------------------------性能设置---------------------------------------------
"""
# http错误也会返回
HTTPERROR_ALLOW_ALL = eval(os.environ.get('HTTPERROR_ALLOW_ALL', "True"))
# Avoid in-memory DNS cache. See Advanced topics of docs for info
DNSCACHE_ENABLED = True
# 深度优先级,正数广度优先,负数深度优先,设置了这个就不要设置priority了
# request.priority = request.priority - ( depth * DEPTH_PRIORITY )
DEPTH_PRIORITY = 0
# 请求延迟
DOWNLOAD_DELAY = float(os.environ.get('DOWNLOAD_DELAY', 1))
# 下载超时时间
DOWNLOAD_TIMEOUT = int(os.environ.get('DOWNLOAD_TIMEOUT', 60))
# 并发设置
CONCURRENT_REQUESTS = int(os.environ.get('CONCURRENT_REQUESTS', 1))
CONCURRENT_REQUESTS_PER_DOMAIN = int(os.environ.get('CONCURRENT_REQUESTS_PER_DOMAIN', 1))
CONCURRENT_REQUESTS_PER_IP = int(os.environ.get('CONCURRENT_REQUESTS_PER_IP', 1))
# 最大请求速度n/min
SPEED = int(os.environ.get('SPEED', 1000))
# 重试码
RETRY_HTTP_CODES = [500, 502, 503, 504, 400, 408, 403, 304, 429]
# 重试次数
RETRY_TIMES = int(os.environ.get('RETRY_TIMES', 20))
# 重定向次数
REDIRECT_MAX_TIMES = int(os.environ.get('REDIRECT_MAX_TIMES', 20))
# 每次重定向优先级调整
REDIRECT_PRIORITY_ADJUST = int(os.environ.get('REDIRECT_PRIORITY_ADJUST', -1))
# 执行完是否结束
IDLE = eval(os.environ.get("IDLE", "False"))
# Redis host and port
"""
---------------------------------------------第三方设置---------------------------------------------
"""
# redis配置
REDIS_HOST = os.environ.get("REDIS_HOST", '127.0.0.1')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_URL = os.environ.get("REDIS_URL", 'redis://127.0.0.1:6379/6')
REDIS_START_URLS_BATCH_SIZE = 1
REDIS_START_URLS_AS_SET = True
# kafka配置
KAFKA_HOSTS = os.environ.get('KAFKA_HOSTS', '127.0.0.1:9092')
KAFKA_TOPIC_FETCH = os.environ.get("KAFKA_TOPIC_FETCH", "bufallo.fetch-discover")
KAFKA_TOPIC_DISCOVER = os.environ.get("KAFKA_TOPIC_DISCOVER", "bufallo.discover")
KAFKA_TOPIC_UPDATE = os.environ.get("KAFKA_TOPIC_UPDATE", "bufallo.update")
KAFKA_TOPIC_ENRICH = os.environ.get("KAFKA_TOPIC_ENRICH", "bufallo.enrich")
# rocketmq配置
ROCKETMQ_ADDRESS = os.environ.get("ROCKETMQ_ADDRESS", '127.0.0.1:9876')
ROCKETMQ_TOPIC = os.environ.get("ROCKETMQ_TOPIC", 'buffalo-stats')
# 远程浏览器代理
REMOTE_CHROME_INTERFACE_PROXY = os.environ.get('REMOTE_CHROME_INTERFACE_PROXY', "http://127.0.0.1:3000/chrome")
REMOTE_CHROME_READ_TIMEOUT = os.environ.get('REMOTE_CHROME_READ_TIMEOUT', '300')

"""
---------------------------------------------代理设置---------------------------------------------
"""
# 代理密钥
ZENSCRAPE_API_KEY = os.environ.get('ZENSCRAPE_API_KEY', None)
PROXY_URLS = os.environ.get('PROXY_URLS', None)


