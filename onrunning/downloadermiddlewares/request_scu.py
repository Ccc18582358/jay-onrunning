import json
import re

import jsonpath
import requests
import scrapy.http
from lxml import etree
from scrapy.utils.defer import deferred_from_coro

import chardet
import urllib.parse
from onrunning import settings
from urllib.parse import urlparse, unquote


def escape_url(url):
    if 'zenscrape' in url:
        parsed_url = urlparse(url)
        query = parsed_url.query
        new_url = unquote(dict([i.split('=') for i in query.split('&')])['url'])
        return new_url
    return url


class CrawlerRequest(object):

    def __init__(self):
        self.url = "https://www.on-running.com/en-us/graphql"
        self.payload = {
            "variables": {
                "identifier": "explore",
                "first": 16,
                "before": "",
                "after": "",
                "itemFilters": [
                    {
                        "name": "product",
                        "values": [
                            "shoes"
                        ]
                    }
                ],
                "variantFilters": [
                    {
                        "name": "gender",
                        "values": [
                            "mens"
                        ]
                    }
                ]
            },
            "query": "query ($identifier: String!, $sortBy: ItemsSortByInput, $itemFilters: [FilterInput!], $variantFilters: [FilterInput!], $first: Int, $last: Int, $before: String, $after: String) {\n  filterPage(identifier: $identifier) {\n    explodeVariants\n    articlesPageBottom\n    paginatedItems(\n      first: $first\n      last: $last\n      before: $before\n      after: $after\n      sortBy: $sortBy\n      filters: $itemFilters\n    ) {\n      totalCount\n      pageInfo {\n        startCursor\n        endCursor\n        hasPreviousPage\n        hasNextPage\n        __typename\n      }\n      nodes {\n        id\n        name\n        mainVariantId\n        price\n        labels\n        productData {\n          shortDescription\n          productSubtype\n          __typename\n        }\n        variants(filters: $variantFilters) {\n          id\n          isBackorderable\n          isRaffle\n          hasRaffleEnded\n          colorName\n          filterValues\n          labels\n          productUrl\n          isMembersOnly\n          imageUrl\n          backgroundImageUrl\n          backgroundVideoUrl\n          skus\n          spreeProduct\n          productVariantData {\n            defaultImageSmall\n            assets\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n"
        }
        self.headers = {
            'authority': 'www.on-running.com',
            'accept': '*/*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-type': 'application/json',
            'on-client': 'frontend',
            'origin': 'https://www.on-running.com',
            'referer': '',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102", "Google Chrome";v="102"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',

        }

    def process_request(self, request, spider):
        #  fetch请求
        request_url = escape_url(request.url)
        callback = request.meta["jay"].get("callback") if request.meta["jay"].get("callback") else \
            request.meta["jay"]["command"]["callback"]
        if callback == "parse_scu" and request_url != self.url:
            payload = {
                "operationName": None,
                "variables": {
                    "slug": ""
                },
                "query": "query ($slug: String!) {\n  productGroup(slug: $slug, isFetchingAssets: true) {\n    name\n    slug\n    productData {\n      careInstructions\n      composition\n      sustainability\n      description\n      mediaGalleryItems\n      name\n      productSpec\n      productSpecType\n      productSubtype\n      labels\n      shortDescription\n      isSubscriptionProduct\n      variants {\n        id\n        labels\n        assets\n        description\n        color\n        defaultImage\n        defaultImageSmall\n        topBanner\n        campaignIds {\n          ...campaignIds\n          __typename\n        }\n        fit\n        modelInformation\n        isMembersOnly\n        inseams {\n          size\n          cm\n          inches\n          __typename\n        }\n        gender\n        highlights\n        spreeProduct {\n          id\n          isLocked\n          isBackorderable\n          isPreorderable\n          isRaffle\n          raffleExpiresAt\n          raffleDrawAt\n          hasRaffleEnded\n          price\n          productType\n          productUrl\n          sku\n          spreeVariants {\n            id\n            size\n            sku\n            stock\n            price\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  sizeInfo {\n    isSizeInfoVisible\n    __typename\n  }\n}\n\nfragment campaignIds on CampaignIds {\n  variationId\n  decisionId\n  __typename\n}\n"
            }

            slug = re.search('(?<=products/).*?(?=/)', request_url).group(0)
            payload["variables"]["slug"] = slug
            self.headers['referer'] = request_url
            return scrapy.Request(method="POST", url=self.url, meta=request.meta,
                                  body=json.dumps(payload), headers=self.headers, callback=getattr(spider, 'parse_scu'))
        return

    def process_response(self, request, response, spider):
        response_url = escape_url(response.url)
        #  列表页请求
        if "/products/" not in response_url and self.url != response_url:
            #  filter_json这个文件是问了获取他的payload中的itemFilters，variantFilters，获取参数的key和value
            production_path = "/app/onrunning/filter_json"
            development_path = "../filter_json"
            with open(production_path, "r") as f:
                filter_json = json.load(f)

            param_list = response_url.partition('?')[0].partition('explore/')[2].split('/')
            for index, param in enumerate(param_list):
                filter_list = list(filter(lambda x: list(filter(lambda y: y["value"] == param, x["values"])),
                                          filter_json["data"]["filterPage"]["filters"]))[0]
                filter_level = filter_list['level']
                filter_id = filter_list['id']
                self.process_filter_param(filter_id, filter_level, param)
            self.headers['referer'] = response_url
            meta = request.meta
            meta['payload'] = self.payload
            meta['headers'] = self.headers
            return scrapy.Request(method="POST", url=self.url, meta=meta,
                                  body=json.dumps(self.payload), headers=self.headers)

        return response

    def process_filter_param(self, filter_id, filter_level, param):
        if filter_level == "item":
            for item_dict in self.payload["variables"]["itemFilters"]:
                if filter_id in list(item_dict.keys()):
                    item_dict["values"].append(param)
                    return
            self.payload["variables"]["itemFilters"].append({"name": filter_id, "values": [param]})

        elif filter_level == "variant":
            for item_dict in self.payload["variables"]["variantFilters"]:
                if filter_id in list(item_dict.keys()):
                    item_dict["values"].append(param)
                    return
            self.payload["variables"]["variantFilters"].append({"name": filter_id, "values": [param]})
