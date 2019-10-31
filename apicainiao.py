# import scrapy
# import json
import status

import scrapy


from scrapy import signals
from scrapy.crawler import CrawlerProcess
from pydispatch import dispatcher
from scrapy.utils.project import get_project_settings
# from path.to.proyect.spiders.mySpider import mySpider


def get(code, retries):
    print("cainiao")
    run_a_spider_on_script(CainaoSpider)
    return status.OFFLINE


def run_a_spider_on_script(spider, signal=signals.item_passed, slot=None):
    process = CrawlerProcess(get_project_settings())
    if (slot is not None):
        dispatcher.connect(slot, signal)

    process.crawl(spider)
    process.start()


class CainaoSpider(scrapy.Spider):
    name = 'meuteste'

    def start_requests(self):
        print("startreq")
        urls = [
            'https://global.cainiao.com/detail.htm?mailNoList=',
        ]
        # code = 'LP00087825330913'
        # code = 'LP00094346667513'
        code = 'LP00097489321387'

        print("code to track:" + code)
        for url in urls:
            yield scrapy.Request(url=url+code, callback=self.parse)

    def parse(self, response):
        print("crawling status:")
        jsons = response.xpath('//textarea[@id="waybill_list_val_box"]/text()')[0].extract()
        data = json.loads(jsons)
        print(data['data'][0]["latestTrackingInfo"])
