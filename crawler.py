#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:

import spynner
import pyquery
import pybloom
import Queue
import tempfile
import shutil

class Crawler(object):
    ''' A single-process crawler, that uses Webkit and can execute Javascript.
        It selects which links to follow with a user-provided filter.
        It won't revisit the same page twice.


    # How to use:

    crawler = Crawler(gui=True,
                      is_link_interesting=lambda url, text: 'download' in url)
    crawler.crawl('http://firefox.com')
    crawler.close()
    '''


    def __init__(self, is_link_interesting, gui=False, timeout=5, **browser_kwargs):
        '''
        is_link_interesting(a_href, a_text): a function that looks at a link
                                             text and target url, and returns
                                             True if the crawler should follow
                                             the link
        gui: True if you want to see the crawler
        timeout: How much to wait for the url to be loaded and JS to execute
        browser_kwargs: these are passed directly to the spynner module
        '''
        self.timeout = timeout
        self.is_link_interesting = is_link_interesting
        # Setup the browser
        self.download_dir_tmp = tempfile.mkdtemp(prefix='crawler_')
        browser_config = {'debug_level': spynner.WARNING,
                          'download_directory': self.download_dir_tmp,
                          'user_agent':'Mozilla/5.0 (compatible; MSIE 9.0;'
                                       ' Windows NT 6.1; Trident/5.0)'}
        browser_config.update(browser_kwargs)
        self.browser = spynner.browser.Browser(**browser_kwargs)
        self.browser.set_html_parser(pyquery.PyQuery)
        if gui:
            self.browser.create_webview()
            self.browser.show()
        # Create the bloom filter
        self.bloom_filter = pybloom.ScalableBloomFilter()
        # Create the queue
        self.queue = Queue.Queue()

    def _visit_url(self, url):
        ''' Visits a url, and processes its links (if they are new) '''
        print "Visiting %s" % url
        self.browser.load(url)
        try:
            self.browser.wait_load(self.timeout)
        except spynner.SpynnerTimeout:
            print "Timed out while waiting for the page to complete execution. That's ok."
            self.browser.wait_a_little(self.timeout)  # to force the wait, while
                                                      # JS events happen.
        for a in self.browser.soup('a'):
            a.make_links_absolute(base_url=self.browser.url)
            link = a.attrib['href']
            if link not in self.bloom_filter:
                self.bloom_filter.add(link)
                if self.is_link_interesting(link, a.text_content()):
                    print "Found intersting link!  %s" % link
                    self._enqueue_visit(link)

    def _enqueue_visit(self, *args):
        ''' Remembers to visit a url later '''
        self.queue.put(args)

    def crawl(self, url):
        ''' Starts the crawl from the seed url '''
        self._visit_url(url)
        while True:
            try:
                args = self.queue.get_nowait()
            except Queue.Empty:
                break
            self._visit_url(*args)
            self.queue.task_done()

    def close(self):
        ''' Cleanup '''
        shutil.rmtree(self.download_dir_tmp)



# Custom function to select intersting links: here, we are interested in links
# that led to a download
import re
import string
def create_bag_of_words(text):
    return set(re.split(
            '|'.join([re.escape(c) for c in string.punctuation]),
            text.lower()))

def is_link_interesting(url, text):
    bag_of_words = create_bag_of_words(text)
    bag_of_words |= create_bag_of_words(url)
    return bag_of_words.intersection(set(['download', 'click', 'here']))

# This is how you start the crawler
if __name__ == "__main__":
    crawler = Crawler(gui=True, is_link_interesting=is_link_interesting)
    crawler.crawl('http://firefox.com')
    crawler.close()

