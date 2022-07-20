# -*- coding: utf-8 -*-
"""
Created on 2018年11月9日

@author: Sunxianliang
"""
import sys
import logging
import logging.config


def get_default_log_config():
    LOG_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        # 'incremental': True,
        'formatters': {
            'default': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(levelname)-8s %(name)-15s %(processName)-10s %(threadName)-10s [%(filename)s:%(lineno)d] %(message)s',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
            },
            'file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': 'logfile.log',
                # 'mode': 'a',
                'backupCount': 30,
                'formatter': 'default',
            },
            # https://pypi.org/project/python-logstash/
            'logstash': {
                'level': 'DEBUG',
                'class': 'logstash.LogstashHandler',
                'host': 'localhost',
                'port': 5230,  # Default value: 5959
                'version': 1,  # Version of logstash event schema. Default value: 0 (for backward compatibility of the library)
                'message_type': 'logstash',  # 'type' field in logstash message. Default value: 'logstash'.
                'fqdn': False,  # Fully qualified domain name. Default value: false.
                'tags': None,  # ['tag1', 'tag2'],  # list of tags. Default: None.
            },
        },
        'loggers': {
           # 'console': {
           #     'level': 'DEBUG',
           #     'handlers': ['console'],
           #     'propagate': False,
           # },
           # 'file': {
           #     'level': 'DEBUG',
           #     'handlers': ['file'],
           #     'propagate': True,
           # },
           # 'logstash': {
           #     'level': 'DEBUG',
           #     'handlers': ['logstash'],
           #     'propagate': True,
           # },
        },
        'root': {
            'level': 'WARN',
            'handlers': ['console'],
        },
    }
    return LOG_CONFIG


def get_logger(name, enable_console=True, enable_file=False, enable_logstash=False, log_level='DEBUG',
               file_name='logfile.log', logstash_host='localhost', logstash_port=5230, logstash_tags=None):
    log_config = get_default_log_config()

    my_logger_handlers = []
    log_config['loggers'][name] = {
        'level': log_level,
        'handlers': my_logger_handlers,
        'propagate': False,  ## 不会继续继承root
    }

    if enable_console:
        my_logger_handlers.append('console')

    if enable_file:
        log_config['handlers']['file']['filename'] = file_name
        my_logger_handlers.append('file')
    else:
        del log_config['handlers']['file']

    if enable_logstash:
        log_config['handlers']['logstash']['host'] = logstash_host
        log_config['handlers']['logstash']['port'] = logstash_port
        if isinstance(logstash_tags, list):
            log_config['handlers']['logstash']['tags'] = logstash_tags
        my_logger_handlers.append('logstash')

    logging.config.dictConfig(log_config)
    return logging.getLogger(name)


def get_logger_from_crawler(crawler):
    if crawler.spider:
        return crawler.spider.logger
    else:
        return logging.getLogger()

def make_logger_from_crawler(crawler):
    settings = crawler.settings
    name = crawler.spidercls.name
    log_level = settings.get('SC_LOG_LEVEL', 'DEBUG')
    enable_console = settings.getbool('SC_LOG_STDOUT', True)
    enable_file = settings.getbool('SC_LOG_FILE', False)
    enable_logstash = settings.getbool('SC_LOG_LOGSTASH', False)
    logstash_host = settings.get("SC_LOG_LOGSTASH_HOST", '127.0.0.1')
    logstash_port = settings.getint("SC_LOG_LOGSTASH_PORT", 5230)
    return get_logger(name, enable_console, enable_file, enable_logstash, log_level,
                      logstash_host=logstash_host, logstash_port=logstash_port)


def get_log_extra(request=None, response=None, extra={}):
    """优先使用参数带入的request, 其次使用response.request"""
    if isinstance(extra, dict):
        pass
    else:
        extra = {}

    if not request and response.request:
        request = response.request

    if request:
        extra['crawlid'] = request.meta.get('crawlid')
        extra['request_url'] = request.url
        extra['proxy'] = request.meta.get('proxy')

    if response:
        extra['status_code'] = response.status
        extra['response_url'] = response.url

    return extra


if __name__ == '__main__':

    logger0 = logging.getLogger('cccccc')
    logger0.warn('000000')

    logger = get_logger('abc')
    logger.debug("hello you guys")

    logger2 = get_logger('x-men', enable_logstash=True, enable_console=True)
    extra = {
        'test_string': 'python version: ' + repr(sys.version_info),
        'test_boolean': True,
        'test_dict': {'a': 1, 'b': 'c'},
        'test_float': 1.23,
        'test_integer': 123,
        'test_list': '[1, 2, \'3\']',
    }
    logger2.info('python-logstash: test.html extra fields 2', extra=extra)
    logger.debug('python-logstash: test.html extra fields 1', extra=extra)
    logger0.warn('000000')
