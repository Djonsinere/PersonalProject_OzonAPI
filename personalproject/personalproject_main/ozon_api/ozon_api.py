import requests
from datetime import timedelta, datetime
from django.utils import timezone
from decimal import Decimal
from ..models import Sale, UserProfile, Stock, Product, Warehouse, Sales_analysis
from django.db.models import Sum, Count, Min, Max,  Prefetch
import logging
from django.db.models import Sum, Max, Value
from django.db.models.functions import Coalesce
from collections import defaultdict
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware, is_aware
import math
logging.basicConfig(
    format="{asctime}[{levelname}] - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.WARN
)

def fetch_ozon_sales(user, since_date, to_date, value):

    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        raise Exception("Профиль пользователя не найден")

    client_id = profile.ozon_client_id
    api_key = profile.ozon_api_key
    url = "https://api-seller.ozon.ru/v2/posting/fbo/list"


    if not since_date or not to_date:
        to_date = timezone.now()
        since_date = to_date - timedelta(days=45)
    since = since_date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    to = to_date.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    headers = {
        "Client-Id": client_id,
        "Api-Key": api_key,
        "Content-Type": "application/json"
    }

    offset = 0
    limit = 1000
    total_processed = 0

    while True:
        payload = {
            "dir": "ASC",
            "filter": {
                "since": since,
                "to": to
            },
            "limit": limit,
            "offset": offset,
            "translit": True,
            "with": {
                "analytics_data": True,
                "financial_data": True
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            logging.error(f"Ошибка API: {response.status_code}")
            logging.error(response.text)
            raise Exception(f"Ошибка API: {response.status_code}")

        data = response.json()
        orders = data.get('result', [])

        if not orders:
            logging.info("Нет больше заказов для обработки")
            break

        for order in orders:
            order_id = order.get('order_id')
            status = order.get('status')
            created_at_str = order.get('created_at')
            financial_data = order.get('financial_data', {})
            cluster_to = financial_data.get('cluster_to', 'Не указано')  
            order_number =  order.get('order_number')
            posting_number = order.get('posting_number')

           
            if not created_at_str:
                logging.info(f"Заказ {order_id} не имеет created_at, используем текущее время")
                created_at_str = timezone.now().isoformat()

           
            try:
                if '.' in created_at_str:
                    main_part, fractional = created_at_str.split('.', 1)
                    fractional = fractional[:6]
                    created_at_str = f"{main_part}.{fractional}"
                
                dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                created_at = timezone.make_aware(dt, timezone.utc)
                
            except Exception as e:
                logging.error(f"Ошибка парсинга даты для заказа {order_id}: {str(e)}")
                logging.error(f"Проблемная дата: {created_at_str}")
                created_at = timezone.now()

           
            klaster_id = None
            if cluster_to:
                try:
                  
                    warehouses = Warehouse.objects.filter(klaster_name=cluster_to)
                    
                    if warehouses.exists():
                       
                        klaster_id = warehouses.first().klaster_id
                    else:
                        logging.error(f"Кластер '{cluster_to}' не найден в базе")
                        
                except Exception as e:
                    logging.error(f"Ошибка обработки кластера '{cluster_to}': {str(e)}")

      
            products = order.get('products', [])

            for product in products:
                sku = product.get('sku')
                name = (product.get('name') or '')[:255]
                quantity = product.get('quantity', 0)
                offer_id = product.get('offer_id', '')
                price = Decimal(product.get('price', '0.0')).quantize(Decimal('0.00'))

 
                if not Sale.objects.filter(
                    user=user,
                    order_id=order_id,
                    sku=sku
                ).exists():
                
                    try:
                        product_obj = Product.objects.get(offer_id=offer_id, user=user)
                    except Product.DoesNotExist:
                        product_obj = None

                    Sale.objects.create(
                        user=user,
                        order_id=order_id,
                        status=status,
                        klaster_id=klaster_id,
                        created_at=created_at,
                        order_number = order_number,
                        posting_number = posting_number,
                        sku=sku,
                        name=name,
                        quantity=quantity,
                        offer_id=offer_id,
                        price=price,
                        product=product_obj,
                        klaster_name=cluster_to 

                    )
                    logging.info(f"Создана продажа: {order_id}, кластер: {cluster_to}")
                    total_processed += 1
                else:
                    logging.info(f"Продукт {sku} уже существует, пропускаем") 

        offset += limit

    logging.info(f"Всего создано {total_processed} записей")
    if value == "supply_st_1": calculate_sales_stats(user, since, to) 
    return total_processed


def calculate_sales_stats(user, since_date=None, to_date=None):

    put_days = 30 
    if isinstance(since_date, str):
        since_date = parse_datetime(since_date) or datetime.strptime(since_date, "%Y-%m-%dT%H:%M:%SZ") 
    if isinstance(to_date, str):
        to_date = parse_datetime(to_date) or datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%SZ")


    since_date = make_aware(since_date) if since_date and not is_aware(since_date) else since_date
    to_date = make_aware(to_date) if to_date and not is_aware(to_date) else to_date


    if not since_date or not to_date:
        to_date = timezone.now()
        since_date = to_date - timedelta(days=45)
     
    
    period_days = max((to_date - since_date).days, 1)


    clusters = {
        w.klaster_id: w.klaster_name 
        for w in Warehouse.objects.all() 
        if w.klaster_id is not None
    }

   
    stocks = (
        Stock.objects
        .filter(product__user=user)
        .values('product__offer_id', 'klaster_id')
        .annotate(
            total_stock=Sum('valid_stock_count'),
            product_name=Max('product__name')
        )
    )
    

    sales = (
        Sale.objects
        .filter(
            user=user,
            created_at__range=(since_date, to_date),
          
        )
        .values('offer_id', 'klaster_id')
        .annotate(total_sold=Sum('quantity'))
    )



    combined = {}
    for stock in stocks:
        key = (stock['product__offer_id'], stock['klaster_id'])
        combined[key] = {
            'offer_id': stock['product__offer_id'],
            'product_name': stock['product_name'],
            'klaster_id': stock['klaster_id'],
            'klaster_name': clusters.get(stock['klaster_id'], f"Кластер {stock['klaster_id']}"),
            'total_stock': stock['total_stock'],
            'total_sold': 0
        }

    for sale in sales:
        key = (sale['offer_id'], sale['klaster_id'])
        if key in combined:
            combined[key]['total_sold'] = sale['total_sold']


    results = []
    for key, data in combined.items():
        avg_sales = data['total_sold'] / period_days if period_days > 0 else 0
        days_left = data['total_stock'] / avg_sales if avg_sales > 0 else float('inf')

        try:
            sa_entry = Sales_analysis.objects.filter(klaster_id=data['klaster_id'], user=user).first()
            if sa_entry is not None and sa_entry.top_up_the_balance is not None:
                top_up_the_balance = sa_entry.top_up_the_balance
            else:
                top_up_the_balance = 30
            if sa_entry is not None and sa_entry.put_days is not None:
                put_days = sa_entry.put_days
            else:
                put_days = 30
            
            days_deliv = 2
        except Sales_analysis.DoesNotExist:
            put_days, days_deliv = 30, 2
        
        if data['total_stock'] == 0 and avg_sales > 0:

            all_clusters_for_product = [
                item for k, item in combined.items() 
                if item['offer_id'] == data['offer_id']
            ]
            

            clusters_with_stock = [
                cluster for cluster in all_clusters_for_product
                if cluster['total_stock'] > 0
            ]
            
            if clusters_with_stock:
                avg_sales_list = []
                for cluster in clusters_with_stock:
                    cluster_avg = cluster['total_sold'] / period_days
                    if cluster_avg > 0:
                        avg_sales_list.append(cluster_avg)

                if avg_sales_list:
                    average_day_sales = sum(avg_sales_list) / len(avg_sales_list)
                    
          
                    try:
                        ratio = average_day_sales / avg_sales
                        log_coef = math.log10(1 + ratio)  
                    except ZeroDivisionError:
                        log_coef = 0
                    
                    
                    
                    try:
                        
                        sa_entry = Sales_analysis.objects.get(
                            klaster_id=data['klaster_id'],
                            user=user  
                        )

                        put_days = sa_entry.put_days if sa_entry.put_days is not None else 30
                        days_deliv = 2
                        source = "БД"
                    except Sales_analysis.DoesNotExist:
                       
                        top_up_the_balance = 30
                        put_days = 30
                        days_deliv = 2
                        source = "по умолчанию"
                    except Exception as e:
                        logging.error(f"Ошибка при получении данных анализа:1 {str(e)}")
                        top_up_the_balance = 30
                        put_days = 30
                        days_deliv = 2
                        source = "ошибка"
                    
               
                    result_of_log = log_coef * (int(put_days) + days_deliv)

                    if cluster['total_stock'] == 0:
                        quantity = cluster['total_stock'] - result_of_log * int(put_days)
                        logging.info(f"if:______________________{cluster['total_stock']} - {result_of_log} * {int(put_days)} = {quantity}______________________")
                    else:
                        required = int(avg_sales) * int(put_days)  
                        quantity = max(0, required - cluster['total_stock'])
                        logging.info(f"else:______________________{cluster['total_stock']} - {round(avg_sales, 1)} * {int(put_days)} = {quantity}______________________")
                    quantity = max(int(avg_sales) * int(put_days) - data['total_stock'], 0)

                    logging.info(f"!!!!!Итоговое кол-во товара которое надо поставить = {round(quantity)}!!!!!")
                    
                    if ratio >= 3:
                        logging.info("-------Соответствует неравенству => логарифмический коэф-------")
                        logging.info(f"Название: {data['product_name']}, кластер: {data['klaster_name']} (ID: {data['klaster_id']}) Источник данных: {source} ")
                        logging.info(f"Источник данных: {source}")
                        logging.info(f"Средние продажи в день: {avg_sales:.2f}")
                        logging.info(f"Ср/день (К) с ост: {average_day_sales:.2f}")
                        logging.info(f"Отношение средних: {ratio:.2f}")
                        logging.info(f"Лог коэффициент: {log_coef:.2f}")
                        logging.info(f"Результат: {result_of_log:.2f}")
                    else:
                        logging.info("-------Не соответствует равенству => используется расчет поставить-------")
                        calculation_put = avg_sales * int(put_days) + days_deliv * avg_sales
                        logging.info(f"Название: {data['product_name']}, кластер: {data['klaster_name']} (ID: {data['klaster_id']})")
                        logging.info(f"Дней поставить: {calculation_put:.1f} (источник: {source})")
        else:
            try:
                sa_entries = Sales_analysis.objects.filter(
                    klaster_id=data['klaster_id'],
                    user=user
                )
                if sa_entries.exists():
                    sa_entry = sa_entries.first()  
                    put_days = sa_entry.put_days if sa_entry.put_days is not None else 30
                    source = "БД"
                else:
                    put_days = 30
                    source = "по умолчанию"
                put_days = sa_entry.put_days if sa_entry.put_days is not None else 30
                days_deliv = 2
                source = "БД"
            except Sales_analysis.DoesNotExist:
                put_days = 30
                days_deliv = 2
                source = "по умолчанию"
            except Exception as e:
                logging.error(f"Ошибка при получении данных анализа:2 {str(e)}")
                put_days = 30
                days_deliv = 2
                source = "ошибка"
            if days_left < 1000:
                quantity = (int(top_up_the_balance) - int(days_left)) * int(avg_sales)
            quantity = 0 if 'quantity' not in locals() else quantity
            quantity = max(0, quantity)


        logging.info(f"товар: {data['offer_id']} надо поставить {quantity}; days_left={days_left}; top_up_the_balance = {top_up_the_balance}; avg_sales:{avg_sales}; total_stock{data['total_stock']}")
        results.append({
            'id': f"{data['offer_id']}:{data['klaster_id']}",
            'offer_id': data['offer_id'],
            'product_name': data['product_name'],
            'klaster_id': data['klaster_id'],
            'klaster_name': data['klaster_name'],
            'days_left': float(round(days_left, 1)),
            'avg_sales': float(round(avg_sales, 2)),
            'total_stock': int(data['total_stock']),
            'total_sold': int(data['total_sold']),
            'quantity': int(quantity) 
        })
 
    if not put_days: put_days = 30 

    normal = [r for r in results if r['days_left'] >= top_up_the_balance] 
    urgent = [r for r in results if r['days_left'] < top_up_the_balance]

    regions = {
        2: "Санкт-Петербург и СЗО",
        3: "Урал",
        7: "Дальний Восток",
        12: "Калининград",
        16: "Воронеж",
        17: "Краснодар",
        144: "Тюмень",
        146: "Волгоград",
        147: "Ростов",
        148: "Уфа",
        149: "Казань",
        150: "Самара",
        151: "Новосибирск",
        152: "Омск",
        153: "Кавказ",
        154: "Москва, МО и Дальние регионы",
        155: "Красноярск"
    }

    cluster_ids = regions.keys()
    sa_entries = Sales_analysis.objects.filter(klaster_id__in=cluster_ids, user=user)
    sa_mapping = {}
    for entry in sa_entries:
        sa_mapping[entry.klaster_id] = entry.top_up_the_balance if entry.top_up_the_balance is not None else 30
    for cluster_id in regions.keys():
        sa_mapping.setdefault(cluster_id, 30)

    from collections import defaultdict
    offer_clusters = defaultdict(set)
    offer_product_names = {}

    for entry in normal:
        offer_id = entry['offer_id']
        klaster_id = entry['klaster_id']
        offer_clusters[offer_id].add(klaster_id)
        if offer_id not in offer_product_names:
            offer_product_names[offer_id] = entry['product_name']

    new_entries = []
    required_cluster_ids = set(regions.keys())

    for offer_id in offer_clusters:
        existing_clusters = offer_clusters[offer_id]
        missing_clusters = required_cluster_ids - existing_clusters
        product_name = offer_product_names.get(offer_id, 'Неизвестный товар')

        for cluster_id in missing_clusters:
            top_up = sa_mapping.get(cluster_id, 30)
            new_entry = {
                'id': f"{offer_id}:{cluster_id}",
                'offer_id': offer_id,
                'product_name': product_name,
                'klaster_id': cluster_id,
                'klaster_name': regions.get(cluster_id, f"Кластер {cluster_id}"),
                'days_left': float('inf'),
                'avg_sales': 0,
                'total_stock': 0,
                'total_sold': 0,
                'quantity': 0,
                'top_up_the_balance': int(top_up)
            }
            new_entries.append(new_entry)

    normal.extend(new_entries)
    
    return urgent, normal


