# -*- coding: utf-8 -*-
import traceback

from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from toolkit import get_ip
from twisted.web.client import ResponseFailed
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, ConnectionRefusedError, ConnectionDone, ConnectError, \
    ConnectionLost, TCPTimedOutError
from jay.downloadermiddlewares import AbstractDownloaderMiddleware


class CustomRetryMiddleware(AbstractDownloaderMiddleware, RetryMiddleware):
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError, ConnectionRefusedError, ConnectionDone,
                           ConnectError, ConnectionLost, TCPTimedOutError, ResponseFailed, TunnelError, IOError,
                           TypeError, ValueError)

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)
        AbstractDownloaderMiddleware.__init__(self, settings)

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY) and not request.meta.get('dont_retry', False):
            return self._retry(request, "%s:%s" % (exception.__class__.__name__, exception), spider)
        else:
            if request.meta.get("callback") == "parse":
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
            self.logger.error("in retry request error %s" % traceback.format_exc())
            raise IgnoreRequest("%s:%s unhandled error. " % (exception.__class__.__name__, exception))

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1
        spider.change_proxy = True
        request.meta['change_proxy'] = True
        request.meta.pop('dont_change_proxy', None)
        if retries <= self.max_retry_times:
            retry_req = request.copy()
            retry_req.meta['retry_times'] = retries
            retry_req.dont_filter = True
            self.logger.warn("retries times: %s, yield request: %s, reason: %s." % (retries, request.url, reason))
            return retry_req
        else:
            if request.meta.get('callback') == 'parse':
                spider.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
            self.logger.error("in %s retry request error to failed pages url:%s, exception:%s" % (
                get_ip(), request.url, reason))
            self.logger.warn("[Give up] url: {url}, retries: {retries} times, reason: {reason}".format(url=request.url,
                                                                                                       retries=retries,
                                                                                                       reason=reason))
            raise IgnoreRequest(
                "Reason: {reason}, Retries: {retries} times.".format(reason=str(reason), retries=str(retries)))
