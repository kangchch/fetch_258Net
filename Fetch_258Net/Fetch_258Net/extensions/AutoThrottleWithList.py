# -*-coding:utf-8-*-

from scrapy.contrib.throttle import AutoThrottle
import logging
import re


class AutoThrottleWithList(AutoThrottle):
    ''' AutoThrottle with a name list so that the spider limits its
        speed only for the sites on the list '''

    # param: site_list: list contains the domain to be limited
    def __init__(self, crawler):
        super(AutoThrottleWithList, self).__init__(crawler)
        self.limit_list = crawler.settings.get("LIMIT_SITES", [])
        self.logger = logging.getLogger('AutoThrottle')
        self.logger.info("AutoThrottle Load")
        limit_list = []
        for item in self.limit_list:
            regex = item.get('REGEX', '')
            dealy_time = item.get('DEALY_TIME', 0)
            if regex and dealy_time > 0:
                limit_list.append(item)
        self.limit_list = limit_list

    def _adjust_delay(self, slot, latency, response):
        """override AutoThrottle._adjust_delay()"""
        if not self.limit_list:
            return None

        for item in self.limit_list:
            if re.match(item['REGEX'], response.url):
                latency = item['DEALY_TIME']
                self.logger.debug("[%s] dealy:%d url:%s" % (item['ID'], latency, response.url))
                super(AutoThrottleWithList, self)._adjust_delay(slot, latency, response)
                return None

        # default
        slot.delay = 0.0
