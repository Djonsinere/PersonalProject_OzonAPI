import django_tables2 as tables
from .models import Product, Stock, Sales_analysis, Input_data
from django.utils.safestring import mark_safe



class StockTable(tables.Table):
    class Meta:
        model = Stock
        template_name = "django_tables2/bootstrap4.html"
        fields = ("warehouse_name", "valid_stock_count", "sku")
        attrs = {"class": "table table-striped table-sm small"}


class SalesAnalysisTable(tables.Table): 
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="pk", orderable=False)  

    supply_name = tables.TemplateColumn(
        '<input type="text" name="supply_name" value="{{ record.supply_name|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Название поставки"
    )
    type_supply = tables.TemplateColumn(
    template_code="""
    <select name="type_supply" class="form-control form-control-sm"
            hx-post="{% url 'update_sales_analysis' record.pk %}"
            hx-trigger="change delay:500ms"
            hx-target="this">
        <option value="Кроссдокинг" {% if record.type_supply == "Кроссдокинг" %}selected{% endif %}>Кроссдокинг</option>
        <option value="Прямая" {% if record.type_supply == "Прямая" %}selected{% endif %}>Прямая</option>
        
    </select>
    """,
    verbose_name="Вид поставки"
    )   
    warehouse_name = tables.TemplateColumn(
        '<input type="text" name="warehouse_name" value="{{ record.warehouse_name|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Название склада(кроссдок)"
    )
    shipping_point = tables.TemplateColumn(
    template_code="""
    <select name="shipping_point" class="form-control form-control-sm"
            hx-post="{% url 'update_sales_analysis' record.pk %}"
            hx-trigger="change delay:500ms"
            hx-target="this">
        <option value="ПВЗ" {% if record.shipping_point == "ПВЗ" %}selected{% endif %}>ПВЗ</option>
        <option value="ППЗ" {% if record.shipping_point == "ППЗ" %}selected{% endif %}>ППЗ</option>
        <option value="СЦ" {% if record.shipping_point == "СЦ" %}selected{% endif %}>СЦ</option>
    </select>
    """,
    verbose_name="Точка отгрузки"
)
    region_destination = tables.Column(verbose_name="Регион назначения")
    top_up_the_balance = tables.TemplateColumn(
        '<input type="text" name="top_up_the_balance" value="{{ record.top_up_the_balance|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Пополнять остаток дн"
    )
    put_days = tables.TemplateColumn(
        '<input type="text" name="put_days" value="{{ record.put_days|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Поставить дн"
    )
    name_driver = tables.TemplateColumn(
        '<input type="text" name="name_driver" value="{{ record.name_driver|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="ФИО Водителя"
    )
    driver_mobile_number = tables.TemplateColumn(
        '<input type="text" name="driver_mobile_number" value="{{ record.driver_mobile_number|default_if_none:"" }}"'
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Номер телефона водителя"
    )
    car_mark = tables.TemplateColumn(
        '<input type="text" name="car_mark" value="{{ record.car_mark|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Марка машины"
    )
    car_number = tables.TemplateColumn(
        '<input type="text" name="car_number" value="{{ record.car_number|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Номер машины"
    )
    capacity = tables.TemplateColumn(
        '<input type="text" name="capacity" value="{{ record.capacity|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Вместимость"
    )
    weight = tables.TemplateColumn(
        '<input type="text" name="weight" value="{{ record.weight|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Вес"
    )

    class Meta:
        model = Sales_analysis
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select", "supply_name", "type_supply", "shipping_point", "region_destination", 
                  "warehouse_name", "top_up_the_balance", "put_days", "name_driver", "driver_mobile_number", 
                  "car_mark", "car_number", "capacity", "weight")
        attrs = {"id": "sales-table",
                 "class": "table table-striped table-sm small"}  
        
