import json
import os
import shutil
import time

from jay.pipelines.base_pipeline import BasePipeline


class JSONPipeline(BasePipeline):
    """
    数据存储到json中
    """

    def __init__(self, settings):
        super(JSONPipeline, self).__init__(settings)
        self.logger.debug("Setup json pipeline.")
        self.files = {}
        self.setup()

    def create(self, crawlid):
        file_name = "task/%s_%s.json" % (self.crawler.spidercls.name, crawlid)
        if os.path.exists(file_name):
            shutil.copy(file_name, "%s.%s" %
                        (file_name, time.strftime("%Y%m%d%H%M%S")))

        fileobj = open(file_name, "w")
        self.files[file_name] = fileobj
        return fileobj

    def setup(self):
        if not os.path.exists("task"):
            os.mkdir("task")

    def process_item(self, item, spider):
        self.logger.debug("Processing item in JSONPipeline.")
        crawlid = item["crawlid"]
        file_name = "task/%s_%s.json" % (spider.name, crawlid)
        fileobj = self.files.get(file_name) or self.create(crawlid)
        fileobj.write("%s\n" % json.dumps(dict(item)))
        return item

    def spider_closed(self):
        self.logger.info("close file...")
        for fileobj in self.files.values():
            fileobj.close()
