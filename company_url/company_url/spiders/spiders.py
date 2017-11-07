#! coding: utf-8

import requests
import os
import pymongo
from pymongo import MongoClient
import datetime
import logging
import scrapy
import re
import time
import traceback
from scrapy import log
import sys
from scrapy.conf import settings
from company_url.items import CompanyUrlItem
from scrapy.selector import Selector
from lxml import etree
from ipdb import set_trace


reload(sys)
sys.setdefaultencoding('utf-8')

class CompanyUrlSpider(scrapy.Spider):
    name = "fetch_258"
    allowed_domains = ['www.258.com']

    def __init__(self, settings, *args, **kwargs):
        super(CompanyUrlSpider, self).__init__(*args, **kwargs)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def start_requests(self):
        try:
            start_url = 'http://www.258.com/company/'
            yield scrapy.Request(url=start_url, callback=self.parse, dont_filter=True)
        except:
            self.log('start_request error! (%s)' % (str(traceback.format_exc())), level=log.INFO)

    ##遍历二级小行业的href
    def parse(self, response):
        sel = Selector(response)
        name_url = 'http://www.258.com'

        if response.status != 200:
            self.log('fetch failed! status=%d' % (response.status), level=log.WARNING)

        industy_hrefs = sel.xpath("//ul[@class='ProductIndexRightbox clearfix']//@href").extract()
        for href in industy_hrefs:
            meta = {'dont_redirect': True, 'href': href, 'dont_retry': True}
            yield scrapy.Request(url=name_url + href, meta=meta, callback=self.parse_two_page, dont_filter=True)

    ## 解析小行业的公司url
    def parse_two_page(self, response):
        sel = Selector(response)

        href_next = response.meta['href']

        i = CompanyUrlItem()
        if response.status != 200:
            self.log('fetch failed! status=%d' % (response.status), level=log.WARNING)

        url_xpaths = sel.xpath("//a[@class='fl mr20']")
        for url_xpath in url_xpaths:
            i['company_url'] = url_xpath.xpath("@href")[0].extract()
            yield i

        get_next = u"下一页"
        page_nums = sel.xpath("//ul[@class='pagination']/li/a/text()").extract()
        if get_next in page_nums:
            current_page = sel.xpath("//a[@class='Themebg ThemeFborder']/text()").extract()[0]
            next_page = int(current_page) + 1
            next_url = 'http://www.258.com' + href_next + 'p/%d/' % (next_page)

            self.log('succsed! next_url=%s, company_url=%s, next_page=%d' % (next_url, i['company_url'], next_page), level=log.INFO)
            meta = {'dont_redirect': True, 'href': href_next, 'dont_retry': True}
            yield scrapy.Request(url=next_url, meta=meta, callback=self.parse_two_page, dont_filter=True)
