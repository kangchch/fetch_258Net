# -*- coding: utf-8 -*-

import requests
import pymongo
import datetime
from lxml import etree
import pdb
import os
import logging
import time
import random

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

# sys.path.append('/tools/python_common')
# from common_func import logInit

start_url = 'http://shanen.shop.258.com'
# 获取url对应的网页源码
def get_source(urls):
    try:
        headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cache-Control': 'max-age=0',
                'Connection': 'keep-alive',
                'Host': 'shanen.shop.258.com',
                'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(urls, headers=headers)
    except requests.RequestException as e:
        print e
        logging.error('response.status_code = %d!' % (response.status_code))
    else:
        # sleep_time = random.randint(1, 3)
        # time.sleep(sleep_time)
        return response.text

if __name__ == '__main__':

    # DIR_PATH = os.path.split(os.path.realpath(__file__))[0]
    # LOG_FILE = DIR_PATH + '/logs/' + __file__.replace('.py', '.log')
    # logInit(logging.INFO, LOG_FILE, 0, True)

    # for url in urls:
    response= get_source(start_url)
    if not response:
        logging.error('fetch failed! failed url=%s ' %  (url))
    else:
        selector = etree.HTML(response)
<<<<<<< HEAD
        keywords = selector.xpath("//div[@class='about_text mt10']/text()")
=======
        keywords = selector.xpath("//div[@class='about_text mt10']//text()")
>>>>>>> b3bfb6bfe71970bbb792235f51ce63daae3292a5
        keywords = keywords if keywords else []
        print keywords
        # logging.info('url=%s, ' % (url))
