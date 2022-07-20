import datetime
import json
import logging
import pprint

from rocketmq.client import Producer, Message
from scrapy.statscollectors import StatsCollector
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)


class RocStatsCollector(StatsCollector):

    def __init__(self, crawler):
        super().__init__(crawler)
        self.settings = get_project_settings()

    def close_spider(self, spider, reason):
        self.dump_to_rocket()
        if self._dump:
            logger.info("Dumping Roc stats:\n" + pprint.pformat(self._stats),
                        extra={'spider': spider})
        self._persist_stats(self._stats, spider)

    def dump_to_rocket(self):
        try:
            producer = Producer('BDP_Process', max_message_size=1024 * 1024)
            producer.set_name_server_address(self.settings.get('ROCKETMQ_ADDRESS'))
            producer.start()

            msg_body = json.dumps(self._stats, cls=DateEncoder, ensure_ascii=False).encode('utf-8')

            msg = Message(self.settings.get('ROCKETMQ_TOPIC'))
            msg.set_body(msg_body)
            msg.set_keys('keys')
            msg.set_tags('tags')

            result = producer.send_sync(msg)
            logger.info(f'ROCKETMQ result status:{result.status}, id:{result.msg_id}, offset:{ result.offset}')
            producer.shutdown()
        except:
            pass


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return json.JSONEncoder.default(self, obj)
