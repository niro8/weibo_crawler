#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import rsa
import binascii
import re
import os
import random
import requests
import urllib
import pandas
import datetime
import time
import logging
from bs4 import BeautifulSoup

# 登录类
class LoginSina(object):

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    def get_su(self):
        username_base64 = base64.b64encode(urllib.parse.quote_plus(self.username).encode("utf-8"))
        return username_base64.decode("utf-8")

    def get_server_data(self, su):
        pre_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su={}&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)&_="
        pre_data_res = requests.get(pre_url.format(su), headers=self.headers)
        sever_data = eval(pre_data_res.content.decode("utf-8").replace("sinaSSOController.preloginCallBack", ''))
        return sever_data

    def get_password(self, password, servertime, nonce, pubkey):
        rsaPublickey = int(pubkey, 16)
        key = rsa.PublicKey(rsaPublickey, 65537)
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
        message = message.encode("utf-8")
        passwd = rsa.encrypt(message, key)
        passwd = binascii.b2a_hex(passwd)
        return passwd

    def get_cookies(self):
        su = self.get_su()
        d = self.get_server_data(su)
        postdata = {
            'entry':'sso',
            'gateway':'1',
            'from':'null',
            'savestate':'0',
            'useticket':'0',
            'pagerefer':"http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
            'vsnf':'1',
            'su':su,
            'service':'sso',
            'servertime':d['servertime'],
            'nonce':d['nonce'],
            'pwencode':'rsa2',
            'rsakv':'1330428213',
            'sp':self.get_password(self.password, d['servertime'], d['nonce'], d['pubkey']),
            'sr':'1366*768',
            'encoding':'UTF-8',
            'cdult':'3',
            'domain':'sina.com.cn',
            'prelt':'27',
            'returntype':'TEXT'
        }
        login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
        res = requests.post(login_url, data=postdata, headers=self.headers)
        ticket = eval(res.text)['crossDomainUrlList'][0][eval(res.text)['crossDomainUrlList'][0].find('ticket'):]
        new_url='http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack&{}&retcode=0'.format(ticket)
        return requests.get(new_url).cookies

