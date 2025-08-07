from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ozon_client_id = models.CharField(max_length=50)
    ozon_api_key = models.CharField(max_length=100)
    ozon_base_url = models.CharField(max_length=100, default="https://api-seller.ozon.ru")
    data_initialized = models.BooleanField(default=False)
    data_initialization_error = models.TextField(blank=True, null=True)

    def get_initialization_status(self):
        if self.data_initialized:
            return "completed"
        if self.data_initialization_error:
            return f"failed: {self.data_initialization_error}"
        return "pending"
    
    def __str__(self):
        return f"Профиль {self.user.username}"

class Input_data(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='input_data')
    driver_name = models.CharField(max_length=255, null=True, blank=True)  # ФИО водителя
    driver_mobilephone = models.CharField(max_length=20, null=True, blank=True)  # Номер телефона водителя
    car_brand = models.CharField(max_length=100, null=True, blank=True)  # Марка машины
    car_number = models.CharField(max_length=20, null=True, blank=True)  # Номер машины (гос. номер)
    car_max_weight = models.FloatField(null=True, blank=True)  # Максимальный вес в кг
    car_max_capacity = models.FloatField(null=True, blank=True)  # Максимальная вместимость машины в м³
    name_shipping_point = models.CharField(max_length=255, null=True, blank=True)  # Название точки отгрузки кроссдок
    type_shipping_point = models.CharField(max_length=50, choices=[('ПВЗ', 'ПВЗ'), ('ППЗ', 'ППЗ'), ('СЦ', 'СЦ')], null=True, blank=True)  # Тип точки отгрузки
    top_up_remaining_days = models.PositiveIntegerField(null=True, blank=True)  # Пополнять остаток дней
    supply_on = models.PositiveIntegerField(null=True, blank=True)  # Поставлять на дней
    class Meta:
        db_table = 'personalproject_input_data'
        verbose_name = 'Водимые данные'
        verbose_name_plural = 'Водимые данные'

    def __str__(self):
        return self.name
class Product(models.Model):
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='products'
    )
    ozon_product_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    sku = models.BigIntegerField(
        verbose_name='SKU из Ozon',
        null=True,
        blank=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    offer_id = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2)
    depth = models.DecimalField(max_digits=10, decimal_places=2)
    width = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    weight_unit = models.CharField(max_length=10)
    dimension_unit = models.CharField(max_length=10)
    image_url = models.URLField(max_length=255)
    model = models.CharField(max_length=100, blank=True, null=True)
    product_zone = models.CharField(max_length=50, blank=True, null=True) #зона размещения товара
    europallet = models.IntegerField(blank=True, null=True)
    box_type = models.CharField(max_length=5, blank=True, null=True)
    box_xl = models.IntegerField(blank=True, null=True)
    box_l = models.IntegerField(blank=True, null=True)
    box_m = models.IntegerField(blank=True, null=True)
    box_s = models.IntegerField(blank=True, null=True)
    fit_from = models.DateTimeField(blank=True, null=True) # годен от 
    fit_to = models.DateTimeField(blank=True, null=True)# годен до
    cost_price  = models.IntegerField(blank=True, null=True)# себестоимость

    class Meta:
        db_table = 'personalproject_product'
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

