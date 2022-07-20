import json
import logging
import os
import time
import uuid
from copy import deepcopy
from urllib.parse import urlparse
from scrapy import Spider, Request, signals
from scrapy.exceptions import DontCloseSpider
from scrapy.utils.response import response_status_message
from toolkit import get_ip
from jay.request import build_request
from jay.utils import request_to_str
from jay.utils import ItemCollector, ItemCollectorPath, enrich_wrapper


class JaySpider(Spider):
    name = 'JaySpider'
    is_spu_found_in_bucket = False
    flags = []

    def __init__(self, *args, **kwargs):
        Spider.__init__(self, *args, **kwargs)
        self.index = None
        self.local_ip = get_ip()
        self.logger.debug("init, args: {}, kwargs: {}".format(str(args), str(kwargs)))
        self.command = {'crawlid': kwargs.get('crawlid') or "cli_{}".format(uuid.uuid1()),
                        'type': kwargs.get('type', 'discover'), 'callback': kwargs.get('callback', "parse"),
                        'priority': int(kwargs.get('priority', 1000)), 'urls': kwargs.get('urls'),
                        'meta': json.loads(kwargs.get('meta'))}
        self.url_check()

    def init_stats(self):
        self.crawler.stats.set_value('crawlid', self.command.get('crawlid'))
        self.crawler.stats.set_value('type', self.command.get('type'))
        self.crawler.stats.set_value('urls', self.command.get('urls'))
        self.crawler.stats.set_value('name', self.name)
        self.crawler.stats.set_value('bucket_count', 0)
        self.crawler.stats.set_value('total_spu_count', 0)
        self.crawler.stats.set_value('scraped_spu_count', 0)
        self.crawler.stats.set_value('scraped_sku_count', 0)

    def _set_crawler(self, crawler):
        super(JaySpider, self)._set_crawler(crawler)
        self.crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)

    def spider_idle(self):
        if self.settings.getbool('IDLE', True):
            raise DontCloseSpider

    @property
    def logger(self):
        logger = logging.getLogger("jay-" + self.name)
        return logging.LoggerAdapter(logger, {'spider': self})

    def start_requests(self):
        # request构造器 不能写在init里，因为set_crawler初始化settings在init之后，无法获取到settings
        self.init_stats()
        log_message = {
            "parse": "正常抓取",
            "parse_scu": "fetch任务",  # 属于parse的下一级任务
            "parse_tag": "标签任务"
        }
        self.logger.info(f"任务类型：{log_message.get(self.command['callback'])}")
        self.logger.info(f"总计{len(self.start_urls)}个请求")
        # 可以通过callback参数控制爬取的是bucket还是scu
        for index, url in enumerate(self.start_urls):
            meta = dict(
                jay=dict(
                    command=self.command,
                    crawlid=self.command['crawlid'],
                    priority=self.command['priority'],
                ),
                index=index + 1,
                # mitmproxy测试用
                # proxy="http://localhost:8080"
            )
            request = build_request(url,
                                    meta=meta,
                                    callback=getattr(self, self.command['callback']),
                                    flags=self.flags,
                                    errback=self.errback
                                    )
            yield request
            self.logger.info(f"正在发起第{index + 1}个链接: {url}")

    def parse(self, response, **kwargs):
        self.logger.info("Parse bucket: {}".format(response))
        command = self.command['type']
        # 发现，返回scu,spu
        if command == 'discover':
            scu_urls = self.extract_scu_urls(response)
            # 去重
            scu_urls = list(set(scu_urls))
            # 修改优先级
            self.adjust(response)
            self.logger.info("found {} scus in bucket {}, url: {}".format(len(scu_urls),
                                                                          response.meta['jay'].get('bucket_position',
                                                                                                   1), response.url))
            self.crawler.stats.inc_value('bucket_count')
            self.crawler.stats.inc_value('total_spu_count', len(scu_urls))

            for position, scu_url in enumerate(scu_urls):
                # 拷贝一下，防止多个请求同时操作meta造成数据污染
                scu_meta_copy = deepcopy(response.meta)
                scu_meta_copy['jay']['scu_position_in_bucket'] = position
                # 构造请求
                request = build_request(scu_url, callback=self.parse_scu, meta=scu_meta_copy, flags=self.flags, )
                self.logger.debug("yield SCU request: {}".format(self.request_to_str(request)))
                yield request
            # 下一页链接
            next_bucket_url = self.extract_next_bucket_url(response)
            if len(scu_urls) == 0:
                next_bucket_url = None
            self.logger.info("next_bucket_url: {}".format(str(next_bucket_url)))
            # 递归寻找是否有下一页
            next_request = self.yield_next_bucket(response, next_bucket_url, self.parse)
            yield next_request

        # 只返回scu
        elif command == 'tbd':
            # 返回bucket,scu
            pass
        # 标签任务
        elif command == 'enrich':
            pass

    def yield_next_bucket(self, response, next_bucket_url, callback):
        self.adjust(response)
        priority = response.meta['jay']['priority']
        if isinstance(next_bucket_url, str):
            response.meta['jay']['bucket_url'] = next_bucket_url
            request = build_request(next_bucket_url, callback=callback, meta=response.meta,
                                    dont_filter=True)
            self.logger.info("yield next BUCKET request: {}".format(request_to_str(request)))
            return request
        # 有可能是post请求
        elif isinstance(next_bucket_url, dict):
            response.meta['jay']['bucket_url'] = next_bucket_url['url']
            request = build_request(
                next_bucket_url['url'], method=next_bucket_url['method'], callback=callback,
                body=next_bucket_url['body'], meta=response.meta, dont_filter=True)
            self.logger.info("yield BUCKET request: {}".format(request_to_str(request)))
            return request
        elif isinstance(next_bucket_url, Request):
            request = next_bucket_url
            self.logger.info("yield BUCKET request: {}".format(request_to_str(request)))
            return request
        elif next_bucket_url is None:
            self.logger.warning("There is no next page！")
            return None
        else:
            self.logger.error("illegal type found: " + type(next_bucket_url))
            return None

    def parse_scu(self, response):
        callback = self.command['callback']
        if callback == 'parse_scu':
            self.logger.info(f"正在处理第{response.meta['index']}个链接: {response.url}")
        item_loader = self.get_item_loader(response)
        meta = response.request.meta['jay']
        # 用于存放多级item，通过meta传递
        item_collector = ItemCollector()
        meta['item_collector'] = item_collector
        meta['path'] = ItemCollectorPath()
        item_collector.add_item_loader(meta['path'], item_loader)
        self.enrich_scu_base_data(item_loader, response)
        self.logger.debug(f"Start to enrich scu data :{response.url}")
        # 子类spider继承该方法
        requests = self.enrich_scu_data(item_loader, response)
        # 通过enrich_scu_data的返回值判断item_collector是否有值
        result = self.yield_item(requests, item_collector, response)

        return result

    def parse_tag(self, response):
        scu_urls = self.extract_scu_urls(response)
        if self.is_spu_found_in_bucket:
            scu_product_ids = self.enrich_tag(None, response, None)
            for scu_product_id in scu_product_ids:
                item = self.parse_tag_detail(response, scu_product_id)
                yield item
        else:
            for position, scu_url in enumerate(scu_urls):
                # 拷贝一下，防止多个请求同时操作meta造成数据污染
                scu_meta_copy = deepcopy(response.meta)
                scu_meta_copy['jay']['scu_position_in_bucket'] = position
                scu_meta_copy['jay']['is_spu'] = True
                # 构造请求
                request = build_request(scu_url, callback=self.parse_tag_detail, meta=scu_meta_copy)
                self.logger.info("yield SCU request: {}".format(self.request_to_str(request)))
                yield request
            # 下一页链接
        next_bucket_url = self.extract_next_bucket_url(response)
        if len(scu_urls) == 0:
            next_bucket_url = None
        self.logger.info("next_bucket_url: {}".format(str(next_bucket_url)))
        # 递归寻找是否有下一页
        next_request = self.yield_next_bucket(response, next_bucket_url, self.parse_tag)
        yield next_request

    def parse_tag_detail(self, response, product_id=None):
        item_loader = self.get_item_loader(response)
        meta = response.request.meta['jay']
        item_collector = ItemCollector()
        meta['item_collector'] = item_collector
        meta['path'] = ItemCollectorPath()
        item_collector.add_item_loader(meta['path'], item_loader)
        self.enrich_scu_base_data(item_loader, response)
        self.logger.debug(f"Start to enrich scu data :{response.url}")
        # 子类spider继承该方法
        requests = self.enrich_tag(item_loader, response, product_id)
        # 通过enrich_scu_data的返回值判断item_collector是否有值
        result = self.yield_item(requests, item_collector, response)
        return result

    def yield_item(self, requests, item_collector, response):
        if requests:
            item_collector.add_requests(requests)

        if item_collector.have_request():
            req = item_collector.pop_request()
            if isinstance(req, Request):
                for k, v in response.request.meta['jay'].items():
                    if k not in req.meta['jay']:
                        req.meta['jay'][k] = v

                req.meta['priority'] += 1
                req.callback = self.parse_next
                req.errback = self.errback
                return req
            else:
                response.request.meta['jay'].update(req['meta'])
                response.request.meta['jay']['priority'] += 1
                req['meta'] = response.request.meta
                req['callback'] = self.parse_next
                req['dont_filter'] = True
                return build_request(**req)
        else:
            item = item_collector.load_item()
            if response.meta['jay'].get('is_spu_dead', False):
                item['meta']['is_spu_dead'] = True
            return item

    def parse_next(self, response):
        meta = response.request.meta['jay']
        item_collector = meta['item_collector']
        path = meta['path']
        loader = item_collector.item_loader(path)
        prop = path.last_prop()
        # the method named 'enrich_***' defined in inherit spiders
        requests = getattr(self, 'enrich_%s' % prop)(loader, response)
        result = self.yield_item(requests, item_collector, response)
        return result

    # 全局设置
    def enrich_scu_base_data(self, item_loader, response):
        bucket_url = response.meta['jay'].get('bucket_url', response.meta['jay'].get('seed', ''))
        # 有的时候发送的是post请求
        if isinstance(bucket_url, dict) and 'url' in bucket_url:
            bucket_url = bucket_url['url']

        item_loader.add_value('spiderid', response.meta['jay'].get('spiderid'))
        item_loader.add_value('url', response.url)
        item_loader.add_value('seed', response.meta['jay'].get('seed', ''))
        item_loader.add_value('timestamp', time.time())
        item_loader.add_value('status_code', response.status)
        item_loader.add_value('status_msg', response_status_message(response.status))
        item_loader.add_value('domain', urlparse(response.url).hostname.split('.', 1)[1])
        item_loader.add_value('crawlid', response.meta['jay'].get('crawlid'))
        item_loader.add_value('response_url', response.url)
        item_loader.add_value('item_type', getattr(self, 'item_type', 'product'))
        item_loader.add_value('proxy', response.meta['jay'].get('proxy'))
        item_loader.add_value('meta', dict(command=response.meta['jay']['command']))
        item_loader.add_value('bucket_position', response.meta['jay'].get('bucket_position', 1))  # 第几页
        item_loader.add_value('scu_position_in_bucket', response.meta['jay'].get('scu_position_in_bucket'))  # 第几件
        item_loader.add_value('bucket_url', bucket_url)  # 页的链接
        item_loader.add_value('scu_url', response.url)  # 链接

    def errback(self, failure):
        if failure and failure.value and hasattr(failure.value, 'response'):
            response = failure.value.response

            if response:
                # 采集出现异常, 也应将成功抓取的部分sku存进来才是, all_skus=False
                if 'item_collector' in response.request.meta['jay']:
                    item_collector = response.request.meta['jay']['item_collector']
                    response.request.meta['jay']['tags']['all_skus'] = False
                    item_collector.pop_item_loader(
                        response.request.meta['jay']['path'])
                    return self.yield_item(None, item_collector, response)
                else:
                    crawlid = response.request.meta['jay'].get('crawlid')
                    request_count = response.meta['jay'].get(
                        'request_count_per_item', 1)
                    self.logger.debug(
                        "item crawl report. local_ip: {local_ip}, crawlid: {crawlid}, request_count: {request_count}, product_id: {product_id}, success: {success}".format(
                            local_ip=self.local_ip,
                            crawlid=crawlid,
                            request_count=request_count,
                            product_id='unknown',
                            success=False
                        ), extra={
                            'local_ip': self.local_ip,
                            'crawlid': crawlid,
                            'request_count': request_count,
                            'product_id': 'unknown',
                            'status_code': response.status,
                            'success': False
                        })
                    loader = self.get_item_loader(response)
                    self.enrich_scu_base_data(loader, response)
                    item = loader.load_item()

                # 商品解析后异常的场景
                is_spu_dead = response.meta['jay'].get('is_spu_dead', False)
                if is_spu_dead:
                    item['meta']['is_spu_dead'] = True

                if item['status_msg'].count("Unknown Status"):
                    item['status_msg'] = "errback: %s" % failure.value
                self.logger.error("errback: %s" % item)

                return item
            else:
                self.logger.error("failure has NO response")
        else:
            self.logger.error(
                "failure or failure.value is NULL, failure: %s" % failure)

    @staticmethod
    def get_item_loader(response):
        raise NotImplementedError

    @staticmethod
    def adjust(response):
        """此方法只允许在parse环节调用, 扶正为了提高next_page抓取优先级而做的meta回调"""
        response.meta['jay']['callback'] = 'parse_scu'
        response.meta['jay']['command']['priority'] = response.meta['jay']['command']['priority'] - 20

    @staticmethod
    def request_to_str(request):
        body = request.body
        if body:
            body = json.dumps(json.loads(body))
        return "{method} {url}".format(
            method=request.method, url=request.url, body=body,
            type=type(request), headers=request.headers,
            meta=request.meta
        )

    @enrich_wrapper
    def enrich_scu_data(self, item_loader, response):
        raise NotImplementedError

    def enrich_tag(self, item_loader, response, product_id):
        raise NotImplementedError

    def extract_scu_urls(self, response):
        raise NotImplementedError

    def extract_next_bucket_url(self, response):
        raise NotImplementedError

    @staticmethod
    def is_bad_redirect_location(request, response, redirect):
        return False

    def url_check(self):
        if ',' in self.command['urls']:
            if self.comma_url():
                return
            if self.command['callback'] != 'parse_scu':
                self.logger.error("参数或链接错误，退出")
                exit(-1)
            else:
                self.start_urls = self.command['urls'].replace(' ', '').split(',')
        elif self.command['callback'] != 'parse_scu' and self.command['type'] == 'fetch':
            self.logger.error("参数或链接错误，退出")
            exit(-1)
        else:
            self.start_urls = [self.command['urls']]

    def comma_url(self):
        if self.command['meta']['source_site_code'] in ['BLDA', 'SLTD', 'SLTDO', 'TMLD']:
            self.start_urls = [self.command['urls']]
            return True
        return
