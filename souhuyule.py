# -*- coding: utf-8 -*-
import json
import re
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
from urllib import urlencode
import pymongo
import requests
import time
import sys
from bs4 import BeautifulSoup
from requests import ConnectionError
from config import *
reload(sys)
sys.setdefaultencoding('utf-8')

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

def souhu_index(headers,page):
    data={
        'scene': 'CHANNEL',
        'sceneId': '19',
        'page': page,
        'size': '20',
        '_': '1500533123044'
    }
    params = urlencode(data)  ##利用urllib中的urlencode来构建data
    urls = 'http://v2.sohu.com/public-api/feed'
    url = urls + '?'+ params
    print url
    try:
        response = requests.get(url,headers)
        time.sleep(3)
        response.encoding = response.apparent_encoding  #默认编码改为UTF-8
        if response.status_code == 200:  #检测返回码是否200
            return response.text
        return None
    except ConnectionError:
        print 'Error occurred'
        return None

def souhu_page_index(text):
    try:
        data = json.loads(text)
        for i in data:
            ids =  i['id']
            authorIds = i['authorId']
            page_url ='http://www.sohu.com/a/'+ str(ids)+'_'+str(authorIds)
            print page_url
            if db[MONGO_TABLE].find_one({'pub_url':pub_url}):  #url去重，如果存在，提示爬过，否则else。
                print '这url爬过'
            else:
                yield pub_url
    except:
        pass

def souhu_content(page_url,headers):
    try:
        response = requests.get(page_url,headers)
        time.sleep(3)
        response.encoding = response.apparent_encoding  #默认编码改为UTF-8
        if response.status_code == 200:  #检测返回码是否200
            soup = BeautifulSoup(response.text, 'lxml')
            title = soup.find_all('h1')
            news_time = soup.select('#news-time')
            author = soup.select('#user-info > h4 > a')
            text = soup.select( '#article-container > div.left.main > div.text > article')
            for title,news_time,author,text in zip(title,news_time,author,text):
                return {
                    'title':title.get_text(),
                    'news_time':news_time.get_text(),
                    'author':author.get_text(),
                    'text':text.get_text(),
                    'page_url':page_url

                }
            # texts = re.sub('<img (.*?)>', '', response.text)
            # text1 = re.sub('<p>(.*?)<br>(.*?)</p>','',texts)
            # text2 = re.sub('<span>','',text1)
            # text3 = re.sub('</span>','',text2)
            # text = re.findall('<p>(.*?)</p>',text3)

        return None
    except ConnectionError:
        print 'Error occurred'
        return None

'''写入文档'''
def write_to_file(content):
    with open('souhuyele.txt', 'a', ) as f:
        f.write(json.dumps(content, ensure_ascii=False) + '\n')  #关闭写入的文件中编码
        f.close()


'''保存到mongodb'''
# def save_to_mongo(datail):
#     if db[MONGO_TABLE].insert(datail):
#         print('Successfully Saved to Mongo', datail)
#         return True
#     return False

def main(page):
    headers = {
        'User - Agent': 'Mozilla / 5.0(Windows NT 6.1;WOW64) AppleWebKit / 537.36(KHTML, likeGecko) Chrome / 59.0.3071.86 Safari / 537.36'
    }
    text = souhu_index(headers, page)
    page_url = souhu_page_index(text)
    for page_url in page_url:
        data = souhu_content(page_url, headers)
        write_to_file(data)
        # if data: save_to_mongo(data)

if __name__ == '__main__':
    start = time.clock()
    # pool = Pool()   # 默认线程数
    pool = ThreadPool(10)  #指定线程数
    group = ([page for page in range(GROUP_START, GROUP_END + 1)])
    pool.map(main,group)
    pool.close()
    pool.join()
    end = time.clock()
    print end - start


