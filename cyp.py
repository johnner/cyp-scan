# !/usr/bin/env python
# coding: utf-8

from __future__ import print_function
import functools
from twisted.internet import reactor, defer
from twisted.web.client import getPage
from BeautifulSoup import BeautifulSoup
import re
import argparse
import logging
logging.basicConfig(level=logging.INFO)


def pagination(fn):
    @functools.wraps(fn)
    def func(*args, **kwargs):
        offset = args[0].offset
        result = fn(*args, page=func.count)
        func.count += offset
        return result
    func.count = 0
    return func


class CypSearch():

    def __init__(self, offset=20, max_page=40, host=None, keywords=None):
        if keywords:
            self.keywords = keywords
        else:
            raise ValueError('keywords must be included')
        if host:
            self.host = host
        else:
            raise ValueError('host must be specified')

        self.offset = offset
        self.max_page = max_page
        self.found_jobs = []

    def start(self):
        lst = []
        for i in range(0, self.max_page + self.offset, self.offset):
            page = self.next_page(page=0)
            lst.append(self.fetch_page(page))

        dl = defer.DeferredList(lst)
        dl.addBoth(self.finish)

    @pagination
    def next_page(self, page=0):
        return '{}my_jobs/jobs_job_list.html?cv_search=0,,,all,{},{}'.format(self.host,
                                                                             self.offset,
                                                                             page)

    def extract_job_links(self, html):
        """ get job links on the page """
        soup = BeautifulSoup(html)
        soup.prettify()
        links = []
        tds = soup.findAll('td', {'class': 'itd_lb'})
        for td in tds:
            anchor = td.find('a')
            if anchor and anchor['href']:
                links.append('%s%s' % (self.host, str(anchor['href'])))
        return links


    def scan_keyword(self, html, link, page):
        """ scan job details for keywords"""
        soup = BeautifulSoup(html)
        soup.prettify()
        found = False
        table = soup.find('table', {'class': 'FeturedAdTd'}, )
        t = table.find('table')
        for word in self.keywords:
            td = t.findAll('td', text=re.compile(word, re.IGNORECASE))
            if td:
                found = True
        if found:
            print ('Keyword found! Link: %s, Page: %s' % (link, page))
            self.found_jobs.append((link, page))


    @defer.inlineCallbacks
    def fetch_page(self, url):
        html = yield getPage(url)
        jobs = self.extract_job_links(html)
        for job in jobs:
            print('========== fetch job details ==========')
            jhtml = yield getPage(job)
            self.scan_keyword(jhtml, job, url)
        defer.returnValue(jobs)


    def finish(self, res):
        print('======== finish =========')
        reactor.stop()
        print(self.found_jobs)


def main(keywords, output):
    search = CypSearch(host='http://www.cyprusjobs.com/',
                       keywords=keywords,
                       offset=20, max_page=20)
    search.start()
    reactor.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl for cyprus jobs '
                                                 'example: python cyp.py python javascript '
                                                 'define output file: python cyp.py python javascript -o result.xls')
    parser.add_argument('keyword', nargs='+', help='one or more keywords to search')
    parser.add_argument('-o', type=str, dest='output', help='output result file name')
    args = parser.parse_args()
    logging.info(args.keyword)
    logging.info(args.output)

    main(args.keyword, args.output)
