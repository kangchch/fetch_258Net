# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy import log
import pymongo
import datetime
from scrapy.conf import settings


class Fetch258NetPipeline(object):

    def __init__(self, settings):
        self.settings = settings

    @classmethod
    def from_crawler(cls, crawler):
        return cls(settings=crawler.settings)

    def process_item(self, item, spider):
        return
        i = item['update_item']

        try:
            spider.mongo_db.content_tbl.insert_one(i)
            spider.mongo_db.company_url.update_one({'url': i['company_url']}, {'$set': {'status': 1}})
        except pymongo.errors.DuplicateKeyError:
            spider.log('insert url is existed! url=%s' % (i['company_url']), level=log.WARNING)
            pass
        except Exception, e:
            spider.log('insert mongo failed! url=%s e=%s' % (i['company_url'], str(e)), level=log.ERROR)
