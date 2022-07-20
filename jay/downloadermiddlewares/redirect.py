# -*- coding: utf-8 -*-
from urllib.parse import urljoin

from w3lib.url import safe_url_string
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message

from jay.downloadermiddlewares import AbstractDownloaderMiddleware


class CustomRedirectMiddleware(AbstractDownloaderMiddleware, RedirectMiddleware):

    def __init__(self, settings):
        RedirectMiddleware.__init__(self, settings)
        AbstractDownloaderMiddleware.__init__(self, settings)
        self.stats = self.crawler.stats

    def process_response(self, request, response, spider):
        if request.meta.get('dont_redirect', False):
            return response

        redirected_url = None
        if 'Location' in response.headers:
            redirected_url = urljoin(request.url, safe_url_string(response.headers['location']))

        if not redirected_url:
            return response

        redirected = None
        if not self.settings.get('CHANGE_URL', True):
            return request
        else:
            if response.status in [302, 303, 429]:
                redirected = self._redirect_request_using_get(request, redirected_url)
            elif response.status in [301]:
                redirected = request.replace(url=redirected_url)
            elif response.status in [307]:
                redirected = request
            if not redirected:
                return response

        return self._redirect(redirected, request, spider, response)

    def _redirect(self, redirect, request, spider, response):
        reason = response_status_message(response.status)

        redirect_times = request.meta.get('redirect_times', 0) + 1

        # 检查重定向的地址是因为商品已经不存在或者拒绝访问而导致的
        is_bad_redirect_location = spider.is_bad_redirect_location(request, response, redirect)
        is_spu_dead = is_bad_redirect_location and request.meta.get('is_spu_dead', False)
        is_blocked_location = is_bad_redirect_location and not request.meta.get('is_spu_dead', False)

        if redirect_times <= self.max_redirect_times and not is_spu_dead:
            # 重定向次数
            redirect.meta['redirect_times'] = redirect_times
            # 记录重定向的urls历史
            redirect.meta.setdefault('redirect_urls', []).append(request.url)
            # 提高抓取优先级
            # redirect.meta['priority'] = redirect.meta['priority'] + self.priority_adjust

            self.logger.warn("Redirecting %s to %s from %s for %s times" % (reason, redirect.url,
                                                                            request.url,
                                                                            redirect.meta.get("redirect_times")),
                             extra={
                                 'redirect_url': redirect.url,
                                 'redirect_times': redirect_times,
                                 'original_url': redirect.meta['redirect_urls'][0]
                             })
            if is_blocked_location:
                redirect.replace(url=request.url)

            return redirect

        self.logger.warn("Discarding %s, redirection count: %d, original url: %s" % (redirect.url,
                                                                                     redirect_times,
                                                                                     request.meta.get('url')),
                         extra={
                             'redirect_url': redirect.url,
                             'redirect_times': redirect_times,
                             'original_url': redirect.meta['redirect_urls'][0] if 'redirect_urls' in redirect.meta else request.url
                         })

        if request.meta.get('callback') == 'parse':
            # 对于分类页失败，总数+1
            self.crawler.stats.inc_total_pages(crawlid=request.meta['crawlid'])
            self.logger.error(
                    "in redicrect request error to failed pages url:%s, exception:%s, meta:%s" % (
                            request.url, reason, request.meta)
            )
        elif request.meta.get('callback') == 'parse_scu':
            # 对于item解析, 算作解析成功, 计数到extracted
            self.crawler.stats.incr_x_scu_crawled(crawl_id=request.meta['crawlid'])
        else:
            pass

        raise IgnoreRequest("got a denied location or max redirections reached: %s" % reason)
