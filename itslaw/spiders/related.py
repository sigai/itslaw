# -*- coding: utf-8 -*-
import json
from urllib.parse import urlencode, urlparse
from time import sleep

import scrapy
from scrapy import Request
from scrapy.exceptions import CloseSpider
from itslaw.items import JudgementItem
from redis import Redis, ConnectionPool
from scrapy.conf import settings


class HomepageRecommendSpider(scrapy.Spider):
    name = 'related'
    allowed_domains = ['www.itslaw.com']

    def __init__(self):
        self.pool = ConnectionPool(host=settings["REDIS_HOST"], port=settings["REDIS_PORT"], decode_responses=True, db=0)
        self.r = Redis(connection_pool=self.pool)
    
    def start_requests(self):
        for _ in range(10000000):
            doc = self.r.srandmember("itslaw:start")
            if self.r.sismember("itslaw:crawled", doc):
                continue
            pageSize = 100
            pageNo = 1
            parameters = {
                "pageSize": pageSize,
                "pageNo": pageNo,
            }

            url = f"https://www.itslaw.com/api/v1/judgements/judgement/{doc}/relatedJudgements?" + urlencode(parameters)
            yield Request(url=url, meta={"parameters": parameters, "doc": doc})

    def parse(self, response):
        res = json.loads(response.body_as_unicode())
        code = res["result"]["code"]
        message = res["result"]["message"]
        doc = response.meta["doc"]
        
        if 0 != code:
            error_essage = res["result"]["errorMessage"]
            print(message, error_essage)
            sleep(60)
            return
        else:
            self.r.sadd("itslaw:crawled", doc)
        
        data = res["data"]
        relatedJudgementInfo = data['relatedJudgementInfo']
        relatedJudgements = relatedJudgementInfo.get("relatedJudgements", None)
        if not relatedJudgements:
            return

        for j in relatedJudgements:
            yield JudgementItem(id=j["key"])
        
        pageNo = relatedJudgementInfo["pageNo"]
        if pageNo == 1:
            return
        parameters = response.meta["parameters"]
        parameters["pageNo"] = pageNo

        urlparse(response.url)
        url = response.url.split("?")[0] + "?" + urlencode(parameters)

        yield Request(url=url,  meta={"parameters": parameters, "doc": doc})
