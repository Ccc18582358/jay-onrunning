import json

from scrapy.utils.misc import load_object

from jay.items import BaseItem
from jay.pipelines.base_pipeline import BasePipeline
from jay.tools.stringcase import capitalcase, lowercase


class AdaptPipeline(BasePipeline):

    def __init__(self, settings):
        super(AdaptPipeline, self).__init__(settings)

    def process_item(self, item, spider):
        self.logger.debug("Start to adapt")
        if (item is None) or (not isinstance(item, BaseItem)):
            return item
        item_doc_adapter = self.get_item_doc_adapter(item.__class__.__name__)
        result = item_doc_adapter.process_item(item, spider)
        self.logger.info(json.dumps(result['items']))
        self.logger.debug(json.dumps(result))

        return result

    # 转化为SpiderItemDocAdapter
    def get_item_doc_adapter(self, jay_item_class_name):
        spider_name = jay_item_class_name[:-4]  # strip tail 'Item'

        item_doc_adapter_class_name = "{lower_spider_name}.adapters.{capital_spider_name}ItemDocAdapter".format(
            capital_spider_name=capitalcase(spider_name),
            lower_spider_name=lowercase(spider_name).replace('api', '').replace('rainforest', '')
        )
        adapter = load_object(item_doc_adapter_class_name)()
        adapter.logger = self.logger
        return adapter
