# -*- coding:utf-8 -*-
import json
import os
import re
from functools import reduce
from operator import itemgetter

import jsonpath
import requests
import scrapy
from toolkit import groupby

from onrunning.items import OnrunningItem
from onrunning.spiders.onrunning_spider import OnrunningSpider
from jay.request import build_request
from jay.spiders.update_spider import UpdateSpider
from jay.utils import CustomLoader, enrich_wrapper, ItemCollectorPath


class OnrunningUpdateSpider(UpdateSpider):
    name = "onrunning_update"
    redis_key = "ONRUNNING:COMMANDS"
    # sku是否需要跳转到新的url
    redirect_sku = False

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

    @staticmethod
    def spu_is_dead(response):
        if response.status == 404:
            return True
        return False
