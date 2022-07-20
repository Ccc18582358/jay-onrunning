import os
import random

from scrapy_zenscrape import ZenscrapeMiddleware
from scrapy_zyte_smartproxy import ZyteSmartProxyMiddleware

from onrunning.downloadermiddlewares.request_scu import CrawlerRequest
from jay.settings import *

# 日志配置
LOG_LEVEL = "INFO"

# 需要改
BOT_NAME = 'jay'

# 需要改
SPIDER_MODULES = ['onrunning.spiders']

# 需要改
NEWSPIDER_MODULE = 'onrunning.spiders'

DOWNLOADER_MIDDLEWARES = {
    CrawlerRequest: 400,
    ZyteSmartProxyMiddleware: 200
    # ScyllaProxyMiddleware: 200
}

DOWNLOAD_DELAY = 2

USER_AGENT = {
    'user-agent': random.choice([
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60',
        'Opera/8.0 (Windows NT 5.1; U; en)',
        'Mozilla/5.0 (Windows NT 5.1; U; en; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 9.50',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0',
        'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2 ',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER',
        'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)',
        'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 SE 2.X MetaSr 1.0',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0) ',
    ])
}
from twisted.web.http_headers import Headers as TwistedHeaders

TwistedHeaders._caseMappings.update({
    b'authority': b'authority',
    b'accept': b'accept',
    b'accept-language': b'accept-language',
    b'content-type': b'content-type',
    b'origin': b'origin',
    b'on-client': b'on-client',
    b'referer': b'referer',
    b'sec-ch-ua': b'sec-ch-ua',
    b'sec-ch-ua-mobile': b'sec-ch-ua-mobile',
    b'sec-ch-ua-platform': b'sec-ch-ua-platform',
    b'sec-fetch-dest': b'sec-fetch-dest',
    b'sec-fetch-mode': b'sec-fetch-mode',
    b'sec-fetch-site': b'sec-fetch-site',
    b'user-agent': b'user-agent',
    b'x-requested-with': b'x-requested-with',
    b'x-csrf-token': b'x-csrf-token',
    b'x-newrelic-id': b'x-newrelic-id',
})
ZYTE_SMARTPROXY_APIKEY = 'f3e5226514e6421ea4b40b9ecb1d8c12'
ZYTE_SMARTPROXY_ENABLED = True