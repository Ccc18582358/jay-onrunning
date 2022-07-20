import datetime

from scrapy.statscollectors import StatsCollector
from redis import Redis

# key, filed, value
#
# crawlid:<crawlid>
#       failed_download_<type>: count
#       total_pages
#       crawled_pages
#       x_pages_total
#       x_pages_loaded
#       x_pages_failed
#       x_pages_crawled
#       x_items_total
#       x_items_crawled
#       x_items_crawled_find_spu
#
# failed_download_<type>:<crawid>
#       url, reason
#
# crawlid:<crawlid>#failed_download_<type>
# crawlid:<crawlid>#total_pages
#


def split_key_path(key_path):
    return key_path.split('#')


class RedisStatsCollector(StatsCollector):
    def __init__(self, crawler, spider=None):
        super().__init__(crawler)
        self.spider = spider
        self.crawler = crawler
        self.expired_time = 7 * 60 * 60 * 24  # 4 days

        host = self.crawler.settings.get("REDIS_HOST")
        port = self.crawler.settings.get("REDIS_PORT")
        self.redis = Redis(host, port)

    @classmethod
    def from_spider(cls, spider):
        return cls(spider.crawler, spider)

    def clear_stats(self, spider=None):
        self._stats.clear()

    # Get all stats:
    def get_stats(self, spider=None):
        return self._stats

    # Set all stats:
    def set_stats(self, stats, spider=None):
        self._stats = stats

    # Get stat value
    def get_value(self, key_path, default=None, spider=None):
        result = None
        splitted_key_path = split_key_path(key_path)

        if len(key_path) == 1:
            [key] = splitted_key_path
            result = self.redis.get(key)
        elif len(key_path) == 2:
            [key, field] = splitted_key_path
            result = self.redis.hget(key, field)

        if result is None:
            return default
        else:
            return result

    # Set stat value
    def set_value(self, key_path, value, spider=None):
        splitted_key_path = split_key_path(key_path)

        if(value is not datetime):
            value = str(value)

        if len(splitted_key_path) == 1:
            [key] = splitted_key_path
            return self.redis.set(key, value)
        elif len(splitted_key_path) == 2:
            [key, field] = splitted_key_path
            return self.redis.hset(key, field, value)

    # Increment stat value
    def inc_value(self, key_path, count=1, start=0, spider=None):
        splitted_key_path = split_key_path(key_path)

        if len(splitted_key_path) == 1:
            [key] = splitted_key_path
            return self.redis.incr(key, count)
        elif len(splitted_key_path) == 2:
            [key, field] = splitted_key_path
            return self.redis.hincrby(key, field, count)

    # Set stat value only if greater than previous
    def max_value(self, key_path, value, spider=None):
        splitted_key_path = split_key_path(key_path)

        old_value = value
        if len(splitted_key_path) == 1:
            [key] = splitted_key_path
            old_value = self.redis.get(key)
        elif len(splitted_key_path) == 2:
            [key, field] = splitted_key_path
            old_value = self.redis.hget(key, field)

        if(value is not None) and (old_value is not None) and (value > old_value):
            return self.set_value(key, value)
        else:
            return old_value

    # Set stat value only if lower than previous
    def min_value(self, key_path, value, spider=None):
        splitted_key_path = split_key_path(key_path)

        old_value = value
        if len(splitted_key_path) == 1:
            [key] = splitted_key_path
            old_value = self.redis.get(key)
        elif len(splitted_key_path) == 2:
            [key, field] = splitted_key_path
            old_value = self.redis.hget(key, field)

        if(value is not None) and (old_value is not None) and (value < old_value):
            return self.set_value(key, value)
        else:
            return old_value
