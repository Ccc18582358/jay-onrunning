import os
import sys
from scrapy.dupefilters import RFPDupeFilter
from scrapy.cmdline import execute

if __name__ == '__main__':
    crawlid = 'crawlid-test'
    type = 'discover'
    # type = 'fetch'
    priority = '1000'
    full = 'True'
    extended = 'True'
    force = 'True'
    urls = 'https://www.on-running.com/en-us/explore/mens/apparel/pants?page=last'
    callback = 'parse'
    # callback = 'parse_tag'
    meta = '{"source_site_code":"ONRUNNING","brand_code":"citizen","gender_code":"famale","taxon_code":"watch","brand_id":205,"source_site_id":8,"gender_id":2,"taxon_id":831,"tags":[]}'
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    execute(['scrapy', 'crawl', 'onrunning',
             '-a',
             'crawlid=' + crawlid,
             '-a',
             'type=' + type,
             '-a',
             'callback=' + callback,
             '-a',
             'priority=' + priority,
             '-a',
             'full=' + full,
             '-a',
             'extended=' + extended,
             '-a',
             'force=' + force,
             '-a',
             'urls=' + urls,
             '-a',
             'meta=' + meta]
            )
