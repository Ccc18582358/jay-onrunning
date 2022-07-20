# -*- coding:utf-8 -*-

import json
import time
import traceback
from abc import ABC, abstractmethod
from copy import deepcopy
from functools import reduce
from hashlib import md5, sha1
from os.path import join
from urllib.parse import urlparse, unquote
from toolkit.managers import ExceptContext

from jay.pipelines.utils import format_price, References


class Formatter(ABC):
    def __init__(self, *args, **kwargs):
        super(Formatter, self).__init__(*args, **kwargs)
        self.version = "1.0.0"

    @property
    @abstractmethod
    def settings(self):
        pass

    @staticmethod
    def md5_encode(string, count=6):
        return md5(str(string).encode()).hexdigest()[:count]

    @classmethod
    def gen_path(cls, base, spiderid, url):
        codec = cls.sha1_encode(url)
        return join(base, spiderid, "%s.jpg" % codec).replace('\\', '/')

    @staticmethod
    def sha1_encode(string):
        return sha1(string.encode()).hexdigest()

    def enrich_reference(self, _type, *names):
        reference = dict()
        reference["item_type"] = self.generate_identifier(
            _type.capitalize(), *map(lambda name: name.capitalize(), names))
        return reference

    def enrich_bullet(self, spu_id, string, *names, convert=None):
        if not string:
            return None
        bullet = self.enrich_reference("bullet", *names)
        bullet["item_id"] = self.generate_identifier(
            spu_id, self.md5_encode(string))
        bullet["en"] = convert(string) if convert else string
        return bullet

    def enrich_title(self, spu_id, title):
        return self.enrich_bullet(spu_id, title, 'title')

    def enrich_desc(self, spu_id, desc):
        return self.enrich_bullet(spu_id, desc, 'desc')

    def enrich_features(self, spu_id, features):
        if not features:
            return None
        return self.enrich_bullet(spu_id, json.dumps(features), 'features')

    def enrich_specs(self, spu_id, specs):
        if not specs:
            return None
        specs_list = []
        if isinstance(specs, dict):
            for k, v in specs.items():
                specs_list.append([k, v])
        else:
            specs_list = specs
        return self.enrich_bullet(spu_id, json.dumps(specs_list), 'specs')

    @staticmethod
    def generate_identifier(prefix, *tags):
        return reduce(lambda x, y: "%s::%s" % (x, y), tags, prefix)

    def enrich_album(self, spu_id, color, *images):
        album = self.enrich_reference("album")
        album["item_id"] = self.generate_identifier(spu_id, color.capitalize())
        album["images"] = self.prop_keeper(images)
        return album

    def enrich_image(self, spu_id, color, url, path, init=False, _type=""):
        image = self.enrich_reference("image")
        image["item_id"] = self.generate_identifier(
            spu_id, color.capitalize(), _type or self.md5_encode(url))
        image["url"] = url
        image["path"] = path
        image["init"] = init
        image["type"] = _type
        image["origin"] = True
        return image

    def enrich_dimension(self, spu_id, _type, key, value):
        if not (key or value):
            return None
        dimension = self.enrich_reference("dimension", _type)
        dimension["item_id"] = self.generate_identifier(
            spu_id, self.md5_encode(value))
        dimension["key"] = key
        dimension["value"] = value
        return dimension

    def enrich_size(self, spu_id, size_code, size_value):
        return self.enrich_dimension(spu_id, 'size', size_code, size_value)

    def enrich_color(self, spu_id, color_code, color_value):
        return self.enrich_dimension(spu_id, 'color', color_code, color_value)

    def enrich_width(self, spu_id, width_code, width_value):
        return self.enrich_dimension(spu_id, 'width', width_code, width_value)

    def enrich_sku(self, spu_id, sku_id, status_code, tags, timestamp, url, dyno_info, steady_info):
        sku = self.enrich_reference("sku")
        sku["item_id"] = "%s#%s" % (spu_id, sku_id)
        meta = dict()
        meta["timestamp"] = int(timestamp * 1000)
        meta["url"] = self.escape_url(url)
        sku["tags"] = tags or []
        meta["status_code"] = "NORMAL" if status_code < 300 else "ERROR"
        sku["meta"] = meta
        sku["dyno_info"] = dyno_info
        sku["steady_info"] = steady_info
        return sku

    def enrich_dead_sku(self, sku_id):
        """生成一个表示已经死去的sku, 告诉taz他已经死了, 日后无需采集

        :sku_id: SITE_NAME#SPU_CODE#SKU_CODE
        """
        sku = self.enrich_reference('sku')
        sku['item_id'] = sku_id
        dyno_info = self.enrich_dyno_info(
            0.0, 0.0, False, "", None, None, is_dead=True)
        sku['dyno_info'] = dyno_info
        return sku

    @staticmethod
    def enrich_dyno_info(price, list_price, availability, availability_reason, stock, currency, is_dead=False,
                         country=None, sales=None, bids=None, asks=None):
        if sales is None:
            sales = []
        if bids is None:
            bids = []
        if asks is None:
            asks = []

        dyno_info = dict()
        dyno_info["list_price"] = format_price(list_price) or -1
        dyno_info["price"] = format_price(price) or dyno_info["list_price"] or -1
        dyno_info["stock"] = stock
        dyno_info["availability"] = False if dyno_info["price"] == -1 else bool(
            dyno_info["price"] and availability and stock > 0)
        dyno_info["availability_reason"] = availability_reason
        dyno_info["currency"] = currency
        dyno_info['is_dead'] = is_dead
        dyno_info['country'] = country
        dyno_info['sales'] = str(["{}, {}".format(x['createdAt'], int(x['localAmount'])) for x in sales])
        dyno_info['bids'] = str(["{}, {}".format(x['node']['count'], int(x['node']['amount'])) for x in bids])
        dyno_info['asks'] = str(["{}, {}".format(x['node']['count'], int(x['node']['amount'])) for x in asks])
        return dyno_info

    @staticmethod
    def enrich_no_stock_dyno_info():
        dyno_info = dict()
        dyno_info["list_price"] = -1
        dyno_info["price"] = -1
        dyno_info["stock"] = 0
        dyno_info["availability"] = False
        dyno_info["availability_reason"] = 'This product is currently unavailable'
        return dyno_info

    def enrich_steady_info(self, upc, model_number, mpn, part_number, album, bullets, *dimensions,
                           condition="new", condition_detail="", ean=''):
        steady_info = dict()
        steady_info["upc"] = upc
        steady_info["model_number"] = model_number
        steady_info["ean"] = ean
        steady_info["mpn"] = mpn
        steady_info["part_number"] = part_number
        steady_info["condition"] = condition
        steady_info["condition_detail"] = condition_detail
        if album:
            steady_info["album"] = self.prop_keeper(album)[0]
        steady_info["dimensions"] = self.prop_keeper(dimensions)
        bts = self.prop_keeper(bullets)
        steady_info["bullets"] = bts
        return steady_info

    @staticmethod
    def prop_keeper(elements, *keys):
        new_elements = list()
        keys = keys or ["item_id", "item_type"]
        for element in elements if isinstance(elements, (list, tuple)) else [elements]:
            if isinstance(element, dict):
                new_element = dict()
                for key in keys:
                    new_element[key] = element[key]
                new_elements.append(new_element)
        return new_elements

    def create_item_doc(self):
        return {
            'version': self.version,
            'command': 'DISCOVER'
        }

    def create_dead_item_doc(self, items):
        return {
            'version': self.version,
            'command': 'UPDATE',
            'trace': {},
            # 'tags': [],
            'references': [],
            'items': self.enrich_dead_items(items)
        }

    def create_out_of_stock_item_doc(self, items):
        return {
            'version': self.version,
            'command': 'UPDATE',
            'trace': {},
            # 'tags': [],
            'references': [],
            'items': self.enrich_out_of_stock_items(items)
        }

    @staticmethod
    def enrich_dead_items(items):
        item_list = []
        for item in items['sku_items']:
            item_list.append({
                "item_type": item['item_type'],
                "item_id": item['item_id'],
                "meta": {
                    "url": item['item_url'],
                    "timestamp": int(time.time() * 1000)
                },
                "tags": [],
                "steady_info": {
                },
                "dyno_info": {
                    "list_price": 0,
                    "price": 0,
                    "stock": 0,
                    "currency": "",
                    "availability": False,
                    "availability_reason": "Spu not found",
                    "is_dead": True
                }
            })
        return item_list

    @staticmethod
    def enrich_out_of_stock_items(items):
        item_list = []
        for item in items['sku_items']:
            item_list.append({
                "item_type": item['item_type'],
                "item_id": item['item_id'],
                "meta": {
                    "url": item['item_url'],
                    "timestamp": int(time.time() * 1000)
                },
                "tags": [],
                "steady_info": {
                },
                "dyno_info": {
                    "stock": 0,
                    "currency": "",
                    "availability": False,
                    "availability_reason": "Out of Stock",
                    "is_dead": False
                }
            })
        return item_list

    def enrich_spu(self, spu_id, meta, status_code, *skus):
        item = dict()
        item["item_type"] = "Spu"
        item["item_id"] = spu_id
        item_meta = deepcopy(meta['command']['meta'])
        item_meta["url"] = self.escape_url(meta["url"])
        item_meta["timestamp"] = int(time.time() * 1000)
        item_meta["status_code"] = "NORMAL" if status_code < 300 else "ERROR"
        item_meta["all_skus"] = meta.pop('all_skus', True)
        item["meta"] = item_meta
        item["tags"] = item_meta.pop('tags', [])
        item["skus"] = self.prop_keeper(skus)
        return item

    def enrich_update_spu(self, spu_id, item, *skus):
        item_list = dict()
        item_list["item_type"] = "Spu"
        item_list["item_id"] = spu_id
        item_meta = dict()
        item_meta["url"] = item["url"]
        item_meta["timestamp"] = int(time.time() * 1000)
        item_meta["status_code"] = "NORMAL" if item["status_code"] < 300 else "ERROR"
        item_meta["all_skus"] = True
        item_list["meta"] = item_meta
        item_list["tags"] = item_meta.pop('tags', [])
        item_list["skus"] = self.prop_keeper(skus)
        return item_list

    @staticmethod
    def escape_url(url):
        if 'zenscrape' in url:
            parsed_url = urlparse(url)
            query = parsed_url.query
            new_url = unquote(dict([i.split('=') for i in query.split('&')])['url'])
            return new_url
        return url


