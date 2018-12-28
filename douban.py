#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2018-12-25 10:22:35
# Project: douban

from pyspider.libs.base_handler import *
import re
import pymongo


class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
        }
    }
    client = pymongo.MongoClient('localhost')
    db = client['douban']
    collection = db['Top250']

    @every(minutes=24 * 60)
    def on_start(self):
        url = 'https://movie.douban.com/top250?start='
        for page in range(10):
            self.crawl(url + str(page * 25), callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('div.info > div.hd > a').items():
            self.crawl(each.attr.href, callback=self.detail_page)
            # self.crawl(next, callback=self.index.page)

    @config(priority=2)
    def detail_page(self, response):
        return {
            "No": response.doc('.top250-no').text().lstrip('No.'),
            "title": response.doc('title').text(),
            "rating": response.doc('strong[property="v:average"]').text(),
            "attrs": response.doc('#info > span:nth-child(1) > span.attrs').text(),
            "actor": response.doc('#info > span.actor > span.attrs').text(),
            "releaseDate": response.doc('span[property="v:initialReleaseDate"]').text(),
            "runtime": response.doc('span[property="v:runtime"]').text(),
            "genre": response.doc('span[property="v:genre"]').text(),
            "corner": re.search('制片国家/地区: (.*?)\n', response.doc('#info').text(), re.S).group(1),
            "report": response.doc('#link-report').text(),
            "url": response.url,
        }

    def on_result(self, result):
        if result:
            self.save_to_mongo(result)

    def save_to_mongo(self, result):
        if self.collection.insert(result):
            print(result)
