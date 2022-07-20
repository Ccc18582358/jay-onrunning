import re

from jay.pipelines.base_pipeline import BasePipeline


def check_re_id(re_exp, string):
    res = re.search(re_exp, string)
    if res and res.group(0) == string:
        return True
    else:
        return False


class AssertPipeline(BasePipeline):

    def __init__(self, settings):
        super(AssertPipeline, self).__init__(settings)
        self.min_quantity = self.settings.get('IMAGE_QUANTITY_MIN')
        self.max_quantity = self.settings.get('IMAGE_QUANTITY_MAX')

    def process_item(self, item, spider):
        self.logger.debug("Start to test.html")
        command = item['command']
        refs = item['references']
        items = item['items']
        # 暂时没有"更新"的check
        if command == 'UPDATE':
            return item
        assert command in ['DISCOVER', 'UPDATE'], 'unknown command'
        callback = item['trace']['command']['callback']
        self.check_refs(refs, callback)
        self.check_items(items)
        self.crawler.stats.inc_value('scraped_spu_count')
        self.crawler.stats.inc_value('scraped_sku_count', count=len(item['items'][0]['skus']))
        return item

    def check_refs(self, refs, callback):
        # 所有的item_type:album,image,feature,spec,title,desc,color,size,width,sku
        if callback == 'parse_tag':
            assert len(refs) == 0, 'Not empty reference'
            return
        assert len(refs) > 0, 'empty reference'
        total_availability = False
        # 库存警告
        for sku_info in list(filter(lambda x: x['item_type'] == 'Sku', refs)):
            if sku_info['dyno_info']['availability']:
                total_availability = True
        if not total_availability:
            self.logger.warning('all sku stocks is empty')
        # album检查图片数量，检查是否有主图
        for album_info in list(filter(lambda x: x['item_type'] == 'Album', refs)):
            quantity = len(album_info['images'])
            origin_count = 0
            assert quantity in range(self.min_quantity, self.max_quantity), 'unexpected image quantity'
            for image_info in album_info['images']:
                image = \
                    list(filter(lambda x: x['item_type'] == 'Image' and x['item_id'] == image_info['item_id'], refs))[0]
                if image['init']:
                    origin_count = origin_count + 1
            assert origin_count == 1, 'wrong origin image'

    def check_items(self, items):
        assert len(items) > 0, 'empty items'
        # 主要检查id，是否有多余#, 是否为空
        spu_info = items[0]
        spu_id = spu_info['item_id']
        assert spu_id.count('#') == 1, 'more than one "#"'
        res = check_re_id(r'(\w|-|\s)+', spu_id.partition('#')[2])
        assert res, 'spu_id not match re'
        product_id = spu_id.split('#')[1]
        assert product_id != '', 'spu_id is None'
        for sku in spu_info['skus']:
            sku_id = sku['item_id'].split('#')[2]
            res = check_re_id(r'(\w|-|\s|/)+', sku_id)
            assert res, 'sku_id not match re'
            assert sku_id != '', 'sku_id is None'
            assert sku['item_id'].count('#') == 2, 'more than two "#"'
            assert sku_id != 'null', 'sku_id is "null"'
            assert sku_id != 'None', 'sku_id is "None"'
