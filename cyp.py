# !/usr/bin/env python
# coding: utf-8

import functools
from twisted.internet import reactor, defer
from twisted.web.client import getPage
from bs4 import BeautifulSoup
from openpyxl import Workbook
from openpyxl.styles import Font, colors
import re
import argparse
import logging
logging.basicConfig(level=logging.DEBUG)


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

    def __init__(self, offset=20, max_page=40,
                 host=None, keywords=None, output=None):
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
        if not output:
            raise ValueError('output file must be defined')
        else:
            self.output = output

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
        soup = BeautifulSoup(html, "html.parser")
        soup.prettify()
        jobs = []
        tds = soup.findAll('td', {'class': 'itd_lb'})
        for td in tds:
            anchor = td.find('a')
            if anchor and anchor['href']:
                date = td.find('span').string
                job = {
                    'title': anchor.string,
                    'link': '%s%s' % (self.host, str(anchor['href'])),
                    'date': date,
                    'keywords': []
                }
                jobs.append(job)
        return jobs

    def scan_keyword(self, html, job, page):
        """ scan job details for keywords"""
        soup = BeautifulSoup(html, "html.parser")
        soup.prettify()
        found = False
        words_found = []
        table = soup.find('table', {'class': 'FeturedAdTd'}, )
        t = table.find('table')
        for word in self.keywords:
            td = t.findAll('td', text=re.compile(word, re.IGNORECASE))
            if td:
                found = True
                job['keywords'].append(word)
        if found:
            logging.info('Keyword found! Link: %s, Page: %s' % (job['link'], page))
            job['page'] = page
            self.found_jobs.append(job)


    @defer.inlineCallbacks
    def fetch_page(self, url):
        html = yield getPage(url.encode('utf8'))
        jobs = self.extract_job_links(html)
        for idx, job in enumerate(jobs, 1):
            logging.info('fetching job details...')
            jhtml = yield getPage(job['link'].encode('utf8'))
            self.scan_keyword(jhtml, job, url)
        defer.returnValue(jobs)

    def finish(self, res):
        reactor.stop()
        if not self.found_jobs:
            logging.info('Unfortunately there is no job with keywords: {}'.format(self.keywords))
        else:
            self.save_jobs()
            logging.info('Found jobs: {}. Saved to file {}'.format(len(self.found_jobs), self.output))

    def save_jobs(self):
        """ save found jobs to file to excel file """
        wb = Workbook()
        ws = wb.active
        t_url = ws.cell(row=1, column=1)
        t_url.value = 'Link'
        t_key = ws.cell(row=1, column=2)
        t_key.value = 'Keyword'

        for idx, job in enumerate(self.found_jobs, 2):
            ft = Font(color=colors.BLUE)
            jc = ws.cell(row=idx, column=1)
            jc.value = job['title']
            jc.hyperlink = job['link']
            jc.font = ft

            kw = ws.cell(row=idx, column=2)
            kw.value = ', '.join(job['keywords'])

            dt = ws.cell(row=idx, column=3)
            dt.value = job['date']

        logging.info('saving to file %s' % self.output)
        wb.save(self.output)


def main(keywords, output, paging=10, max_page=10):
    if not output:
        output = 'jobs.xlsx'
    search = CypSearch(host='http://www.cyprusjobs.com/',
                       keywords=keywords,
                       output=output,
                       offset=paging,
                       max_page=max_page)
    search.start()
    reactor.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Crawl for cyprus jobs '
                                                 'example: python cyp.py python javascript '
                                                 'define output file: python cyp.py python javascript -o result.xls '
                                                 'to define paging: python cyp.py python -p 10 -m 50')
    parser.add_argument('keyword', nargs='+', help='one or more keywords to search')
    parser.add_argument('-o', type=str, dest='output', help='output result file name')
    # parser.add_argument('-p', type=int, dest='paging', help='how many urls to get on page')
    # parser.add_argument('-m', type=int, dest='maxpage', help='maximum jobs to scan')
    args = parser.parse_args()

    main(args.keyword, args.output)