class BaseProductsTable(tables.Table):
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="id", orderable=False)
    offer_id = tables.Column(verbose_name="Артикул")
    product_name = tables.Column(verbose_name="Название")
    days_left = tables.Column(verbose_name="Дней осталось")
    total_stock = tables.Column(verbose_name="Остаток")
    klaster_id = tables.Column(verbose_name="ID кластера")
    klaster_name = tables.Column(verbose_name="Имя кластера")
    avg_sales = tables.Column(verbose_name="Продаж/день")
    total_sold = tables.Column(verbose_name="Продано всего")

    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select", "offer_id", "product_name", "avg_sales", "days_left", "total_stock", "total_sold", "klaster_name")#"klaster_id",
        attrs = {
            "id": "products-table",
            "class": "table table-striped table-sm small",
            "thead": {"class": "thead-grey"}
        }

class UrgentProductsTable(BaseProductsTable):
    class Meta(BaseProductsTable.Meta):
        attrs = {
            "id": "urgent-table",
            "class": "table table-striped table-sm small",
            "thead": {"class": "thead-grey"}
        }

class NormalProductsTable(BaseProductsTable):
    class Meta(BaseProductsTable.Meta):
        attrs = {
            "id": "normal-table",
            "class": "table table-striped table-sm small",
            "thead": {"class": "thead-grey"}
        }


class DriversTable(tables.Table):
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="pk", orderable=False)  
    name_driver = tables.TemplateColumn(
        '<input type="text" name="name_driver" value="{{ record.name_driver|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="ФИО водителя"
    )
    driver_mobile_number = tables.TemplateColumn(
        '<input type="text" name="driver_mobile_number" value="{{ record.driver_mobile_number|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Мобильный телефон водителя"
    )
    class Meta:
        model = Sales_analysis
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select", "name_driver", "driver_mobile_number")
        attrs = {"id": "drivers-table",
                 "class": "table table-striped table-sm small"} 

class VehiclesTable(tables.Table):
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="pk", orderable=False)  

    car_mark = tables.TemplateColumn(
        '<input type="text" name="car_mark" value="{{ record.car_mark|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Марка машины"
    )
    car_number = tables.TemplateColumn(
        '<input type="text" name="car_number" value="{{ record.car_number|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Номер машины"
    )
    weight = tables.TemplateColumn(
        '<input type="text" name="weight" value="{{ record.weight|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Макс вес кг"
    )
    capacity = tables.TemplateColumn(
        '<input type="text" name="capacity" value="{{ record.capacity|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Вместимость м^3"
    )
    class Meta:
        model = Sales_analysis
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select",  "car_mark", "car_number", "weight", "capacity")
        attrs = {"id": "drivers-table",
                 "class": "table table-striped table-sm small"}
         
class ProductTable(tables.Table): 
    select = tables.CheckBoxColumn(accessor="pk", orderable=False)  
    name = tables.Column(verbose_name="Название")

    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select", "name")  #, "offer_id"
        attrs = {"class": "table table-striped table-sm small"}

class ShippingPointTable(tables.Table):
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="pk", orderable=False)  # Чекбокс
    name_shipping_point = tables.TemplateColumn(
        '<input type="text" name="name_shipping_point" value="{{ record.name_shipping_point|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_shipping_point_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Название"
    )
    type_shipping_point = tables.TemplateColumn(
    template_code='''
    <select name="type_shipping_point" class="form-control"
            hx-post="{% url 'update_shipping_point_table' record.pk %}"
            hx-trigger="change delay:500ms"
            hx-target="this"
            hx-swap="outerHTML">
        <option value="ПВЗ" {% if record.type_shipping_point == "ПВЗ" %}selected{% endif %}>ПВЗ</option>
        <option value="ППЗ" {% if record.type_shipping_point == "ППЗ" %}selected{% endif %}>ППЗ</option>
        <option value="СЦ" {% if record.type_shipping_point == "СЦ" %}selected{% endif %}>СЦ</option>
    </select>
    ''',
    verbose_name="Тип"
)
    class Meta:
        model = Input_data
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select",  "name_shipping_point", "type_shipping_point",)
        attrs = {"id": "shipping_point-table",
                 "class": "table table-striped table-sm small"} 

