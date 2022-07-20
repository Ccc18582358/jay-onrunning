# -*- coding:utf-8 -*-
from ..cust_logger import get_logger_from_crawler


class AbstractDownloaderMiddleware(object):

    def __init__(self, settings):
        self.logger = get_logger_from_crawler(self.crawler)
        self.settings = settings

    @classmethod
    def from_crawler(cls, crawler):
        cls.crawler = crawler
        obj = cls(crawler.settings)
        return obj
