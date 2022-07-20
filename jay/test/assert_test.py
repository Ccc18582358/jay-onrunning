import pytest
from loguru import logger


class TestCase:
    logger = logger
    min_quantity = 1
    max_quantity = 10

    def test_refs(self, refs):
        # 所有的item_type:album,image,feature,spec,title,desc,color,size,width,sku

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

    def test_items(self, items):
        assert len(items) > 0, 'empty items'
        # 主要检查id，是否有多余#, 是否为空
        spu_info = items[0]
        spu_id = spu_info['item_id']
        assert spu_id.count('#') == 1, 'more than one "#"'
        product_id = spu_id.split('#')[1]
        assert product_id != '', 'spu_id is None'
        for sku in spu_info['skus']:
            sku_id = sku['item_id'].split('#')[2]
            assert sku_id != '', 'sku_id is None'
            assert sku['item_id'].count('#') == 2, 'more than two "#"'


if __name__ == '__main__':
    pytest.main(['-s', 'assert_test'])
