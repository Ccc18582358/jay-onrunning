import json
from jay.cust_logger import get_logger_from_crawler

from scrapy.http import Request


class JaySpiderMiddleware(object):

    def __init__(self, crawler):
        self.crawler = crawler
        self.settings = crawler.settings
        self.logger = get_logger_from_crawler(crawler)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_spider_output(self, response, result, spider):
        for spider_output in result:
            if isinstance(spider_output, Request):
                yield self.process_request_output(spider_output, response, spider)
            else:
                yield self.process_item_output(spider_output, response, spider)

    def process_item_output(self, item, response, spider):
        raise NotImplementedError

    def process_request_output(self, request, response, spider):
        return request


class AmazonMiddleware(JaySpiderMiddleware):
    def process_item(self, item, response, spider):
        node_ids = item["node_ids"]
        brand = item["brand"]
        if not (node_ids and brand):
            self.logger.info("%s miss node_ids or brand, node_ids: %s, brand: %s" % (
                item["url"], node_ids, brand))
        return item


class AreatrendMiddleware(JaySpiderMiddleware):

    def process_item(self, item, response, spider):
        data = spider.redis_conn.hget("areatrend:product", item["product_id"])
        if data:
            item["ware"] = json.loads(data)
        return item
