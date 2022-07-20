# -*- coding:utf-8 -*-

from scrapy.signals import spider_closed

from jay.cust_logger import get_logger_from_crawler
from .file_pipeline import FilePipeline
from .adapt_pipeline import AdaptPipeline
from .json_pipeline import JSONPipeline
from .kafka_pipeline import KafkaPipeline
from .assert_pipeline import AssertPipeline



