import os
import sys

from scrapy.cmdline import execute

if __name__ == '__main__':
    type = 'update'
    callback = 'parse'
    priority = '1000'
    full = 'True'
    extended = 'True'
    force = 'True'
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    execute(['scrapy', 'crawl', 'spider_update',
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
             ]
            )
