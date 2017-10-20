# coding:utf-8

import json
import re
import logging
import requests
from datetime import datetime
from collections import namedtuple
from urlparse import urljoin
from w3lib.encoding import html_to_unicode
from bs4 import Tag, BeautifulSoup
from db import client
from db import DEBUG


class HotBase(object):
    db_m = client.get_default_database()
    headers = {
        "user-agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/50.0.2661.86 Safari/537.36")}
    timeout = 15
    c_json = False
    skip = None
    tag = "news"
    api = "/v2/hot/crawler/news"

    @staticmethod
    def extract_tag_attribute(root, name="text"):
        if root is None:
            return ""
        assert isinstance(root, (Tag, BeautifulSoup))
        if name == "text":
            return root.get_text().strip()
        else:
            value = root.get(name, "")
            if isinstance(value, (list, tuple)):
                return ",".join(value)
            else:
                return value.strip()

    @staticmethod
    def pre_url(url):
        return url

    @classmethod
    def download(cls, url, c_json=False, skip=None, headers=None):
        if headers is None:
            headers = cls.headers
        response = requests.get(url, headers=headers, timeout=(10, cls.timeout))
        content = response.content
        if skip:
            content = content[skip[0]:skip[1]]

        if c_json:
            return json.loads(content)
        else:
            _, content = html_to_unicode(
                content_type_header=response.headers.get("content-type"),
                html_body_str=content
            )
            return content.encode("utf-8")

    @classmethod
    def parse(cls, doc):
        pass

    @classmethod
    def after_parse(cls, result):
        # cls.show(result)
        cls.store_mongo(result)
        cls.upload(result)

    @classmethod
    def upload(cls, result):
        if DEBUG:
            url = urljoin("http://bdp.deeporiginalx.com", cls.api)
        else:
            # http://10.117.191.225:9001(内网地址)
            url = urljoin("http://bdp.deeporiginalx.com", cls.api)
        data = {cls.tag: [news["title"] for news in result]}
        try:
            req = requests.post(url=url, data=data)
            resp = json.loads(req.content.replace("'", '"'))
            if resp.get("code") != 2000:
                logging.warning(cls.__name__ + " [Upload] -> " + resp.get("data", "Success"))
            else:
                logging.info(cls.__name__ + " [Upload] -> " + resp.get("data", "Failed"))
        except Exception as e:
            logging.warning(e)
            logging.warning(cls.__name__ + " [Upload] -> Failed")

    @classmethod
    def store_mongo(cls, result):
        try:
            cls.db_m.hot_word_news.insert(result)
        except Exception as e:
            logging.warning(e)
            logging.warning(cls.__name__ + " [Store] -> Mongo Failed")
        else:
            logging.info(cls.__name__ + " [Store] -> Mongo Success")

    @staticmethod
    def show(result):
        for item in result:
            keys = item.keys()
            for key in keys:
                print"|%s->%s" % (key, item[key]),
            print "|"

    @classmethod
    def run(cls, url):
        print(cls.__name__ + " [Start]")
        logging.info(cls.__name__ + " [Start]")
        url = cls.pre_url(url)
        content = cls.download(url, c_json=cls.c_json,
                               skip=cls.skip,
                               headers=cls.headers)
        result = cls.parse(content)
        cls.after_parse(result)


class HotNews(HotBase):
    tag = "news"
    api = "/v2/hot/crawler/news"


class HotWord(HotBase):
    tag = "words"
    api = "/v2/hot/crawler/words"


class NetEaseHotNews(HotNews):
    @classmethod
    def parse(cls, doc):
        soup = BeautifulSoup(doc, "lxml", from_encoding="utf-8")
        tags = soup.select(selector="div.tabContents")[6].select(selector="a")
        result = []
        insert = datetime.utcnow()
        for tag in tags:
            title = cls.extract_tag_attribute(tag)
            if title:
                title = title.strip()
                result.append({"title": title,
                               "insert": insert,
                               "tag": cls.tag,
                               "origion": cls.__name__})
        return result