class DownloadWeibo(object):

    def __init__(self, keywords, startTime, endTime, saveDir, cookies, df=pandas.DataFrame()):
        self.keywords = keywords
        self.startTime = startTime
        self.endTime = endTime
        self.saveDir = saveDir
        self.cookies = cookies
        self.df = df

    def get_keyword(self):
        return urllib.parse.quote(urllib.parse.quote(self.keywords))

    # 拼接链接
    def get_url(self):
        search_str = self.get_keyword()+'?q='+urllib.parse.quote(self.keywords)
        url = 'http://s.weibo.com/weibo/'+search_str+'&typeall=1&suball=1&timescope=custom:'+self.startTime+':'+self.endTime+'&page='
        return url

    # 获取界面
    def get_html(self, pageNum):
        url = self.get_url()+str(pageNum)
        res = requests.get(url, cookies=self.cookies)
        return res.text.replace('\u200b','')

    # 处理时间
    def get_datetime(self, s):
        try:
            today = datetime.datetime.today()
            if '今天' in s:
                H, M = re.findall(r'\d+',s)
                date = datetime.datetime(today.year, today.month, today.day, int(H), int(M)).strftime('%Y-%m-%d %H:%M')
            elif '年' in s:
                y, m, d, H, M = re.findall(r'\d+',s)
                date = datetime.datetime(int(y), int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')                       
            else:    
                m, d, H, M = re.findall(r'\d+',s)
                date = datetime.datetime(today.year, int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')
        except:
            date = s
        return date

    # 获取内容
    def get_results(self, html):
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        if len(soup.select('.card-no-result'))>0:
            results = None
            logger.info('No Results')
        else:
            logger.info('微博数量：%s' % len(soup.select('div[action-type="feed_list_item"]')))
            for i in soup.select('div[action-type="feed_list_item"]'):
                blog = {}
                blog['博主昵称'] = i.select('.name')[0].get('nick-name')
                blog['博主主页'] = 'https:'+i.select('.name')[0].get('href')
                if len(i.select('.comment_txt'))>1:
                    # blog['微博内容'] = i.select('.comment_txt')[0].get_text().strip()+'\n转发：'+i.select('.comment_txt')[1].get_text().strip()
                    blog['微博内容'] = i.select('p.txt')[0].get_text().strip()
                blog['发布时间'] = self.get_datetime(i.select('div[class="content"] p[class="from"] a')[0].get_text())
                blog['微博地址'] = 'https:'+i.select('div[class="content"] p[class="from"] a')[0].get('href')
                try:
                    blog['微博来源'] = i.select('div[class="content"] p[class="from"] a')[1].get_text()
                except:
                    blog['微博来源'] = ''
                try:
                    sd = i.select('.card-act ul li')
                except Exception:
                    logger.info('sd not found...')
                    logger.error('Something wrong with', exc_info=True)
                try:
                    blog['转发'] = 0 if sd[1].text.replace('转发','').strip()=='' else int(sd[1].text.replace('转发','').strip())
                except:
                    blog['转发'] = 0
                try:
                    blog['评论'] = 0 if sd[2].text.replace('评论','').strip()=='' else int(sd[2].text.replace('评论','').strip())
                except:
                    blog['评论'] = 0
                try:
                    blog['赞'] = 0 if sd[3].select('em')[0].get_text()=='' else int(sd[3].select('em')[0].get_text())
                except:
                    blog['赞'] = 0
                results.append(blog)
        return results

    def get_totalpage(self):
        soup = BeautifulSoup(self.get_html(1), 'html.parser')
        # self.count = int(re.search(r'\d+',soup.select('.result')[0].text).group(0))
        if len(soup.select('.card-no-result'))>0:
            totalpage = 0
        else:
            totalpage = len(soup.select('.s-scroll li'))
        return totalpage

    def get_contents(self):
        totalpage = self.get_totalpage()
        if totalpage==0:
            logger.info('No Results')
        else:
            logger.info('共有%s页' % totalpage)
            for i in range(1, totalpage+1):
                try:
                    logger.info('第%s页' % i)
                    time.sleep(random.randint(5,10))
                    html_page = self.get_html(i)
                    results = self.get_results(html_page)
                    if results != None:
                        self.df = self.df.append(results)
                except:
                    logger.error('Something wrong with', exc_info=True)
                    time.sleep(120)
                    logger.info('第%s页' % i)
                    time.sleep(random.randint(5,10))
                    html_page = self.get_html(i)
                    results = self.get_results(html_page)
                    self.df = self.df.append(results)
        self.df_count = len(self.df)

# 输入关键词、日期，分天爬取
def main():
    username = '********' # 输入用户名
    password = '********' # 输入密码
    ls = LoginSina(username, password)
    c = ls.get_cookies()
    keywords = input('请输入关键词：')
    startTime = input('输入开始时间(Format:YYYY-mm-dd):')
    endTime = input('输入结束时间(Format:YYYY-mm-dd):')
    saveDir = os.path.abspath('.')+'\\'
    start_date = datetime.datetime.strptime(startTime, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(endTime, '%Y-%m-%d')+datetime.timedelta(days=1)
    start_temp = start_date
    end_temp = start_temp+datetime.timedelta(hours=1)
    r = pandas.DataFrame()
    while end_temp<=end_date:
        logger.info('查询时间为：%s ~ %s' % (start_temp.strftime('%Y-%m-%d-%H'),end_temp.strftime('%Y-%m-%d-%H')))
        dw = DownloadWeibo(keywords, start_temp.strftime('%Y-%m-%d-%H'), end_temp.strftime('%Y-%m-%d-%H'), saveDir, c, r)
        dw.get_contents()
        # logger.info('查询结果条数：%d' % dw.count)
        logger.info('取得结果条数：%d' % dw.df_count)
        r = dw.df
        start_temp = end_temp
        end_temp = start_temp+datetime.timedelta(hours=1)
    excel_path = saveDir+keywords+startTime.replace('-','')[4:8]+'-'+endTime.replace('-','')[4:8]+'.xlsx'
    try:
        r.to_excel(excel_path, index=0)
        logger.info('搜索关键字：%s' % keywords)
        logger.info('开始时间：%s' % startTime)
        logger.info('结束时间：%s' % endTime)
        logger.info('共导出%s条微博' % len(r))
        logger.info('导出地址：%s' % excel_path)
    except:
        logger.error('Something wrong with', exc_info=True)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('export_record.log')
    handler.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(console)
    logger.info('*'*30+'START'+'*'*30)
    main()
    logger.info('*'*30+'E N D'+'*'*30)
