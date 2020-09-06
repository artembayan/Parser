# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class ParserItem(scrapy.Item):

    # define the fields for your item here like:
    # name = scrapy.Field()
    timestamp = scrapy.Field()
    # "RPC":
    url = scrapy.Field()
    title = scrapy.Field()
    brand = scrapy.Field()
    marketing_tags = scrapy.Field()
    section = scrapy.Field()
    price_data = scrapy.Field()
    assets = scrapy.Field()
    metadata = scrapy.Field()
    description = scrapy.Field()
    new = scrapy.Field()
    params = scrapy.Field()
    variants = scrapy.Field()
