import re
from operator import itemgetter

from toolkit import groupby

from jay.adapters import ItemDocAdapter


class OnrunningItemDocAdapter(ItemDocAdapter):

    @staticmethod
    def get_type(image_block):
        pass

    def process_custom(self, spu_id, package, item):
        """主要用来获取bullet和skus

        :param spu_id:
        :param package:
        :param item:
        :return:
        """
        size_comparison_table = {"Small": "S", "Medium": "M", "Large": "L"}
        skus = list()
        refs = package['references']
        o_title = self.enrich_title(spu_id, item['title'])
        refs.append(o_title)
        o_spec = self.enrich_specs(spu_id, item['spec'])
        refs.append(o_spec)
        o_desc = self.enrich_desc(spu_id, item['description'])
        refs.append(o_desc)
        o_feature = self.enrich_features(spu_id, item['feature'])
        refs.append(o_feature)
        o_width = None
        currency = 'USD'

        for sku_info in item['sku_info']:
            color_id = str(sku_info['color_id'])
            color = sku_info['color_v'].strip()
            o_color = self.enrich_color(spu_id, color_id, color)
            refs.append(o_color)
            o_images = []
            for img in sku_info['image_list']:

                init = True if 'g1.png' in img else False
                o_image = self.enrich_image(spu_id, color_id, img,
                                            self.gen_path('/', item['spiderid'], img), init,
                                            "")
                refs.append(o_image)
                o_images.append(o_image)
            o_album = self.enrich_album(spu_id, color_id, *o_images)
            refs.append(o_album)
            size_id = str(sku_info['size_id'])
            size = sku_info['size_v'].strip()
            o_size = self.enrich_size(spu_id, size_id, size)
            refs.append(o_size)

            url = sku_info['url']
            price = sku_info['price']
            available = sku_info['available']
            available_reason = None if available else 'Out Of Stock'
            stock = sku_info['stock']

            if item.get('meta') == '':
                tags = ''
            else:
                tags = item['meta']['command']['meta']['tags']
            o_dyno_info = self.enrich_dyno_info(price, price, available, available_reason, stock, currency)
            o_steady_info = self.enrich_steady_info(None, None, None, None,
                                                    o_album, [o_title, o_feature, o_spec, o_desc], o_color, o_size,
                                                    o_width)
            sku_id = '%s_%s' % (color_id, size_id)
            o_sku = self.enrich_sku(spu_id, sku_id, item['status_code'], tags, item['timestamp'],
                                    url,
                                    o_dyno_info, o_steady_info)
            skus.append(o_sku)
            refs.append(o_sku)
        return skus