class KlasterTable(tables.Table): 
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="pk", orderable=False)
    region_destination = tables.Column(verbose_name="Активые кластеры")

    top_up_the_balance = tables.TemplateColumn(
        '<input type="text" name="top_up_the_balance" value="{{ record.top_up_the_balance|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Пополнять остаток от дн"
    )
    put_days = tables.TemplateColumn(
        '<input type="text" name="put_days" value="{{ record.put_days|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_sales_analysis" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Пополнять на дн"
    )
    class Meta:
        model = Sales_analysis
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select", "region_destination", "top_up_the_balance", "put_days")
        attrs = {"id": "profile_klaster-table",
                 "class": "table table-striped table-sm small"}  


class ReferenceTable(tables.Table):
    id = tables.Column(visible=False)
    select = tables.CheckBoxColumn(accessor="id", orderable=False)
    name = tables.Column(verbose_name="Название")
    image_url = tables.TemplateColumn(
        '<img src="{{ record.image_url }}" width="80" height="80" class="img-fluid rounded">',
        verbose_name="Фото"
    )
    offer_id = tables.Column(verbose_name="Артикул")
    barcode = tables.Column(verbose_name="Штрихкод")
    price = tables.Column(verbose_name="Цена")
    sku = tables.Column(verbose_name="SKU")
    model = tables.TemplateColumn(
        '<input type="text" name="model" value="{{ record.model|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Модель"
    )
    europallet =tables.TemplateColumn(
        '<input type="text" name="europallet" value="{{ record.europallet|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Европаллета"
    )
    box_type =  tables.TemplateColumn(
        '<input type="text" name="box_type" value="{{ record.box_type|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Короб тип"
    )
    box_xl = tables.TemplateColumn(
        '<input type="text" name="box_xl" value="{{ record.box_xl|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="XL корообка"
    )
    box_l =tables.TemplateColumn(
        '<input type="text" name="box_l" value="{{ record.box_l|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="L коробка"
    )
    box_m =tables.TemplateColumn(
        '<input type="text" name="box_m" value="{{ record.box_m|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="M коробка"
    )
    box_s = tables.TemplateColumn(
        '<input type="text" name="box_s" value="{{ record.box_s|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="S коробка"
    )
    fit_from =tables.TemplateColumn(
        '<input type="text" name="fit_from" value="{{ record.fit_from|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Годен от"
    )
    fit_to =tables.TemplateColumn(
        '<input type="text" name="fit_to" value="{{ record.fit_to|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Годен до"
    )
    cost_price  =tables.TemplateColumn(
        '<input type="text" name="cost_price" value="{{ record.cost_price|default_if_none:"" }}" '
        'class="form-control" hx-post="{% url "update_refernce_table" record.pk %}" hx-trigger="change delay:500ms">', verbose_name="Себестоимость"
    )
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        fields = ("select", "name", "image_url", "offer_id", "barcode", "sku", "model", "europallet", "box_type", "box_xl", "box_l", "box_m", "box_s", "fit_from", "fit_to", "price", "cost_price")
        attrs = {
            "id": "reference-table",
            "class": "table table-striped table-sm small",
            "thead": {"class": "thead-grey"}
        }


class Total_supply_table(tables.Table): 
    number = tables.Column(verbose_name="Номер")
    offer_id = tables.Column(verbose_name="Артикул")
    image_url = tables.TemplateColumn(
        '<img src="{{ record.image_url }}" width="80" height="80" class="img-fluid rounded">',
        verbose_name="Фото"
    )
    name = tables.Column(verbose_name="Название товара")
    quantity = tables.Column(verbose_name="Количество")
    cost_price = tables.Column(verbose_name="Себестоимость")
    total_price = tables.Column(verbose_name="Цена")
    
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        fields = ("number", "name", "offer_id", "image_url", "quantity", "cost_price", "total_price")
        attrs = {"id": "shipping_point-table",
                 "class": "table table-striped table-sm small"} 

