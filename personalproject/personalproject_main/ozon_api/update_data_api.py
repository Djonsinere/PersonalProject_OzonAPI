import requests
import time
import logging
from django.db import transaction
from personalproject_main.models import Product, Price, Stock, UserProfile, Warehouse
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class OzonAPI:
    def __init__(self, user_profile: UserProfile):
        """Инициализация API для конкретного пользователя."""
        self.user_profile = user_profile
        self.user = user_profile.user  # Получаем связанного User
        self.session = requests.Session()
        self.base_url = user_profile.ozon_base_url
        self.headers = {
            "Client-Id": user_profile.ozon_client_id,
            "Api-Key": user_profile.ozon_api_key,
            "Content-Type": "application/json"
        }
        self.request_delay = 1.0
        
        logger.info(f"\n=== Инициализация для {self.user.username} ===")
        logger.info(f"Client ID: {user_profile.ozon_client_id}")
        logger.info(f"API Key: {user_profile.ozon_api_key[:6]}...")

    def _make_request(self, url: str, payload: Dict, retry: int = 0) -> Optional[Dict]:
        """Универсальный метод для выполнения запросов к API."""
        try:
            time.sleep(self.request_delay)
            response = self.session.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=20
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and retry < 3:
                wait_time = 60
                logger.warning(f"Превышен лимит запросов. Ожидаем {wait_time} сек...")
                time.sleep(wait_time)
                return self._make_request(url, payload, retry + 1)
            logger.error(f"HTTP Error {e.response.status_code}: {str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса: {str(e)}")
            return None

    def get_products_attributes(self, product_ids: List[str]) -> Dict[str, Dict]:
        """Получение атрибутов товаров по их ID."""
        if not product_ids:
            return {}

        try:
            batch_size = 50
            attributes = {}
            
            for i in range(0, len(product_ids), batch_size):
                batch = product_ids[i:i+batch_size]
                payload = {"filter": {"product_id": batch}, "limit": len(batch)}
                
                response = self._make_request(
                    f"{self.base_url}/v4/product/info/attributes",
                    payload
                )
                
                if response and isinstance(response.get('result'), list):
                    for item in response['result']:
                        item_id = str(item.get('id'))
                        attributes[item_id] = {
                            'name': item.get('name'),
                            'barcode': item.get('barcode'),
                            'height': item.get('height'),
                            'depth': item.get('depth'),
                            'width': item.get('width'),
                            'weight': item.get('weight'),
                            'weight_unit': item.get('weight_unit'),
                            'dimension_unit': item.get('dimension_unit'),
                            'primary_image': item.get('primary_image')
                        }
                time.sleep(1)
                
            return attributes
                
        except Exception as e:
            logger.error(f"Ошибка получения атрибутов: {str(e)}")
            return {}

    def get_all_products(self) -> List[Dict]:
        """Получение всех товаров с пагинацией."""
        products = []
        last_id = ""
        
        while True:
            payload = {"filter": {}, "last_id": last_id, "limit": 1000}
            
            response = self._make_request(
                f"{self.base_url}/v3/product/list",
                payload
            )
            
            if not response or not response.get('result', {}).get('items'):
                break
                
            batch = response['result']['items']
            products.extend(batch)
            last_id = response['result'].get('last_id', '')
            
            for p in batch:
                p['product_id'] = str(p.get('product_id', ''))
            
            logger.info(f"Получено товаров: {len(products)}")
            
            if not last_id:
                break
        
        return products

    def get_prices(self, product_ids: List[str]) -> List[Dict]:
        """Получение цен для списка товаров."""
        if not product_ids:
            return []

        payload = {
            "filter": {
                "product_id": product_ids,
                "visibility": "ALL"
            },
            "limit": 1000
        }
        
        response = self._make_request(
            f"{self.base_url}/v5/product/info/prices",
            payload
        )
        
        return response.get('items', []) if response else []

    def get_stocks(self) -> List[Dict]:
        """Получение данных об остатках."""
        stocks = []
        offset = 0
        
        while True:
            payload = {"filter": {}, "limit": 1000, "offset": offset}
            
            response = self._make_request(
                f"{self.base_url}/v1/analytics/manage/stocks",
                payload
            )
            
            if not response or not response.get('items'):
                break
                
            batch = response['items']
            stocks.extend(batch)
            offset += 1000
            
            logger.info(f"Получено остатков: {len(stocks)}")
            
            if len(batch) < 1000:
                break
        
        return stocks

    @transaction.atomic
    def save_to_db(self, products: List[Dict], prices: List[Dict], stocks: List[Dict]):
        """Сохранение всех данных в базу данных с использованием Django ORM."""
        if not products:
            logger.warning("Нет товаров для сохранения")
            return
    
        try:
            product_ids = [p['product_id'] for p in products]
            attributes = self.get_products_attributes(product_ids)
            
            offer_product_map = {}
            product_by_ozon_id = {}

            # ========== Обработка товаров ==========
            for p in products:
                product_id = str(p.get('product_id', ''))
                offer_id = str(p.get('offer_id', ''))
                
                # Получение атрибутов
                attr = attributes.get(product_id, {})
                
                # Обработка изображения
                primary_image = attr.get('primary_image', '')
                image_url = primary_image.get('url', '') if isinstance(primary_image, dict) else str(primary_image)
                
                # Создание или обновление товара
                product, created = Product.objects.update_or_create(
                    ozon_product_id=product_id,
                    user=self.user,
                    defaults={
                        'name': attr.get('name') or p.get('name', ''),
                        'offer_id': offer_id,
                        'barcode': attr.get('barcode') or p.get('barcode', ''),
                        'height': attr.get('height'),
                        'depth': attr.get('depth'),
                        'width': attr.get('width'),
                        'weight': attr.get('weight'),
                        'weight_unit': attr.get('weight_unit', 'kg'),
                        'dimension_unit': attr.get('dimension_unit', 'cm'),
                        'image_url': image_url,
                        'price': 0.0
                    }
                )

                product_by_ozon_id[product_id] = product
                offer_product_map[offer_id] = product

            # ========== Обработка цен ==========
            price_counter = 0
            for pr in prices:
                product_id = str(pr.get('product_id', ''))
                product = product_by_ozon_id.get(product_id)
                
                if product:
                    price_data = pr.get('price', {})
                    product_price = float(price_data.get('price', 0))
                    
                    # Обновляем продукт
                    product.price = product_price
                    product.save()
                    
                    # Обновляем или создаем цену
                    Price.objects.update_or_create(
                        product=product,
                        defaults={
                            'price': product_price,
                            'marketing_price': price_data.get('marketing_price', 0),
                            'marketing_seller_price': price_data.get('marketing_seller_price', 0),
                            'min_price': price_data.get('min_price', 0),
                            'old_price': price_data.get('old_price', 0),
                            'retail_price': price_data.get('retail_price', 0),
                            'vat': price_data.get('vat', 0),
                            'currency_code': price_data.get('currency_code', 'RUB')
                        }
                    )
                    price_counter += 1

            # ========== Обработка остатков ==========
            stock_counter = 0
            for s in stocks:
                offer_id = str(s.get('offer_id', ''))
                product = offer_product_map.get(offer_id)
                
                if product:
                    sku = s.get('sku')
                    try:
                        product.sku = int(sku) if sku else None
                        product.save()
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid SKU: {sku} для товара {product.id}")

                    warehouse_name = s.get('warehouse_name', 'Unknown')
                    
                    warehouse, _ = Warehouse.objects.update_or_create(
                        warehouse_name=warehouse_name,
                    )

                    Stock.objects.update_or_create(
                        product=product,
                        warehouse_name=warehouse_name,
                        sku=sku,
                        defaults={
                            'valid_stock_count': int(s.get('valid_stock_count', 0)),
                            'klaster_id': warehouse.klaster_id
                        }
                    )
                    stock_counter += 1

            logger.info(f"Успешно сохранено:")
            logger.info(f"- Товары: {len(products)} (с ценами: {price_counter})")
            logger.info(f"- Атрибуты: {len(attributes)}")
            logger.info(f"- Остатки: {stock_counter}")

        except Exception as e:
            logger.error(f"Ошибка сохранения: {str(e)}", exc_info=True)
            raise

    def update_all_data(self):
        """Основной метод для полного обновления данных."""
        try:
            products = self.get_all_products()
            if not products:
                logger.warning("Нет данных о товарах")
                return

            product_ids = [p['product_id'] for p in products]
            prices = self.get_prices(product_ids)
            stocks = self.get_stocks()

            self.save_to_db(products, prices, stocks)

        except Exception as e:
            logger.error(f"Ошибка обновления: {str(e)}")

    def update_attributes_for_existing(self):
        """Обновление атрибутов для существующих товаров."""
        try:
            products = Product.objects.filter(user=self.user)
            product_ids = [str(p.ozon_product_id) for p in products]
            
            attributes = self.get_products_attributes(product_ids)
            
            updated = 0
            for product in products:
                attr = attributes.get(str(product.ozon_product_id))
                if attr:
                    primary_image = attr.get('primary_image', '')
                    image_url = primary_image.get('url', '') if isinstance(primary_image, dict) else str(primary_image)

                    Product.objects.filter(id=product.id).update(
                        name=attr.get('name', product.name),
                        barcode=attr.get('barcode', product.barcode),
                        height=attr.get('height', product.height),
                        depth=attr.get('depth', product.depth),
                        width=attr.get('width', product.width),
                        weight=attr.get('weight', product.weight),
                        weight_unit=attr.get('weight_unit', product.weight_unit),
                        dimension_unit=attr.get('dimension_unit', product.dimension_unit),
                        image_url=image_url
                    )
                    updated += 1
            
            logger.info(f"Обновлено атрибутов: {updated}/{len(products)}")

        except Exception as e:
            logger.error(f"Ошибка обновления атрибутов: {str(e)}")
