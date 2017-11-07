# -*-coding:utf-8-*-

import random
import Queue
import time
import re
import subprocess
import requests
from pymongo import MongoClient
from requests_toolbelt.adapters.source import SourceAddressAdapter
import logging
import base64
from scrapy.contrib.downloadermiddleware.useragent import UserAgentMiddleware
from scrapy.http import TextResponse

TEST_URL = {'URL': 'http://www.baidu.com/img/baidu_jgylogo3.gif', 'SIZE': 705}


class AntiBanMiddleware(UserAgentMiddleware):
    def __init__(self, settings):
        super(AntiBanMiddleware, self).__init__()
        self.logger = logging.getLogger('Anti Ban')
        self.spider_info = settings.get('SPIDER_INFO', {})
        self.init_mongo_db()

        # init proxy and ip queue
        self.proxy_list = []
        self.proxy_queue = None
        self.ip_list = []
        self.ip_queue = None

        if 'TJ_PROXY' in self.spider_info and self.spider_info['TJ_PROXY']:
            self.proxy_queue = Queue.Queue()
            for proxy in self.mongo_db.tj_proxy.find({}):
                self.proxy_list.append(proxy)
            random.shuffle(self.proxy_list)
            for proxy in self.proxy_list:
                self.proxy_queue.put(proxy)
            self.logger.info('initialize tj proxy size=%d', self.proxy_queue.qsize())
            if self.proxy_queue.qsize() == 0:
                self.proxy_queue = None
        elif 'MULTI_IP' in self.spider_info:
            self.ip_queue = Queue.Queue()
            muti_ip = self.spider_info['MULTI_IP']
            if muti_ip['MONGO']:
                for item in self.mongo_db.tj_ips.find({'ID': self.spider_info['ID']}):
                    self.ip_list.append(item['IP'])
                self.logger.info('initialize mongo ip size=%d ips=%s', len(self.ip_list), str(self.ip_list))
            else:
                self.ip_list = self.get_ip_list_from_locale()
                self.logger.info('initialize locale ip size=%d ips=%s', len(self.ip_list), str(self.ip_list))

            random.shuffle(self.ip_list)
            if muti_ip.get('NEED_AUTH', False):
                self.ip_list = self.get_usefulness_ip(self.ip_list)
            for ip in self.ip_list:
                self.ip_queue.put(ip)
            self.logger.info('initialize usefulness ip size=%d ips=%s', len(self.ip_list), str(self.ip_list))

    def __del__(self):
        try:
            if self.mongo_db:
                self.mongo_db.logout()
        except Exception, e:
            pass

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def init_mongo_db(self):
        while True:
            try:
                self.mongo_db = MongoClient('192.168.60.65', 10010).anti_ban
                break
            except Exception, e:
                self.logger.error('initialize mongo db error! (%s)', str(e))
                time.sleep(5)

    def get_ip_list_from_locale(self):
        call_handle = subprocess.Popen('ip addr',  shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        ip_buf = call_handle.stdout.readlines()
        ip_list = re.findall(r'(?<=inet )\d+\.\d+\.\d+\.\d+(?=/)', str(ip_buf))
        ip_pub_list = []
        for ip in ip_list:
            if re.match(r'^1(((0|27)(.(([1-9]?|1[0-9])[0-9]|2([0-4][0-9]|5[0-5])))|(72.(1[6-9]|2[0-9]|3[01])|92.168))(.(([1-9]?|1[0-9])[0-9]|2([0-4][0-9]|5[0-5]))){2})$', ip):
                continue
            ip_pub_list.append(ip)
        return ip_pub_list

    def get_usefulness_ip(self, ip_list):
        usefulness_ip_list = []
        for ip in ip_list:
            try:
                s = requests.Session()
                s.mount('http://', SourceAddressAdapter((ip, 0)))
                s.mount('https://', SourceAddressAdapter((ip, 0)))
                r = s.get(TEST_URL['URL'])
                if r.status_code == 200 and len(r.text) == TEST_URL['SIZE']:
                    usefulness_ip_list.append(ip)
            except Exception, e:
                print str(e)
                continue
        return usefulness_ip_list

    def process_request(self, request, spider):
        if self.proxy_queue:
            proxy = self.proxy_queue.get()
            request.meta['proxy_src'] = proxy
            proxy_address = proxy['ip']
            proxy_user_pass = proxy['user_pass']

            request.meta['proxy'] = proxy_address
            if proxy_user_pass:
                basic_auth = 'Basic ' + base64.encodestring(proxy_user_pass)
                request.headers['Proxy-Authorization'] = basic_auth.strip()

            self.proxy_queue.put(proxy)
            self.logger.debug('process_request set proxy %s qsize=%d before %s',
                              str(proxy), self.proxy_queue.qsize(), request.url)
        elif self.ip_queue:
            ip = self.ip_queue.get()
            request.meta['bindaddress'] = (ip, 0)
            self.ip_queue.put(ip)
            self.logger.debug('process_request set ip=%s qsize=%d before %s',
                              ip, self.ip_queue.qsize(), request.url)

    def process_response(self, request, response, spider):
        if 'bindaddress' in request.meta:
            self.logger.debug('process_response ip=%s qsize=%d after %s',
                              request.meta['bindaddress'][0], self.ip_queue.qsize(), request.url)
        elif 'proxy_src' in request.meta:
            self.logger.debug('process_response proxy %s qsize=%d after%s',
                              request.meta['proxy_src'], self.proxy_queue.qsize(), request.url)
        else:
            self.logger.debug('process_response lost url %s', request.url)
        return response

    def process_exception(self, request, exception, spider):
        self.logger.warning('process_exception ip=%s proxy=%s errmsg=%s',
                            request.meta['bindaddress'][0] if 'bindaddress' in request.meta else '127.0.0.1',
                            request.meta.get('proxy_src', ''), str(exception))
        request.meta['errmsg'] = str(exception)
        return TextResponse(
            url=request.url,
            status=110,
            request=request)
