# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import datetime
import json

from scrapy.exceptions import DropItem
from sqlalchemy.orm import sessionmaker

from Crawler.util.category.category_processing import Categorizing
from Crawler.util.common import check_essential_element
from models import Product, db_connect, create_deals_table


class CategoryPipeline(object):
    def process_item(self, item, spider):
        category = Categorizing(item=item)
        category.convert_category()
        return category.get_item()


class FilterPipeline(object):
    def __init__(self):
        self.item_set = set()
    
    def process_item(self, item, spider):
        check_item = (item.get('brand'), item.get('productNo'))
        if check_item in self.item_set:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.item_set.add(check_item)
        return item


class CrawlerPipeline(object):
    def __init__(self):
        engine = db_connect()
        create_deals_table(engine)
        self.Session = sessionmaker(bind=engine)
    
    def process_item(self, item, spider):
        session = self.Session()
        if check_essential_element(item):
            with open("logs/drop_file_%s.json" % datetime.datetime.today().strftime("%y-%m-%d"), 'a') as f:
                f.write(json.dumps(dict(item), ensure_ascii=False)+'\r\n')
            raise DropItem("Duplicate item found: %s" % item)
        else:
            product = Product(**item)
            
            try:
                if session.query(Product).filter_by(productNo=item.get('productNo'),
                                                    brand=item.get('brand')).first() is None:
                    session.add(product)
                else:
                    session.query(Product).filter_by(productNo=item.get('productNo'), brand=item.get('brand')).update(
                        item)
                session.commit()
            except:
                session.rollback()
                raise
            finally:
                session.close()
        
        return item
    
    def close_spider(self, spider):
        pass
