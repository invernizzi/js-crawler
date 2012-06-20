js-crawler
==========

A short and simple web crawler written in Python, that uses Webkit and executes Javascript.

How to use
-----------
```python
crawler = Crawler(gui=True,                                                 # To see the crawler in action
                  is_link_interesting=lambda url, text: 'download' in url)  # Follow every link containing
                                                                            #  "download" in the url
crawler.crawl('http://firefox.com')
crawler.close()
```