class Price(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    marketing_price = models.DecimalField(max_digits=10, decimal_places=2)
    marketing_seller_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    retail_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat = models.DecimalField(max_digits=5, decimal_places=2)
    currency_code = models.CharField(max_length=10, default='RUB')

    class Meta:
        db_table = 'personalproject_prices'
        verbose_name = 'Цена'
        verbose_name_plural = 'Цены'

class Stock(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='stocks',
    )
    warehouse_name = models.CharField(max_length=255)
    valid_stock_count = models.IntegerField()
    sku = models.IntegerField()
    klaster_id = models.IntegerField(verbose_name='ID кластера', null=True, blank=True, db_index=True)
    class Meta:
        db_table = 'personalproject_stock'
        verbose_name = 'Складской остаток'
        verbose_name_plural = 'Складские остатки'


class Sales_analysis(models.Model):
    user = models.ForeignKey(
        'auth.User',  # Используем стандартную модель пользователя
        on_delete=models.CASCADE,
        related_name='sales_analyses'
    )
    supply_name = models.CharField(max_length=30, null=True)
    type_supply = models.CharField(max_length=12, null=True)
    shipping_point = models.CharField(max_length=30, null=True)  #  
    region_destination = models.CharField(max_length=30, null=True) #klaster_names
    warehouse_name = models.CharField(max_length=50, null=True) # для кроссдока
    top_up_the_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    put_days = models.DecimalField(max_digits=10, decimal_places=2, default=30,  null=True)
    name_driver = models.CharField(max_length=50, null=True)
    driver_mobile_number = models.CharField(max_length=15, null=True)
    car_mark = models.CharField(max_length=30, null=True)
    car_number = models.CharField(max_length=20, null=True, blank=True)
    tc_number = models.CharField(max_length=10, null=True)
    capacity = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    klaster_id = models.IntegerField(verbose_name='ID кластера', null=True, blank=True)

    class Meta:
        db_table = "sales_analysis"

class Sale(models.Model): 
    '''продажи за период'''
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    order_id = models.BigIntegerField()
    status = models.CharField(max_length=50)
    created_at = models.DateTimeField()
    order_number = models.CharField(max_length=25, null=True, blank=True)
    posting_number = models.CharField(max_length=25,null=True, blank=True)
    sku = models.BigIntegerField()
    #warehouse_id = models.BigIntegerField(verbose_name='ID склада', null=True, blank=True)
    klaster_id = models.IntegerField(verbose_name='ID кластера', null=True, blank=True)
    name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    offer_id = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    klaster_name = models.CharField(max_length=255, verbose_name='Название кластера', null=True, blank=True)

    class Meta:
        db_table = 'personalproject_sales'
        verbose_name = 'Продажа'
        verbose_name_plural = 'Продажи'

    def __str__(self):
        return f"{self.order_id} - {self.name}"


class Warehouse(models.Model):
    warehouse_id = models.BigIntegerField(verbose_name='ID склада', null=True, blank=True, db_index=True)
    warehouse_name = models.CharField(max_length=255, verbose_name='Название склада', null=True, blank=True)
    klaster_id = models.IntegerField(verbose_name='ID кластера', null=True, blank=True)
    klaster_name = models.CharField(max_length=255, verbose_name='Название кластера', null=True, blank=True)
    class Meta:
        db_table = 'personalproject_warehouses'
        verbose_name = 'Склады'
        verbose_name_plural = 'Склады'

    def __str__(self):
        return f"{self.warehouse_name} (ID: {self.warehouse_id})"
    
############################## ПОСТАВКИ ШАГ 2 ##############################
from django.db import models
from django.contrib.auth.models import User

class SupplyOperation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supply_operations')
    uid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Supply(models.Model):
    """Модель поставки"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='supplies')
    operation = models.ForeignKey(SupplyOperation, on_delete=models.CASCADE, related_name='supplies')
    supply_status = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100)
    shipping_point = models.CharField(max_length=100)
    region_name = models.CharField(max_length=100)
    klaster_id = models.IntegerField()
    warehouse = models.CharField(max_length=100)
    type_supply = models.CharField(max_length=100)

    sku_count = models.PositiveIntegerField()
    units_count = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.DecimalField(max_digits=10, decimal_places=3)
    mono_pallets = models.PositiveIntegerField()
    mix_pallets = models.PositiveIntegerField()
    mix_boxes = models.PositiveIntegerField()

    draft = models.CharField(max_length=100, null=True, blank=True)
    draft_id  = models.CharField(max_length=100, null=True, blank=True)
    draft_create_operation_id = models.CharField(max_length=100, null=True, blank=True)

    drop_off_warehouse_id = models.BigIntegerField(null=True, blank=True)
    delivery_time_from = models.DateTimeField(null=True, blank=True)
    delivery_time_to = models.DateTimeField(null=True, blank=True)

    create_supply_from_draft_operation_id = models.CharField(max_length=100, null=True, blank=True)
    supply_id = models.BigIntegerField(null=True, blank=True)

    cargo_create_operation_id = models.CharField(max_length=100, null=True, blank=True)  

    created_at = models.DateTimeField(auto_now_add=True)

class SupplyProduct(models.Model):
    """Товары в поставке"""
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='products')
    klaster_id = models.IntegerField()
    product_offer_id = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    cost_price = models.DecimalField(max_digits=15, decimal_places=2)
    sales_sum = models.DecimalField(max_digits=20, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.DecimalField(max_digits=10, decimal_places=3)

class CargoItem(models.Model):
    """Грузоместо товара в поставке"""
    supply = models.ForeignKey(Supply, on_delete=models.CASCADE, related_name='cargo_items')
    product_offer_id = models.CharField(max_length=100)
    cargo_type = models.CharField(max_length=100)  # Короб XL, L, M, S, Моно, Микс и т.п.
    total_quantity_in_cargo = models.PositiveIntegerField()
    cargo_count = models.PositiveIntegerField()

############################## ПОСТАВКИ ШАГ 2 ##############################