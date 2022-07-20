# -*- coding:utf-8 -*-
import json
import os
import urllib

from scrapy import Request
from scrapy.utils.project import get_project_settings

settings = get_project_settings()


# 经过测试发现：
# COOKIES_ENABLED为True时，cookie中设置cookie有效，header中cookie无效
# COOKIES_ENABLED为False时，cookie中设置cookie无效，header中cookie有效

def build_request(url,
                  callback=None,
                  method='GET',
                  body=None,
                  flags=None,
                  meta=None,
                  encoding='utf-8',
                  dont_filter=settings.get('DONT_FILTER', False),
                  errback=None,
                  proxy=True
                  ):
    headers = settings.get('HEADERS', {})
    cookies = settings.get('COOKIES', None)

    if os.getenv('ZENSCRAPE_API_KEY') and proxy:
        zenscrape_api_key = {
            'apikey': os.getenv('ZENSCRAPE_API_KEY', None)
        }
        headers.update(zenscrape_api_key)

        params = (
            ("url", urllib.parse.quote(url, safe='')),
            ("keep_headers", settings.get('KEEP_HEADERS', 'true')),
            ("premium", settings.get('PREMIUM', 'false'))
        )

        url = _get_url(params)

    return Request(url,
                   meta=meta,
                   callback=callback,
                   flags=flags,
                   method=method,
                   headers=headers,
                   body=body,
                   cookies=cookies,
                   encoding=encoding,
                   dont_filter=dont_filter,
                   errback=errback)


def _get_url(params):
    qs_params = dict()
    qs_params.update(params)

    qs = '&'.join(f'{k}={v}' for k, v in qs_params.items())
    return f'https://app.zenscrape.com/api/v1/get?{qs}'