class Products_in_supply(tables.Table): 
    offer_id = tables.Column(verbose_name="Артикул")
    image_url = tables.TemplateColumn(
        '<img src="{{ record.image_url }}" width="80" height="80" class="img-fluid rounded">',
        verbose_name="Фото"
    )
    quantity = tables.TemplateColumn(
    """
    <form method="post" action="{% url 'update_products_in_supply_table' %}" id="main-form">
    {% csrf_token %}
    <input type="number"
           name="quantity:{{ record.offer_id }}:{{ record.klaster_id }}"
           value="{{ record.quantity }}"
           class="form-control form-control-sm"
           min="0">
    </form>
    """,
    verbose_name="Количество"
    )
    days_to_end = tables.Column(verbose_name="Дней до конца")
    days_with_supply = tables.Column(verbose_name="Дней с поставкой")
    cost_price = tables.Column(verbose_name="Себестоимость")
    klaster_id = tables.Column(verbose_name="klaster_id")
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        fields = ("offer_id", "image_url", "quantity", "days_to_end", "days_with_supply", "cost_price")
        attrs = {"id": "products_in_supply-table",
                 "class": "table table-striped table-sm small"} 

class Cargo_type_table(tables.Table): 
    type = tables.Column(verbose_name="Тип грузоместа")
    offer_id = tables.Column(verbose_name="Артикул")
    quantity = tables.Column(verbose_name="Количество")
    status = tables.Column(verbose_name="Статус") 
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        fields = ("type", "offer_id", "quantity", "status")
        attrs = {"id": "cargo_type-table",
                 "class": "table table-striped table-sm small"} 


class ProductsTable(tables.Table):
    name = tables.Column(verbose_name="Название товара")
    image_url = tables.TemplateColumn('<img src="{{ record.image_url }}" width="80" height="80" class="img-fluid rounded">',verbose_name="Фото")
    offer_id = tables.Column(verbose_name="Артикул")
    barcode = tables.Column(verbose_name="Баркод")
    total_stock = tables.Column(verbose_name="Остаток")
    total_sold = tables.Column(verbose_name="Продажи")
    realized_by_revenue = tables.Column(verbose_name="Реализовано по выручке(руб)")
    sold_at_cost = tables.Column(verbose_name="Реализовано по себестоимости(руб)")
    days_end = tables.Column(verbose_name="Закончится дней")
    class Meta:
        model = Product
        template_name = "django_tables2/bootstrap4.html"
        fields = ("name","image_url", "offer_id", "barcode", "total_stock", "total_sold", "realized_by_revenue", "sold_at_cost", "days_end")
        attrs = {"id": "products-table",
                 "class": "table table-striped table-sm small"} 
        thead_attrs = {"class": "thead-dark"}  


