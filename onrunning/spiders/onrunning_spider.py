# -*- coding:utf-8 -*-
import json
import os
import re
import time

import urllib
from functools import reduce
import ast
from urllib.parse import urlparse, unquote, quote
import jsonpath
import lxml
import scrapy
from operator import itemgetter
from toolkit import groupby
from onrunning import settings
from jay.downloadermiddlewares import CustomProxyMiddleware
from jay.spiders.jay_spider import JaySpider
from onrunning.items import OnrunningItem
from jay.utils import CustomLoader, enrich_wrapper, ItemCollectorPath
import requests
from lxml import etree


def escape_url(url):
    if 'zenscrape' in url:
        parsed_url = urlparse(url)
        query = parsed_url.query
        new_url = unquote(dict([i.split('=') for i in query.split('&')])['url'])
        return new_url
    return url


class OnrunningSpider(JaySpider):
    name = 'onrunning'

    def enrich_tag(self, item_loader, response, product_id):
        data = json.loads(response.text)
        product_id = data['data']['productGroup']['slug']
        item_loader.add_value('product_id', product_id)
        return

    @staticmethod
    def get_item_loader(response):
        return CustomLoader(item=OnrunningItem())

    @enrich_wrapper
    def enrich_scu_data(self, item_loader, response):
        data = json.loads(response.text)
        product_id = data['data']['productGroup']['slug']
        title = data['data']['productGroup']['name']
        description = data['data']['productGroup']['productData']['description']
        variants = data['data']['productGroup']['productData']['variants']
        for variant in variants:
            url = variant['spreeProduct']['productUrl']
            image_list = ['https:' + img['mediaUrl'] for img in variant['assets'] if
                          img['mediaUrl'].endswith('.png')]
            color_id = variant['id']
            color_v = variant['color']
            size_list = variant['spreeProduct']['spreeVariants']
            for size in size_list:
                size_id = size['id']
                size_v = size['size']
                stock = size['stock']
                available = True if stock > 0 else False
                price = size['price']
                sku_info = {'size_id': size_id, 'color_id': color_id, 'color_v': color_v, 'size_v': size_v,
                            'available': available,
                            'price': price, 'stock': stock, 'url': url, 'image_list': image_list}
                item_loader.add_value('sku_info', sku_info)
        item_loader.add_value('product_id', product_id)
        item_loader.add_value('description', description)
        item_loader.add_value('title', title)

    def extract_scu_urls(self, response):
        data = json.loads(response.text)
        nodes = data['data']['filterPage']['paginatedItems']['nodes']
        urls = [node['variants'][0]['productUrl'] for node in nodes]
        return urls

    def extract_next_bucket_url(self, response):
        data = json.loads(response.text)
        has_next_page = jsonpath.jsonpath(data, '$..hasNextPage')[0]
        if has_next_page:
            end_cursor = jsonpath.jsonpath(data, '$..endCursor')[0]
            payload = response.meta['payload']
            payload['variables']['after'] = end_cursor
            headers = response.meta['headers']
            return scrapy.Request(method="POST", url=response.url, meta=response.meta,
                                  body=json.dumps(payload), headers=headers)
        return
