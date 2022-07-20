from scrapy.signals import spider_closed

from jay.cust_logger import get_logger_from_crawler


class BasePipeline(object):

    def __init__(self, settings):
        self.settings = settings
        self.logger = get_logger_from_crawler(self.crawler)

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        o = cls(crawler.settings)
        crawler.signals.connect(o.spider_closed, signal=spider_closed)
        return o

    def process_item(self, item, spider):
        pass

    def spider_closed(self):
        pass