class IFengHotNews(HotNews):
    @classmethod
    def parse(cls, doc):
        soup = BeautifulSoup(doc, "lxml", from_encoding="utf-8")
        tags = soup.select(selector="div#c01 h3 > a")
        result = []
        insert = datetime.utcnow()
        for tag in tags:
            title = cls.extract_tag_attribute(tag)
            if title:
                result.append({"title": title,
                               "insert": insert,
                               "tag": cls.tag,
                               "origion": cls.__name__})
        return result


class SinaHotNews(HotNews):
    c_json = True
    skip = (10, -2)

    @staticmethod
    def pre_url(url):
        date = datetime.utcnow().strftime("%Y%m%d")
        return url.format(date=date)

    @classmethod
    def pre_regex(cls):
        regex = dict()
        regex["sports"] = re.compile(r"sports\.sina\.com\.cn")
        regex["oly"] = re.compile(r"2012\.sina\.com\.cn")
        regex["ent"] = re.compile(r"ent\.sina\.com\.cn")
        regex["finance"] = re.compile(r"finance\.sina\.com\.cn")
        regex["news"] = re.compile(r"news\.sina\.com\.cn")
        regex["mil"] = re.compile(r"mil\.news\.sina\.com\.cn")
        regex["society"] = re.compile(r"news\.sina\.com\.cn/s/")
        regex["bbs"] = re.compile(r"/bbs/")
        return regex

    @classmethod
    def parse(cls, doc):
        regex = cls.pre_regex()
        data = doc.get("data", {})
        result = list()
        insert = datetime.utcnow()
        top_count = 0
        sCnt = 0
        eCnt = 0
        fCnt = 0
        for item in data:
            if top_count > 9:
                break
            title = item.get("title", "")
            url = item.get("url", "")
            if not title:
                continue
            if regex["sports"].search(url) or regex["oly"].search(url):
                if sCnt > 3:
                    continue
                else:
                    sCnt += 1
            if regex["ent"].search(url):
                if eCnt > 1:
                    continue
                else:
                    eCnt += 1
            if regex["finance"].search(url):
                if fCnt > 5:
                    continue
                else:
                    fCnt += 1
            if not regex["sports"].search(url) \
                    and not regex["oly"].search(url) \
                    and not regex["ent"].search(url) \
                    and not regex["finance"].search(url) \
                    and not regex["news"].search(url) \
                    and not regex["mil"].search(url):
                continue
            if regex["society"].search(url) or regex["bbs"].search(url):
                continue
            top_count += 1

            title = title.strip()
            result.append({"title": title,
                           "insert": insert,
                           "tag": cls.tag,
                           "origion": cls.__name__})
        return result


class BaiduHotWord(HotWord):
    c_json = True

    @classmethod
    def parse(cls, doc):
        data = doc.get("data", {})
        result = list()
        insert = datetime.utcnow()
        for item in data:
            title = item.get("title")
            if title:
                title = title.replace("[br]", "").strip()
                result.append({"title": title,
                               "insert": insert,
                               "tag": cls.tag,
                               "origion": cls.__name__})
        return result


def main():
    Ori = namedtuple("Ori", ["desc", "handler", "url"])
    hot_news_task = [
        Ori(u"网易热点", NetEaseHotNews, "http://news.163.com/rank/"),
        Ori(u"凤凰热点", IFengHotNews, "http://news.ifeng.com/hotnews/"),
        Ori(u"新浪热点", SinaHotNews, ("http://top.news.sina.com.cn/ws/GetTopDataList.php?"
                                   "top_type=day&top_cat=www_www_all_suda_suda&top_time="
                                   "{date}&top_show_num=100&top_order=DESC"))
    ]
    hot_word_task = [
        Ori(u"百度热词", BaiduHotWord, "http://news.baidu.com/n?m=rddata&v=hot_word&type=0&date=")
    ]

    for task in hot_news_task:
        try:
            task.handler.run(task.url)
        except Exception as e:
            logging.warning(e)

    for task in hot_word_task:
        try:
            task.handler.run(task.url)
        except Exception as e:
            logging.warning(e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                        filename="hot_word_news.log",
                        filemode="a+")
    main()
