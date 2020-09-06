# -*- coding: utf-8 -*-
import scrapy
import datetime
from Parser.items import ParserItem

# Запускал на Windows через Anaconda и PyCharm
# КОМАНДА ДЛЯ ЗАПУСКА ПАРСЕРА ИЗ ТЕРМИНАЛА ПАЙЧАРМА:
# scrapy runspider Parser\spiders\wildberries.py --output=data.json -L WARNING

class WildberriesSpider(scrapy.Spider):
    name = 'wildberries'
    start_urls = ['https://www.wildberries.ru/catalog/obuv/zhenskaya/sabo-i-myuli/myuli?sort=rate']
    #Характеристики юзер-агента
    uagent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
    # IP адрес прокси-сервера в Москве (настройки - middlewares.py)
    proxy = '81.200.82.240:8080'

    def parse(self, response):
        urls = response.css('div.dtList-inner a.ref_goods_n_p::attr(href)').extract()# Получение URL каждого товара по порядку
        for url in urls:
            url = response.urljoin(url)
            yield scrapy.Request(url=url, callback=self.parse_details)

        #Постраничный переход
        next_page_url = response.css('a.pagination-next::attr(href)').extract_first()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    #Парсинг каждого товара
    def parse_details(self, response):

        item = ParserItem()

        #Очищение цены от пробелов и знака валюты
        def clean_price(text):
            digits = [ symbol for symbol in text if symbol.isdigit() ]
            cleaned_price = ''.join(digits)
            if not cleaned_price:
                return None
            return cleaned_price

        #Информация о времени обращения в формате timestamp
        timestamp = datetime.datetime.now().timestamp()
        item['timestamp'] = timestamp
        item['url'] = response.url

        #Парсинг наименования товара
        item['title'] = response.css('div.brand-and-name > span.name::text').extract_first()

        # item[ 'new' ] =  response.css('div.header-wrapper.lang-ru > ul.header-top > li.geocity.item > span').extract_first()
        # item[ 'new' ] =  response.css('div.delivery-cond j-delivery-cond > span.dfn').extract_first()

        #Парсинг возможных цветовых представлений товара
        if response.css('div.color > span.color::text'):
            color = response.css('div.color > span.color::text').extract_first()
            item['title'] = '{' + item['title'] + '},' + ' {' + color + '}'

        #Парсинг список тэгов с акциями, скидками
        if response.css('div.j-big-sale-icon-card-wrapper > a.spec-actions-link::text'):
            item['marketing_tags'] = response.css('div.j-big-sale-icon-card-wrapper > a.spec-actions-link::text').extract_first()
        else:
            item['marketing_tags'] = None

        #Парсинг брэнда товара
        item['brand'] = response.css('div.brand-and-name > span.brand::text').extract_first()

        #Парсинг иерархии разделов
        for element in response.css('ul.bread-crumbs'):
            item['section'] = element.css('li.breadcrumbs-item > a.breadcrumbs_url > span::text').extract()

        #Парсинг цены со скидкой с посторонними элементами
        raw_current_price = response.css('div.final-price-block > span.final-cost::text').extract_first()
        #Очистка цены от посторонних элементов
        current = clean_price(raw_current_price)
        current_price = float(current) / (10 ** len(current))

        #Парсинг оригинальной цены и размера скидки, если она есть
        if response.css('span.old-price > del.c-text-base::text'):
            raw_orginal_price = response.css('span.old-price > del.c-text-base::text').extract_first()
            #Очистка цены от посторонних элементов
            original = clean_price(raw_orginal_price)
            original_price = float(original) / (10 ** len(original))
            #Подсчет скидки
            sale_tag = "Скидка " + str(int(100 - ((int(current) / int(original))) * 100)) + "%"
            item['price_data'] = {"current": current_price, "original": original_price, "sale_tag": sale_tag}
        else:
            item['price_data'] = {"current": current_price}

        #Парсинг главного изображения товара
        main_image = response.css('ul.carousel > li > a.j-carousel-image.enabledZoom.current::attr(href)').extract_first()
        #Парсинг больших изображений товара
        set_images = response.css('ul.carousel > li > a.j-carousel-image.enabledZoom::attr(href)').extract()

        item['assets'] = {"main_image": main_image, "set_images": set_images}

        #Парсинг описания товара
        description = response.css('div.j-description.description-text.collapsable-content > p::text').extract_first()

        #Парсинг характеристик товара
        for param in response.css('div.params'):
            seq_list = param.css('div.pp > span > b::text').extract()
            val_list = param.css('div.pp > span::text').extract()
            params = dict(zip(seq_list, val_list))

        #Парсинг количества вариантов товара
        i = 0
        if response.css('div.j-colors-list'):
            for o in response.css('div.j-colors-list > ul > li.color'):
                i += 1
        else:
            i = 1

        item['metadata'] = {'description': description}
        item['metadata'].update(params)
        item['variants'] = i

        # print(item)
        # print('---------------')
        yield item


