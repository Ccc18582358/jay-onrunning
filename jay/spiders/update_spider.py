import json
import time
import traceback
from urllib.parse import urlparse

import scrapy
from scrapy import Spider
from scrapy.utils.response import response_status_message
from scrapy_redis import defaults
from scrapy_redis.spiders import RedisSpider
from toolkit.managers import ExceptContext
from jay.request import build_request
from jay.utils import ItemCollector, ItemCollectorPath, enrich_wrapper


class UpdateSpider(RedisSpider):
    name = "spider"
    redis_key = "SOURCE_SITE:COMMANDS"
    redirect_sku = False
    proxy = True

    def __init__(self, *args, **kwargs):
        Spider.__init__(self, *args, **kwargs)
        # https://docs.scrapy.org/en/latest/topics/commands.html
        self.logger.info("init, args: {}, kwargs: {}".format(
            str(args), str(kwargs)))

    def start_requests(self):
        """Returns a batch of start requests from redis."""
        return self.next_requests()

    def next_requests(self):
        """Returns a request to be scheduled or none."""
        use_set = self.settings.getbool('REDIS_START_URLS_AS_SET', defaults.START_URLS_AS_SET)
        fetch_one = self.server.spop
        # if use_set else self.server.lpop
        # XXX: Do we need to use a timeout here?
        found = 0
        while found < self.redis_batch_size:
            data = fetch_one(self.redis_key)
            if data:
                self.logger.info("reading request:{}".format(data))
            length = self.server.scard(self.redis_key)
            if length > 0:
                self.logger.info("{}:remain {} requests".format(self.redis_key, length))
            if not data:
                break
            req = self.make_request_from_data(data)
            if type(req) == list:
                for request in req:
                    yield request
                found += 1
            elif req:
                yield req
                found += 1
            else:
                self.logger.debug("Request not made from data: %r", data)
        if found:
            self.logger.info("Read %s requests from '%s'", found, self.redis_key)

    # 可以在具体spider继承
    def make_request_from_data(self, data):
        data = eval(data.decode())

        url = [item['item_url'] for item in data['items'] if item['item_type'] == 'Spu'][0]
        url = self.url_escape(url)
        meta = dict(
            jay=dict(
                # command=self.command,
                data=data['items'],
                priority=1000
            ),
            priority=1000,
        )
        request = build_request(url, meta=meta, callback=self.parse, dont_filter=True, proxy=self.proxy)
        self.logger.info("yield START request: {method} {url}, headers: {headers}, meta: {meta}".format(
            method=request.method, url=request.url, headers=json.dumps(str(request.headers)), meta=str(request.meta)))
        return request

    @staticmethod
    def get_item_loader(response):
        raise NotImplementedError

    def parse(self, response):
        self.logger.debug("Parse: {}".format(response))
        if self.spu_is_dead(response):
            return self.enrich_dead_spu(response)
        else:
            return self.parse_scu(response)

    @staticmethod
    def spu_is_dead(response):
        if response.status == 404:
            return True
        return False

    def enrich_dead_spu(self, response):
        self.logger.info("Start to enrich dead spu")
        item_loader = self.get_item_loader(response)
        item_loader.add_value('is_dead', True)
        items = response.meta['jay']['data']
        for item in items:
            if item['item_type'] == 'Spu':
                items.remove(item)
        item_loader.add_value('sku_items', items)
        return item_loader.load_item()

    def parse_scu(self, response):
        result = True
        with ExceptContext(errback=self.log_err) as ec:
            item_loader = self.get_item_loader(response)
            meta = response.request.meta['jay']
            item_collector = ItemCollector()
            meta['item_collector'] = item_collector
            meta['path'] = ItemCollectorPath()
            item_collector.add_item_loader(meta['path'], item_loader)
            self.logger.info(f"Start to enrich scu data :{response.url}")
            self.enrich_scu_base_data(item_loader, response)
            requests = self.enrich_scu_data(item_loader, response)
            if requests == 0:
                return self.enrich_dead_spu(response)
            result = self.yield_item(requests, item_collector, response)

        if ec.got_err:
            pass

        return result

    @staticmethod
    def enrich_scu_base_data(item_loader, response):
        items = response.meta['jay']['data']
        for item in items:
            if item['item_type'] == 'Spu':
                items.remove(item)
        item_loader.add_value('sku_items', items)

        item_loader.add_value('url', response.url)

        if type(response.meta['jay']['data']) == str:
            product_id = response.meta['jay']['data']
        else:
            product_id = [item['item_id'].split('#')[1]
                          for item in response.meta['jay']['data'] if item['item_type'] == 'Sku'][0]
        item_loader.add_value('product_id', product_id)
        # item_loader.add_value('meta', dict(
        #     command=response.meta['jay']['command']))
        item_loader.add_value('timestamp', time.time())
        item_loader.add_value('status_code', response.status)
        item_loader.add_value('status_msg', response_status_message(response.status))
        item_loader.add_value('domain', urlparse(response.url).hostname.split('.', 1)[1])
        item_loader.add_value('response_url', response.url)
        item_loader.add_value('item_type', "Spu")
        # item_loader.add_value('meta', dict(command=response.meta['jay']['command']))
        item_loader.add_value('scu_url', response.url)  # 链接

    @enrich_wrapper
    def enrich_scu_data(self, item_loader, response):
        raise NotImplementedError

    def yield_item(self, requests, item_collector, response):
        if requests:
            item_collector.add_requests(requests)

        if item_collector.have_request():
            req = item_collector.pop_request()
            if isinstance(req, scrapy.http.Request):
                for k, v in response.request.meta['jay'].items():
                    if k not in req.meta['jay']:
                        req.meta['jay'][k] = v

                # req.meta['jay']['priority'] += 1
                req.callback = self.parse_next
                return req
            else:
                response.request.meta['jay'].update(req['meta'])
                # response.request.meta['jay']['priority'] += 1
                req['meta'] = response.request.meta
                req['callback'] = self.parse_next
                req['dont_filter'] = True
                return build_request(**req)
        else:
            item = item_collector.load_item()
            if response.meta['jay'].get('is_spu_dead', False):
                item['meta']['is_spu_dead'] = True
            product_id = item.get('product_id', None)
            if product_id:
                is_success = True
            else:
                product_id = 'unknown'
                is_success = False
            request_count = response.meta['jay'].get(
                'request_count_per_item', 1)
            self.logger.info(
                "item crawl report., crawlid: {crawlid}, request_count: {request_count}, "
                "product_id: {product_id}, success: {success}".format(
                    # local_ip=self.local_ip,
                    crawlid=item.get('crawlid'),
                    request_count=request_count,
                    product_id=product_id,
                    status_code=item.get('status_code'),
                    success=is_success
                ), extra={
                    # 'local_ip': self.local_ip,
                    'crawlid': item.get('crawlid'),
                    'request_count': request_count,
                    'product_id': product_id,
                    'status_code': item.get('status_code'),
                    'success': is_success
                })
            if item.get('status_code') != 999:
                # self.inc_crawled_pages(response.meta['jay']['crawlid'])
                # if is_success:
                #     self.inc_x_scu_crawled_find_spu(
                #         response.meta['jay']['crawlid'])
                pass
            else:
                item['status_msg'] = "".join(
                    response.xpath('//html/body/p/text()').extract())

            return item

    def parse_next(self, response):
        with ExceptContext(errback=self.log_err) as ec:
            # response.meta['jay']['request_count_per_item'] += 1
            meta = response.request.meta['jay']
            item_collector = meta['item_collector']
            path = meta['path']
            loader = item_collector.item_loader(path)
            prop = path.last_prop()
            # the method named 'enrich_***' defined in inherit spiders
            requests = getattr(self, 'enrich_%s' % prop)(loader, response)
            result = self.yield_item(requests, item_collector, response)

        if ec.got_err:
            pass

        return result

    def log_err(self, func_name, *args):
        self.logger.error("Error in %s: %s. " % (
            func_name, "".join(traceback.format_exception(*args))))
        return True

    def is_bad_redirect_location(self, request, response, redirect):
        """对CustomRedirectMiddleware的补充, 如果接下来的request没有必要继续发起请求, 返回True

        :redirect_req: 待重定向的request
        """
        return False

    @staticmethod
    def url_escape(url):
        if 'zenscrape' in url:
            url = urlparse(url).query.replace('url=', '').replace('%3A', ':').replace('&location=na', '')
        return url