class ItemDocAdapter(Formatter):
    settings = None
    logger = None

    @staticmethod
    def is_main(image_block):
        return False

    @staticmethod
    def get_type(image_block):
        return ""

    @staticmethod
    def position(image_block):
        return image_block

    @staticmethod
    def enrich_trace():
        return {
            'app': 'jay',
        }

    @abstractmethod
    def process_custom(self, spu_id, item_doc, item):
        return []

    def log_err(self, func_name, *args):
        self.logger.error("Error in %s: %s. " % (
            func_name, "".join(traceback.format_exception(*args))))
        return True

    def process_item(self, item, spider):
        # 死亡判断
        if item.get('is_dead') is True:
            return self.create_dead_item_doc(item)

        with ExceptContext(errback=self.log_err) as ec:
            item_doc = self.create_item_doc()
            command_dict = {
                "discover": "DISCOVER",
                "update": "UPDATE",
                "fetch": "DISCOVER",
                # "tag": "DISCOVER"
            }
            try:
                command = item['meta']['command']['type']
            except:
                command = "update"
            command_type = command_dict.get(command)
            if not command_type:
                self.logger.error("Unknown Command!")
                return
            item_doc["command"] = command_type
            references = References()
            item_doc["references"] = references

            if command_type == "DISCOVER":
                item_doc["trace"] = self.enrich_trace()
                item_doc["trace"]["seed"] = item["seed"]
                item_doc["trace"]["proxy"] = item["proxy"]
                item_doc["trace"]["crawlid"] = item["crawlid"]
                item_doc["trace"]["fingerprint"] = item["fingerprint"]
                item_doc['trace']['bucket_position'] = item['bucket_position']
                item_doc['trace']['bucket_url'] = item['bucket_url']
                item_doc['trace']['scu_position_in_bucket'] = item['scu_position_in_bucket']
                item_doc['trace']['scu_url'] = self.escape_url(item['scu_url'])
                item_doc['trace']['command'] = item["meta"]['command']
                item["meta"]["url"] = item["response_url"]
                spu_id = item["meta"].get("item_id") or "%s#%s" % (
                    item["meta"]['command']['meta'].get("source_site_code"), item["product_id"])
                if item['meta']['command']['callback'] != 'parse_tag':
                    skus = self.process_custom(spu_id, item_doc, item)
                else:
                    skus = []
                spu = self.enrich_spu(spu_id, item["meta"], item["status_code"], *skus)

            elif command_type == "UPDATE":
                item_doc["trace"] = self.enrich_trace()
                spu_id = spider.redis_key.split(':')[0] + "#" + item["product_id"]
                skus = self.process_custom(spu_id, item_doc, item)
                sku_items = item['sku_items']
                skus = self.enrich_all_sku(skus, sku_items)
                # 判断 r["item_id"] == sku["item_id"] 是不是重复的，如果重复，就进行下一次判断，不重复就将sku手动添加到references中
                for sku in skus:
                    jump = False
                    for r in references:
                        if r["item_id"] == sku["item_id"]:
                            jump = True
                            break
                    if jump:
                        continue
                    else:
                        references.append(sku)

                item_doc["references"] = references
                spu = self.enrich_update_spu(spu_id, item, *skus)
            item_doc["items"] = [spu]
        return item_doc

    def enrich_all_sku(self, skus, sku_items):
        new_sku_list = [sku['item_id'] for sku in skus]
        old_sku_list = [sku['item_id'] for sku in sku_items]
        # 先求交集再求差集
        no_stock_sku_list = list(set(new_sku_list) & set(old_sku_list) ^ set(old_sku_list))
        for i in no_stock_sku_list:
            skus.append(self.enrich_non_exist_sku(i))
        return skus

    @staticmethod
    def enrich_non_exist_sku(i):
        sample = {'item_type': 'Sku',
                  'item_id': i,
                  'tags': [],
                  'meta': {'timestamp': int(time.time() * 1000),
                           'url': 'https://www.baidu.com/',
                           'status_code': 'NORMAL'},
                  'dyno_info': {'list_price': 0,
                                'price': 0,
                                'stock': 0,
                                'availability': False,
                                'availability_reason': '',
                                'currency': 'USD',
                                'is_dead': False},
                  'steady_info': {}}
        return sample
