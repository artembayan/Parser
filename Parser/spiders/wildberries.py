# -*- coding: utf-8 -*-
import scrapy
import datetime
from Parser.items import ParserItem

"""
Запускал на Windows через Anaconda и PyCharm
КОМАНДА ДЛЯ ЗАПУСКА ПАРСЕРА ИЗ ТЕРМИНАЛА ПАЙЧАРМА:
scrapy runspider Parser\spiders\wildberries.py --output=data.json -L WARNING
"""

class WildberriesSpider(scrapy.Spider):
    name = 'wildberries'
    start_urls = ['https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli?sort=popular']
    # #Характеристики юзер-агента
    # uagent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
    # # IP адрес прокси-сервера в Москве (настройки - middlewares.py)
    # proxy = '81.200.82.240:8080'

    def parse(self, response):
        # Получение URL каждого товара по порядку

        urls = response.xpath("//div[@class='dtList-inner']/span/span/span/a/@href").extract()
        #response.css('div.dtList-inner a.ref_goods_n_p::attr(href)').extract()

        for url in urls:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, cookies={'__wbl':'cityId=77&regionId=77&city=Москва&phone=84957755505&latitude'
                                                           '=55,7247&longitude=37,7882'}, callback=self.parse_details)

        #Постраничный переход
        next_page_url = response.css('a.pagination-next::attr(href)').extract_first()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, cookies={'__wbl':'cityId=77&regionId=77&city=Москва&phone=84957755505'
                                                                     '&latitude=55,7247&longitude=37,7882'}, callback=self.parse)

    #Парсинг каждого товара
    def parse_details(self, response):

        #Очищение цены от пробелов и знака валюты
        def clean_price(text):
            digits = [ symbol for symbol in text if symbol.isdigit() ]
            cleaned_price = ''.join(digits)
            if not cleaned_price:
                return None
            return float(cleaned_price)

        item = ParserItem()

        #Информация о времени обращения в формате timestamp
        timestamp = datetime.datetime.now().timestamp()
        item['timestamp'] = timestamp
        item['url'] = response.url

        #Парсинг наименования товара
        item['title'] = response.xpath("//div[@class='brand-and-name j-product-title']/span[@class='name']/text()").extract_first().strip()
            #response.css('div.brand-and-name > span.name::text').extract_first().strip()

        #Парсинг возможных цветовых представлений товара
        if response.xpath("//div[@class='color j-color-name-container']/span[@class='color']/text()"):
            color = response.xpath("//div[@class='color j-color-name-container']/span[@class='color']/text()").extract_first()
            item['title'] = f"{item['title']}, {color}"

        #Парсинг список тэгов с акциями, скидками
        if response.xpath("//div[@class='j-big-sale-icon-card-wrapper i-spec-action-v1']/a[@class='spec-actions-link']/text()"):
                #response.css('div.j-big-sale-icon-card-wrapper > a.spec-actions-link::text'):
            item['marketing_tags'] = response.xpath("//div[@class='j-big-sale-icon-card-wrapper i-spec-action-v1']/a[@class='spec-actions-link']/text()").extract_first()
        else:
            item['marketing_tags'] = None

        #Парсинг брэнда товара
        item['brand'] = response.xpath("//span[@class='brand']/text()").extract_first()

        #Парсинг иерархии разделов
        for element in response.xpath("//ul[@class='bread-crumbs']"):
            item['section'] = element.xpath("//li['breadcrumbs-item']/a[@class='breadcrumbs_url']/span/text()").extract()


        #Парсинг цены со скидкой с посторонними элементами
        raw_current_price = response.xpath("//div[@class='final-price-block']/span[@class='final-cost']/text()").extract_first()
        #response.css('div.final-price-block > span.final-cost::text').extract_first()

        #Очистка цены от посторонних элементов
        current_price = clean_price(raw_current_price)

        #Парсинг оригинальной цены и размера скидки, если она есть
        if response.xpath("//span[@class='old-price']/del[@class='c-text-base']/text()").extract_first():
            raw_orginal_price = response.xpath("//span[@class='old-price']/del[@class='c-text-base']/text()").extract_first()
            #response.css('span.old-price > del.c-text-base::text').extract_first()

            #Очистка цены от посторонних элементов
            original_price = clean_price(raw_orginal_price)

            #Подсчет скидки
            discount = round(100 - (current_price / original_price) * 100)
            sale_tag = f"Скидка {discount}%"
            item['price_data'] = {"current": current_price, "original": original_price, "sale_tag": sale_tag}

        else:
            item['price_data'] = {"current": current_price}

        #Парсинг главного изображения товара
        main_image = "https:" + response.xpath("//ul[@class='carousel']/li/a[@class='j-carousel-image enabledZoom current']/@href").extract_first()
                     #response.css('ul.carousel > li > a.j-carousel-image.enabledZoom.current::attr(href)').extract_first()

        #Парсинг больших изображений товара
        images = response.xpath("//ul[@class='carousel']/li/a[@class='j-carousel-image enabledZoom']/@href").extract()
            #response.css('ul.carousel > li > a.j-carousel-image.enabledZoom::attr(href)').extract()
        set_images = ["https:" + i for i in images]

        item['assets'] = {"main_image": main_image, "set_images": set_images}

        #Парсинг описания товара
        description = response.xpath("//div[@class='j-description description-text collapsable-content']/p/text()").extract_first()
            #response.css('div.j-description.description-text.collapsable-content > p::text').extract_first()

        #Парсинг характеристик товара
        for param in response.css('div.params'):
            seq_list = param.xpath("//div[@class='pp']/span/b/text()").extract()
            #param.css('div.pp > span > b::text').extract()
            val_list = param.xpath("//div[@class='pp']/span/text()").extract()
            #param.css('div.pp > span::text').extract()
            params = dict(zip(seq_list, val_list))

        #Парсинг количества вариантов товара
        i = 1
        if response.xpath("//div[@class='j-colors-list j-adaptive-carousel colorpicker']"):
            for o in response.xpath("//div[@class='j-colors-list j-adaptive-carousel colorpicker']/ul/li[@class='color j-color']"):
                i += 1
        else:
            pass

        item['metadata'] = {'description': description}
        item['metadata'].update(params)
        item['variants'] = i

        # print(item)
        # print('---------------')
        yield item


