import datetime
import re

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from jay.spidermiddlewares import JaySpiderMiddleware


class InfluxDBMiddleware(JaySpiderMiddleware):

    def __init__(self, crawler):
        super(InfluxDBMiddleware, self).__init__(crawler)
        self.influxdb_org = crawler.settings.get(
            "INFLUXDB_ORG", 'jinanlongen.com')
        self.influxdb_bucket = crawler.settings.get("INFLUXDB_BUCKET", 'jay')
        self.influxdb_measurement = self.settings.get("MESUREMENT", "jay")

        self.client = InfluxDBClient(
            url=crawler.settings.get("INFLUXDB_URL", '127.0.0.1:8086'),
            token=crawler.settings.get("INFLUXDB_TOKEN", ""))
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

        self.logger.info("InfluxDB connected: {}, org:{}, bucket: {}, measurement: {}".format(
            self.client.url, self.influxdb_org, self.influxdb_bucket, self.influxdb_measurement))

    def process_item_output(self, item, response, spider):
        meta = item.get("meta", {})

        site = meta.get("source_site_code")
        command_type = meta.get("type")
        if site:
            point = Point(self.influxdb_measurement).time(datetime.datetime.utcnow()).tag("app", self.__class__.__name__).tag(
                "item_type", "item").tag("site", site).tag("command_type", command_type).tag(
                    "crawlid", item["crawlid"]).field("value", 1).field("etc", "")

            self.write_api.write(self.influxdb_bucket,
                                 self.influxdb_org, point)
        else:
            self.logger.warn("Invalid item, NO SITE: {}".format(str(item)))
        return item


class UpdateMiddleware(JaySpiderMiddleware):

    def __init__(self, crawler):
        super(UpdateMiddleware, self).__init__(crawler)
        self.client = InfluxDBClient(
            crawler.settings.get("INFLUXDB_HOST", '192.168.200.131'),
            crawler.settings.get("INFLUXDB_POST", 8086),
            crawler.settings.get("INFLUXDB_USERNAME", ""),
            crawler.settings.get("INFLUXDB_PASSWORD", ""),
            crawler.settings.get("INFLUXDB_DB", 'db_roc'))
        self.regex = re.compile("roc_\d+")

    def process_item_output(self, item, response, spider):
        if self.regex.search(item["crawlid"]):
            table_name = self.settings.get("MESUREMENT", "blender")
            tags = {"app": "jay", "command": "UPDATE",
                    "site": item["meta"].get("source_site_code")}
            fields = {"value": 1}
            self.client.write_points([{
                "measurement": table_name,
                "tags": tags,
                "time": datetime.datetime.utcnow(),
                "fields": fields
            }])
        return item
