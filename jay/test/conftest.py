from functools import reduce
from hashlib import md5

import pytest

"""
生成测试用的references和items
session表示可以跨文件调用
conftest名字固定，不能修改
"""

source_site_code = "TEST"
_spu_id = 'test_spu'
_sku_id = 'test_sku'
_color = 'test_color'
image_list = ['http://192.168.200.71:8888/amazon/250c79757f5a35cf27ab0b9e464764d95b9e042e.jpg',
              'http://192.168.200.71:8888/amazon/cc7d7d2c7fcbb59037449c6b9a24713c3f80a62c.jpg']


@pytest.fixture(scope="session")
def refs():
    refs = list()
    o_images = list()
    _init = True
    for image in image_list:
        o_image = enrich_image(_spu_id, _color, image, image.split('/')[-1], _init, )
        o_images.append(o_image)
        refs.append(o_image)
        _init = False
    o_album = enrich_album(_spu_id, _color, *o_images)
    refs.append(o_album)
    return refs


@pytest.fixture(scope="session")
def items():
    items = []
    spu_info = {
        'item_type': 'Spu',
        'item_id': f'{source_site_code}#{_spu_id}',
        'skus': [
            {
                'item_id': f'{source_site_code}#{_spu_id}#{_sku_id}',
                'item_type': 'Sku'
            }
        ]
    }
    items.append(spu_info)
    return items


def enrich_album(spu_id, color, *images):
    album = enrich_reference("album")
    album["item_id"] = generate_identifier(spu_id, color.capitalize())
    album["images"] = prop_keeper(images)
    return album


def enrich_image(spu_id, color, url, path, init=False, _type=""):
    image = enrich_reference("image")
    image["item_id"] = generate_identifier(
        spu_id, color.capitalize(), _type or md5_encode(url))
    image["url"] = url
    image["path"] = path
    image["init"] = init
    image["type"] = _type
    image["origin"] = True
    return image


def enrich_reference(_type, *names):
    reference = dict()
    reference["item_type"] = generate_identifier(
        _type.capitalize(), *map(lambda name: name.capitalize(), names))
    return reference


def generate_identifier(prefix, *tags):
    return reduce(lambda x, y: "%s::%s" % (x, y), tags, prefix)


def md5_encode(string, count=6):
    return md5(str(string).encode()).hexdigest()[:count]


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
