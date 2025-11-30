# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class FragranceItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    """
    Defines the fields for our fragrance data.
    """
    # Raw Data Fields (extracted directly from the website)
    raw_name = scrapy.Field()
    raw_price = scrapy.Field()
    url = scrapy.Field()
    
    image_url = scrapy.Field()  # Extracted in parse method
    brand_name = scrapy.Field() # Placeholder for future data cleaning
    raw_size = scrapy.Field()   # Placeholder for future data cleaning
    
    # Processed Data Fields (after cleaning)
    cleaned_price = scrapy.Field()
    
    #Metadata Fields
    website_source = scrapy.Field()
    timestamp = scrapy.Field()

