import json
import sys

from kafka import KafkaProducer

from jay.pipelines.base_pipeline import BasePipeline
from jay.tools.stringcase import uppercase
from jay.utils import ItemEncoder


class KafkaPipeline(BasePipeline):
    """
        Pushes a serialized item to appropriate Kafka topics.
    """

    def __init__(self, settings):
        super(KafkaPipeline, self).__init__(settings)
        self.logger.debug("Setup kafka pipeline")
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings['KAFKA_HOSTS'].split(","), retries=3)
        except:
            self.logger.error(
                "Unable to connect to Kafka in Pipeline, raising exit flag. ")
            sys.exit(1)

    def errback(self, exception):
        self.logger.error("Error in kafka feature: %s. " % str(exception))

    def callback(self, value):
        self.logger.debug("Success in kafka feature: %s. " % str(value))

    def process_item(self, item, spider):
        command = item.get("command")
        try:
            command_type = item['trace']['command']['type']
        except:
            command_type = 'UPDATE'
        if command is None and not (command in ['discover', 'update', 'enrich', 'fetch']):
            self.logger.warn("Not valid command: {}".format(command))
        else:
            topic_key = "KAFKA_TOPIC_{}".format(uppercase(command_type))
            topic = self.settings.get(topic_key)

            self.logger.debug("Sending item to kafka topic: %s" % topic)
            try:
                message = json.dumps(item, cls=ItemEncoder)
            except UnicodeDecodeError:
                message = json.dumps(item, cls=ItemEncoder, encoding="gbk")
            future = self.producer.send(topic, message.encode())

            future.add_callback(self.callback)
            future.add_errback(self.errback)
            return item
