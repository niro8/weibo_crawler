#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas
import time
import datetime
import re
import random
import logging
from selenium import webdriver

driver = webdriver.Chrome('D:/chromedriver/chromedriver.exe')
df = pandas.DataFrame()

def LoginWeibo(username, password):
    try:
        driver.get('http://www.weibo.com/login.php')
        time.sleep(5)
        driver.find_element_by_xpath('//input[@id="loginname"]').clear()
        driver.find_element_by_xpath('//input[@id="loginname"]').send_keys(username)
        time.sleep(3)
        driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys(password)
        driver.find_element_by_xpath('//*[@id="login_form_savestate"]').click()
        time.sleep(1)
        driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
    except Exception as e:
        logger.error('Something wrong with', exc_info=True)

def GetSearchContent(key):
    driver.get("http://s.weibo.com/")
    logger.info('搜索热点主题：%s' % key)
    driver.find_element_by_xpath("//input[@class='searchInp_form']").send_keys(key)
    time.sleep(3)
    driver.find_element_by_xpath('//*[@id="pl_searchHead"]/div/div/div/div[1]/a').click()
    current_url = driver.current_url.split('&')[0]
    start_date = datetime.datetime(2018,7,4,0)
    end_date = datetime.datetime(2018,7,4,23)
    delta_date = datetime.timedelta(hours=23)
    start_stamp = start_date
    end_stamp = start_date + delta_date
    while end_stamp <= end_date:
        url = current_url + '&typeall=1&suball=1&timescope=custom:' + str(start_stamp.strftime("%Y-%m-%d-%H")) + ':' + str(end_stamp.strftime("%Y-%m-%d-%H")) + '&Refer=g'
        time.sleep(random.randint(5,10))
        driver.get(url)
        handlePage()
        start_stamp = end_stamp + datetime.timedelta(hours=1)
        end_stamp = start_stamp + delta_date

def handlePage():
    page = 1
    while True:
        time.sleep(random.randint(5,10))
        if checkContent():
            logger.info('页数:%s' % page)
            getContent()
            page += 1
            if checkNext():
                driver.find_element_by_xpath("//a[@class='page next S_txt1 S_line1']").click()
            else:
                logger.info("no Next")
                break
        else:
            logger.info("no Content")
            break

def checkContent():
    try:
        driver.find_element_by_xpath("//div[@class='pl_noresult']")
        flag = False
    except:
        flag = True
    return flag

def checkNext():
    try:
        driver.find_element_by_xpath("//a[@class='page next S_txt1 S_line1']")
        flag = True
    except:
        flag = False
    return flag

def get_datetime(s):
    try:
        m, d, H, M = re.findall(r'\d+',s)
        date = datetime.datetime(2018, int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')
    except:
        date = s
    return date

def checkContent():
    try:
        driver.find_element_by_xpath("//div[@class='pl_noresult']")
        flag = False
    except:
        flag = True
    return flag

def checkNext():
    try:
        driver.find_element_by_xpath("//a[@class='page next S_txt1 S_line1']")
        flag = True
    except:
        flag = False
    return flag

def get_datetime(s):
    try:
        m, d, H, M = re.findall(r'\d+',s)
        date = datetime.datetime(2018, int(m), int(d), int(H), int(M)).strftime('%Y-%m-%d %H:%M')
    except:
        date = s
    return date

def getContent():
    nodes = driver.find_elements_by_xpath("//div[@class='WB_cardwrap S_bg2 clearfix']")
    if len(nodes) == 0:
        time.sleep(random.randint(5,10))
        driver.get(driver.current_url)
        getContent()
        return
    results = []
    global df
    logger.info('微博数量：%s' % len(nodes))
    for i in range(len(nodes)):
        blog = {}
        try:
            BZNC = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").text
        except:
            BZNC = ''
        blog['博主昵称'] = BZNC
        try:
            BZZY = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/a[@class='W_texta W_fb']").get_attribute("href")
        except:
            BZZY = ''
        blog['博主主页'] = BZZY
        try:
            WBNR = nodes[i].find_element_by_xpath(".//div[@class='feed_content wbcon']/p[@class='comment_txt']").text
        except:
            WBNR = ''
        blog['微博内容'] = WBNR
        try:
            FBSJ = nodes[i].find_element_by_xpath(".//div[comment() and @class='feed_from W_textb']/a[@class='W_textb']").text
        except:
            FBSJ = ''
        blog['发布时间'] = get_datetime(FBSJ)
        try:
            WBDZ = nodes[i].find_element_by_xpath(".//div[comment() and @class='feed_from W_textb']/a[@class='W_textb']").get_attribute("href")
        except:
            WBDZ = ''
        blog['微博地址'] = WBDZ
        try:
            WBLY = nodes[i].find_element_by_xpath(".//div[comment() and @class='feed_from W_textb']/a[@rel]").text
        except:
            WBLY = ''
        blog['微博来源'] = WBLY
        try:
            ZF_TEXT = nodes[i].find_element_by_xpath(".//a[@action-type='feed_list_forward']//em").text
            if ZF_TEXT == '':
                ZF = 0
            else:
                ZF = int(ZF_TEXT)
        except:
            ZF = 0
        blog['转发'] = ZF
        try:
            PL_TEXT = nodes[i].find_element_by_xpath(".//div[@class='feed_action clearfix']//a[@action-type='feed_list_comment']//em").text
            if PL_TEXT == '':
                PL = 0
            else:
                PL = int(PL_TEXT)
        except:
            PL = 0
        blog['评论'] = PL
        try:
            ZAN_TEXT = nodes[i].find_element_by_xpath(".//div[@class='feed_action clearfix']//a[@action-type='feed_list_like']//em").text
            if ZAN_TEXT == '':
                ZAN = 0
            else:
                ZAN = int(ZAN_TEXT)
        except:
            ZAN = 0
        blog['赞'] = ZAN

        results.append(blog)
    df = df.append(results)
    df.to_excel('C:/Users/Administrator/Desktop/results.xlsx',index=0)
    logger.info('已导出微博条数：%s' % len(df))
    # df.to_csv('C:/Users/Administrator/Desktop/results.csv',index=0,encoding='utf_8_sig')

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
    username = '*********'
    password = '*********'
    LoginWeibo(username, password)
    key = 'p2p'
    GetSearchContent(key)
    time.sleep(10)
    driver.quit()
    logger.info('*'*30+'E N D'+'*'*30)
