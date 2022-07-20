import os
import sys

from scrapy.cmdline import execute

if __name__ == '__main__':
    crawlid = 'crawlid-test'
    type = 'discover'
    priority = '1000'
    full = 'True'
    extended = 'True'
    force = 'True'
    callback = 'parse_scu'
    urls = ''  # callback = 'parse'

    meta = '{"source_site_id":1,"source_site_code":"AMZN","brand_id":153,"brand_code":"chloe","gender_id":2,"gender_code":"female","taxon_id":846,"taxon_code":"sunglasses","tags":[]}'
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    execute(['scrapy', 'crawl', 'brooksrunning',
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
