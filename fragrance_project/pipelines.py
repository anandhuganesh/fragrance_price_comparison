from itemadapter import ItemAdapter
from fragrance_project.cleaning import parse_price, normalize_brand
import logging

logger = logging.getLogger(__name__)

class FragranceProjectPipeline:
    """
    Validates and cleans fragrance item data before storage.
    """
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # 1. Validate required fields exist
        required_fields = ['raw_name', 'raw_price', 'url']
        for field in required_fields:
            if not adapter.get(field):
                logger.warning(f"[{spider.name}] Item missing required field '{field}': {dict(adapter)}")
                raise DropItem(f"Missing required field: {field}")
        
        # 2. Clean and validate price
        raw_price = adapter.get('raw_price')
        cleaned_price = parse_price(raw_price)
        
        if cleaned_price is None:
            logger.warning(f"[{spider.name}] Could not parse price '{raw_price}' for product '{adapter.get('raw_name')}'")
            raise DropItem(f"Invalid price: {raw_price}")
        
        adapter['cleaned_price'] = cleaned_price
        
        # 3. Normalize brand name
        raw_name = adapter.get('raw_name', '').strip()
        # Simple brand extraction (first word usually is the brand)
        brand = raw_name.split()[0] if raw_name else None
        adapter['brand_name'] = normalize_brand(brand)
        
        logger.info(f"[{spider.name}] ✓ Valid item: {raw_name} | Price: {cleaned_price} AED | Brand: {adapter.get('brand_name')}")
        
        return item


class DropItem(Exception):
    """Exception to drop invalid items"""
    pass
