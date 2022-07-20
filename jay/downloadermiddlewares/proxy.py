# -*- coding: utf-8 -*-
import base64
import json
import random

import requests

from jay.downloadermiddlewares import AbstractDownloaderMiddleware


class CustomProxyMiddleware(AbstractDownloaderMiddleware):

    def __init__(self, settings):
        super(CustomProxyMiddleware, self).__init__(settings)
        self.es_headers = {'Content-Type': 'application/json'}
        self.es_proxy_url = "http://192.168.200.170:9200/turtle/_search?size=100"
        self.payload = json.dumps({"query": {"match": {"status": True}}})
        self.proxy_list = settings.get('PROXY_URLS', None)
        self.black_list = ['172.21.149.160', '172.21.104.160']

    def choice(self):
        response = requests.request("POST", self.es_proxy_url, data=self.payload, headers=self.es_headers)
        proxy_list = response.json()['hits']["hits"]
        for index, proxy in enumerate(proxy_list):
            if proxy['_source']['ip'] in self.black_list:
                proxy_list.remove(proxy)
        proxy_set = random.choice(proxy_list)
        return proxy_set

    def process_request(self, request, spider):
        if 'zenscrape' in request.url:
            return
        if self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta['proxy'] = proxy
            self.logger.debug("use proxy: %s to send request" % (request.meta['proxy']))
        else:
            # 要更新代理, 做下清理
            request.meta.pop('proxy', None)
            request.headers.pop('Proxy-Authorization', None)
            next_proxy = self.choice()
            if next_proxy:
                proxy = next_proxy['_source']['ip'] + ":" + str(next_proxy['_source']['port'])
                account_password = next_proxy['_source']['user'] + ":" + next_proxy['_source']['password']
                request.meta['proxy'] = 'http://' + proxy
                request.meta['download_timeout'] = 100
                request.meta['proxy_password'] = account_password
                encoded_account_password = base64.b64encode(account_password.encode('utf-8'))
                request.headers['Proxy-Authorization'] = b'Basic ' + encoded_account_password
                self.logger.debug("use PROXY: %s with AUTH: %s to send request" % (proxy, account_password))


class ScyllaProxyMiddleware(AbstractDownloaderMiddleware):

    def __init__(self, settings):
        super(ScyllaProxyMiddleware, self).__init__(settings)

    def process_request(self, request, spider):
        # 切换代理时, 清除cookie
        request.meta['proxy'] = 'http://192.168.200.36:8888'
        request.meta['download_timeout'] = 100
        self.logger.debug("use PROXY: %s to send request" % 'http://192.168.200.36:8888')