class RegionTable(tables.Table):
    name = tables.Column(verbose_name="Название",attrs={"td":{ "style": "min-width: 200px; max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;"}})
    offer_id = tables.Column(verbose_name="Артикул")
    image_url = tables.TemplateColumn('<img src="{{ record.image_url }}" width="80" height="80" class="img-fluid rounded">',
        verbose_name="Фото")
    stock_2 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-2"}, "th": {"class": "cluster-2"}})
    sales_per_period_2 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-2"}, "th": {"class": "cluster-2"}})
    seles_per_day_2 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-2"}, "th": {"class": "cluster-2"}})
    days_end_2 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-2"}, "th": {"class": "cluster-2"}})
    min_suply_2 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-2"}, "th": {"class": "cluster-2"}})
    stock_3 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-3"}, "th": {"class": "cluster-3"}})
    sales_per_period_3 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-3"}, "th": {"class": "cluster-3"}})
    seles_per_day_3 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-3"}, "th": {"class": "cluster-3"}})
    days_end_3 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-3"}, "th": {"class": "cluster-3"}})
    min_suply_3 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-3"}, "th": {"class": "cluster-3"}})
    stock_7 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-7"}, "th": {"class": "cluster-7"}})
    sales_per_period_7 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-7"}, "th": {"class": "cluster-7"}})
    seles_per_day_7 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-7"}, "th": {"class": "cluster-7"}})
    days_end_7 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-7"}, "th": {"class": "cluster-7"}})
    min_suply_7 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-7"}, "th": {"class": "cluster-7"}})
    stock_12 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-12"}, "th": {"class": "cluster-12"}})
    sales_per_period_12 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-12"}, "th": {"class": "cluster-12"}})
    seles_per_day_12 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-12"}, "th": {"class": "cluster-12"}})
    days_end_12 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-12"}, "th": {"class": "cluster-12"}})
    min_suply_12 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-12"}, "th": {"class": "cluster-12"}})
    stock_16 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-16"}, "th": {"class": "cluster-16"}})
    sales_per_period_16 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-16"}, "th": {"class": "cluster-16"}})
    seles_per_day_16 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-16"}, "th": {"class": "cluster-16"}})
    days_end_16 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-16"}, "th": {"class": "cluster-16"}})
    min_suply_16 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-16"}, "th": {"class": "cluster-16"}})
    stock_17 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-17"}, "th": {"class": "cluster-17"}})
    sales_per_period_17 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-17"}, "th": {"class": "cluster-17"}})
    seles_per_day_17 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-17"}, "th": {"class": "cluster-17"}})
    days_end_17 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-17"}, "th": {"class": "cluster-17"}})
    min_suply_17 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-17"}, "th": {"class": "cluster-17"}})
    stock_144 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-144"}, "th": {"class": "cluster-144"}})
    sales_per_period_144 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-144"}, "th": {"class": "cluster-144"}})
    seles_per_day_144 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-144"}, "th": {"class": "cluster-144"}})
    days_end_144 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-144"}, "th": {"class": "cluster-144"}})
    min_suply_144 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-144"}, "th": {"class": "cluster-144"}})
    stock_146 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-146"}, "th": {"class": "cluster-146"}})
    sales_per_period_146 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-146"}, "th": {"class": "cluster-146"}})
    seles_per_day_146 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-146"}, "th": {"class": "cluster-146"}})
    days_end_146 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-146"}, "th": {"class": "cluster-146"}})
    min_suply_146 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-146"}, "th": {"class": "cluster-146"}})
    stock_147 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-147"}, "th": {"class": "cluster-147"}})
    sales_per_period_147 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-147"}, "th": {"class": "cluster-147"}})
    seles_per_day_147 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-147"}, "th": {"class": "cluster-147"}})
    days_end_147 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-147"}, "th": {"class": "cluster-147"}})
    min_suply_147 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-147"}, "th": {"class": "cluster-147"}})
    stock_148 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-148"}, "th": {"class": "cluster-148"}})
    sales_per_period_148 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-148"}, "th": {"class": "cluster-148"}})
    seles_per_day_148 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-148"}, "th": {"class": "cluster-148"}})
    days_end_148 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-148"}, "th": {"class": "cluster-148"}})
    min_suply_148 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-148"}, "th": {"class": "cluster-148"}})
    stock_149 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-149"}, "th": {"class": "cluster-149"}})
    sales_per_period_149 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-149"}, "th": {"class": "cluster-149"}})
    seles_per_day_149 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-149"}, "th": {"class": "cluster-149"}})
    days_end_149 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-149"}, "th": {"class": "cluster-149"}})
    min_suply_149 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-149"}, "th": {"class": "cluster-149"}})
    stock_150 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-150"}, "th": {"class": "cluster-150"}})
    sales_per_period_150 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-150"}, "th": {"class": "cluster-150"}})
    seles_per_day_150 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-150"}, "th": {"class": "cluster-150"}})
    days_end_150 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-150"}, "th": {"class": "cluster-150"}})
    min_suply_150 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-150"}, "th": {"class": "cluster-150"}})
    stock_151 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-151"}, "th": {"class": "cluster-151"}})
    sales_per_period_151 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-151"}, "th": {"class": "cluster-151"}})
    seles_per_day_151 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-151"}, "th": {"class": "cluster-151"}})
    days_end_151 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-151"}, "th": {"class": "cluster-151"}})
    min_suply_151 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-151"}, "th": {"class": "cluster-151"}})
    stock_152 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-152"}, "th": {"class": "cluster-152"}})
    sales_per_period_152 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-152"}, "th": {"class": "cluster-152"}})
    seles_per_day_152 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-152"}, "th": {"class": "cluster-152"}})
    days_end_152 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-152"}, "th": {"class": "cluster-152"}})
    min_suply_152 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-152"}, "th": {"class": "cluster-152"}})
    stock_153 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-153"}, "th": {"class": "cluster-153"}})
    sales_per_period_153 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-153"}, "th": {"class": "cluster-153"}})
    seles_per_day_153 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-153"}, "th": {"class": "cluster-153"}})
    days_end_153 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-153"}, "th": {"class": "cluster-153"}})
    min_suply_153 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-153"}, "th": {"class": "cluster-153"}})
    stock_154 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-154"}, "th": {"class": "cluster-154"}})
    sales_per_period_154 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-154"}, "th": {"class": "cluster-154"}})
    seles_per_day_154 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-154"}, "th": {"class": "cluster-154"}})
    days_end_154 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-154"}, "th": {"class": "cluster-154"}})
    min_suply_154 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-154"}, "th": {"class": "cluster-154"}})
    stock_155 = tables.Column(verbose_name="Остаток", attrs={"td": {"class": "cluster-155"}, "th": {"class": "cluster-155"}})
    sales_per_period_155 = tables.Column(verbose_name="Продаж за период", attrs={"td": {"class": "cluster-155"}, "th": {"class": "cluster-155"}})
    seles_per_day_155 = tables.Column(verbose_name="Продаж в день", attrs={"td": {"class": "cluster-155"}, "th": {"class": "cluster-155"}})
    days_end_155 = tables.Column(verbose_name="Закончится дней", attrs={"td": {"class": "cluster-155"}, "th": {"class": "cluster-155"}})
    min_suply_155 = tables.Column(verbose_name="Минимально поставить", attrs={"td": {"class": "cluster-155"}, "th": {"class": "cluster-155"}})
    class Meta:
        attrs = {'class': 'table table-bordered'}
        sequence = ('name', 'offer_id', 'image_url',
                    'stock_2', 'sales_per_period_2', 'seles_per_day_2', 'days_end_2', 'min_suply_2', 
                    'stock_3', 'sales_per_period_3', 'seles_per_day_3', 'days_end_3', 'min_suply_3',
                    'stock_7', 'sales_per_period_7', 'seles_per_day_7', 'days_end_7', 'min_suply_7',
                    'stock_12', 'sales_per_period_12', 'seles_per_day_12', 'days_end_12', 'min_suply_12',
                    'stock_16', 'sales_per_period_16', 'seles_per_day_16', 'days_end_16', 'min_suply_16',
                    'stock_17', 'sales_per_period_17', 'seles_per_day_17', 'days_end_17', 'min_suply_17',
                    'stock_144', 'sales_per_period_144', 'seles_per_day_144', 'days_end_144', 'min_suply_144',
                    'stock_146', 'sales_per_period_146', 'seles_per_day_146', 'days_end_146', 'min_suply_146',
                    'stock_147', 'sales_per_period_147', 'seles_per_day_147', 'days_end_147', 'min_suply_147',
                    'stock_148', 'sales_per_period_148', 'seles_per_day_148', 'days_end_148', 'min_suply_148',
                    'stock_149', 'sales_per_period_149', 'seles_per_day_149', 'days_end_149', 'min_suply_149',
                    'stock_150', 'sales_per_period_150', 'seles_per_day_150', 'days_end_150', 'min_suply_150',
                    'stock_151', 'sales_per_period_151', 'seles_per_day_151', 'days_end_151', 'min_suply_151',
                    'stock_152', 'sales_per_period_152', 'seles_per_day_152', 'days_end_152', 'min_suply_152',
                    'stock_153', 'sales_per_period_153', 'seles_per_day_153', 'days_end_153', 'min_suply_153',
                    'stock_154', 'sales_per_period_154', 'seles_per_day_154', 'days_end_154', 'min_suply_154',
                    'stock_155', 'sales_per_period_155', 'seles_per_day_155', 'days_end_155', 'min_suply_155', 
                    )
        attrs = {"id": "region-table",
                 "class": "table table-striped table-sm small"} 
        thead_attrs = {}
        template_name = "django_tables2/bootstrap4.html"