
# -*- coding: utf-8 -*-
##
# @file fetch_258Net.py
# @brief scrapy company info
# @author kangchch
# @version 1.0
# @date 2017-11-2

from scrapy.http import Request
import xml.etree.ElementTree
from scrapy.selector import Selector

import scrapy
import re
from pymongo import MongoClient
from copy import copy
import traceback
import pymongo
import cx_Oracle
from scrapy import log
from Fetch_258Net.items import Fetch258NetItem 
import time
import datetime
import sys
import logging
import random
import binascii
from scrapy.conf import settings
import json

reload(sys)
sys.setdefaultencoding('utf-8')


class Fetch258NetSpider(scrapy.Spider):
    name = "258net"

    def __init__(self, settings, *args, **kwargs):
        super(Fetch258NetSpider, self).__init__(*args, **kwargs)
        self.settings = settings
        mongo_info = settings.get('MONGO_INFO', {})

        try:
            self.mongo_db = pymongo.MongoClient(mongo_info['host'], mongo_info['port']).info_258
        except Exception, e:
            self.log('connect mongo 192.168.60.65:10010 failed! (%s)' % (str(e)), level=log.CRITICAL)
            raise scrapy.exceptions.CloseSpider('initialization mongo error (%s)' % (str(e)))

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def start_requests(self):

        try:
            records = self.mongo_db.company_url.find({'status': 0}, {'company_url': 1})
            for record in records:
                company_url = record['company_url']
                meta = {'dont_redirect': True, 'company_url': company_url, 'dont_retry': True}
                self.log('fetch new url=%s' % (company_url), level=log.INFO)
                yield scrapy.Request(url = company_url, meta = meta, callback = self.parse_introduce_page, dont_filter = True)
        except:
            self.log('start_request error! (%s)' % (str(traceback.format_exc())), level=log.INFO)

    # 解析公司介绍
    def parse_introduce_page(self, response):
        sel = Selector(response)

        ret_item = Fetch258NetItem()
        ret_item['update_item'] = {}
        i = ret_item['update_item']
        i['company_url'] = response.meta['company_url']

        if response.status != 200 or len(response.body) <= 0:
            if response.status == 302:
                self.log('fetch failed ! status = %d, url=%s' % (response.status, i['company_url']), level = log.WARNING)
                yield scrapy.Request(url = i['company_url'], meta = meta, callback = self.parse_introduce_page, dont_filter = True)

        ## introduce 公司简介
        introduce = sel.xpath("//div[@class='about_text mt10']")
        i['introduce'] = '' if not introduce else introduce[0].xpath('string(.)').extract()[0].strip().strip('\n')

        ## company_name 公司名称
        company_name = sel.xpath("//div[@class='companymessages ovh mt10 color33 ml30']/p[@class='fw14']/text()").extract()
        i['company_name'] = '' if not company_name else company_name[0].strip()
        print i['company_name']

        meta = {'dont_redirect': True, 'item': ret_item, 'dont_retry': True}
        yield scrapy.Request(url = i['company_url'], meta = meta, callback = self.parse_contact_page, dont_filter = True)

    #解析联系我们页面
    def parse_contact_page(self, response):
        sel = Selector(response)

        ret_item = response.meta['item']
        i = ret_item['update_item']

        ## 联系方式
        xpath_handles = sel.xpath("//div[@class='companymessages ovh mt10 color33 ml30']//text()").extract()
        xpath_handles = ''.join(xpath_handles)
        # print xpath_handles

        ## contactor 联系人
        contactor = re.findall(u"联系人：\n?\s*([^\s]+)", xpath_handles, re.S) if xpath_handles else ''
        i['contactor'] = '' if not contactor else contactor[0].strip()
        # print i['contactor']

        ## qq QQ 
        qq = re.findall(u"QQ:\n?\s*([^\n]+)(?=\))", xpath_handles, re.S) if xpath_handles else ''
        i['QQ'] = '' if not qq else qq[0].strip()
        # print i['QQ']

        ## duty 职位 department 部门
        duty = sel.xpath("//p[@class='iconfont icon-user']/span//text()").extract()
        i['duty'] = '' if not duty else duty[0].strip().replace('（', '')
        i['department'] = '' if not duty else duty[1].strip().replace('\n', '')
        # print i['duty']
        # print i['department']

        ## telephone 电话
        telephone = re.findall(u"电话：\n?\s*([^\s]+)", xpath_handles, re.S) if xpath_handles else ''
        i['telephone'] = '' if not telephone else telephone[0].strip()
        # print i['telephone']

        ## mobilephone 手机
        mobilephone = re.findall(u"手机：\n?\s*([^\s]+)", xpath_handles, re.S) if xpath_handles else ''
        i['mobilephone'] = '' if not mobilephone else mobilephone[0].strip()
        # print i['mobilephone']

        ## fax 传真
        fax = re.findall(u"传真：\n?\s*([^\s]+)", xpath_handles, re.S) if xpath_handles else ''
        i['fax'] = '' if not fax else fax[0].strip()
        # print i['fax']

        ## url 网址
        url = re.findall(u"官网：\n?\s*([^\s]+)", xpath_handles, re.S) if xpath_handles else ''
        i['url'] = '' if not url else url[0].strip()
        # print i['url']

        ## address 地址
        address = re.findall(u"地址：\n?\s*([^\s]+)", xpath_handles, re.S) if xpath_handles else ''
        i['address'] = '' if not address else address[0].strip()
        # print i['address']

        meta = {'dont_redirect': True, 'item': ret_item, 'dont_retry': True}
        yield scrapy.Request(url = i['company_url'] + '/about/', meta = meta, callback = self.parse_about_page, dont_filter = True)

    #解析认证信息
    def parse_about_page(self, response):
        sel = Selector(response)

        syb = u"商友宝VIP会员，值得信任"
        sm = u"企业营业执照已认证"

        ret_item = response.meta['item']
        i = ret_item['update_item']

        ## 商友宝会员 实名认证 是 1 or 否 0
        syb_sm = sel.xpath("//ul[@class='detail clearfix']/li/@onmousemove").extract()
        syb_sm = ''.join(syb_sm)

        i['syb_member'] = '1' if syb in syb_sm else ' '
        # print i['syb_member']
        if sm in syb_sm:
            i['sm'] = '1'
            # print i['sm']

            ## 成立时间 found_time
            found_time = sel.xpath("//ul[@class='fl w6 infor_list']/li[2]/text()").extract()
            i['found_time'] = '' if not found_time else found_time[0].strip()
            # print i['found_time']

            ## 注册资本 registr_capital
            registr_capital = sel.xpath("//ul[@class='fl w6 infor_list']/li[3]/text()").extract()
            i['registr_capital'] = '' if not registr_capital else registr_capital[0].strip()
            # print i['registr_capital']

            ## 经营范围 operate_range
            operate_range = sel.xpath("//ul[@class='fl w6 infor_list']/li[4]/p[@class='overflow']/text()").extract()
            i['operate_range'] = '' if not operate_range else operate_range[0].strip()
            # print i['operate_range']
        else:
            i['sm'] = ' '

        ## mainpro 主营产品
        mainpro = sel.xpath("//li[@class='mt10']/div[@class='info_data ']/table/tbody/tr[4]/td[@class='data_value'][2]/text()").extract()
        i['mainpro'] = '' if not mainpro else mainpro[0].strip()
        # print i['mainpro']

        ## 注册号 registr
        registr = sel.xpath("//li[@class='mt10']//tr[1]/td[@class='data_value'][2]/text()").extract()
        i['registr'] = '' if not registr else registr[0].strip()
        # print i['registr']

        # industry 主营行业
        industry = sel.xpath("//li[@class='mt10']//tr[4]/td[@class='data_value'][1]/text()").extract()
        i['industry'] = '' if not industry else industry[0].strip()
        # print i['industry']

        # 员工人数 staffs
        staffs = sel.xpath("//li[@class='mt10']//tr[2]/td[@class='data_value'][2]/text()").extract()
        i['staffs'] = '' if not staffs else staffs[0].strip()
        # print i['staffs']

        self.log(' . company_name:%s, url=%s, contactor:%s, QQ:%s, tp:%s, mp:%s, add:%s, syb:%s, sm:%s'
                % (i['company_name'], i['company_url'], i['contactor'], i['QQ'], i['telephone'], i['mobilephone'], i['address'],
                    i['syb_member'], i['sm']), level=log.INFO)
        yield ret_item

