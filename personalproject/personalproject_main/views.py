from itertools import islice
import uuid, time, math, requests, json, uuid, logging, os
from django.template.loader import render_to_string
from collections import defaultdict
from django.shortcuts import get_object_or_404, render, redirect
from .models import Product, Stock, Sales_analysis, Input_data, Sale, UserProfile, SupplyOperation, Supply, SupplyProduct, CargoItem, Warehouse
from .tables import StockTable, SalesAnalysisTable,  UrgentProductsTable, NormalProductsTable, DriversTable, VehiclesTable, ShippingPointTable, KlasterTable, ProductTable, ReferenceTable,  ProductsTable, RegionTable, Total_supply_table, Products_in_supply, Cargo_type_table
from django.views.generic import TemplateView
from django_tables2.views import SingleTableView
import django_tables2 as tables
from django_tables2 import RequestConfig, SingleTableView,Table, Column
from django.contrib.auth import login, authenticate, logout
from .forms import RegistrationForm, LoginForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .ozon_api.ozon_api import fetch_ozon_sales, calculate_sales_stats
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from .ozon_api.update_data_api import OzonAPI
from django.db.models import Sum, Q
from decimal import Decimal
from django.db import transaction
from django.views.decorators.http import require_POST



os.environ['TZ'] = 'Europe/Moscow'
time.tzset()

logging.basicConfig(
    format="{asctime} [{levelname}] - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.INFO
)


def custom_404(request, exception):
    return render(request, "personalproject/errors/404.html", status=404)

def custom_500(request):
    return render(request, "personalproject/errors/500.html", status=500)

def custom_403(request, exception):
    return render(request, "personalproject/errors/403.html", status=403)

def custom_400(request, exception):
    return render(request, "personalproject/errors/400.html", status=400)

@login_required
def base_redirect(request):
    return redirect("products")

@method_decorator(login_required, name='dispatch')
class ProductListView(TemplateView):
    template_name = "personalproject/supply/product_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        since_str = self.request.GET.get('since')
        to_str = self.request.GET.get('to')

        since_date, to_date = self._parse_dates(since_str, to_str)

        since_str = since_date.strftime('%Y-%m-%d')
        to_str = to_date.strftime('%Y-%m-%d')

        urgent, normal = calculate_sales_stats(self.request.user, since_date, to_date)

        moved_ids = self.request.GET.getlist('move_ids')
        table_name = self.request.GET.get('table_name')

        if moved_ids and table_name:
            if table_name == "Срочные":
                for product_id in moved_ids:
                    move_product_between_lists(product_id, urgent, normal)
            elif table_name == "Плановые":
                for product_id in moved_ids:
                    move_product_between_lists(product_id, normal, urgent)
        self.request.session["urgent_data"] = urgent
        self.request.session["normal_data"] = normal
        context.update({
            "sales_table": SalesAnalysisTable(Sales_analysis.objects.filter(user=self.request.user)),
            "urgent_table": UrgentProductsTable(urgent),
            "normal_table": NormalProductsTable(normal),
            'selected_since': since_str,
            'selected_to': to_str,
        })

        return context

    def _parse_dates(self, since_str, to_str):
        try:
            if since_str and to_str:
                since_date = datetime.strptime(since_str, '%Y-%m-%d')
                to_date = datetime.strptime(to_str, '%Y-%m-%d')
            else:
                to_date = timezone.now()
                since_date = to_date - timedelta(days=45)

            since_date = make_aware(since_date.replace(hour=0, minute=0, second=0))
            to_date = make_aware(to_date.replace(hour=23, minute=59, second=59))
            return since_date, to_date

        except (ValueError, TypeError):
            to_date = timezone.now()
            since_date = to_date - timedelta(days=45)
            return since_date, to_date

    def post(self, request, *args, **kwargs):
        if 'update_sales' in request.POST:
            pass
        return self.get(request, *args, **kwargs)

class StockListView(SingleTableView):
    model = Stock
    table_class = StockTable
    template_name = "personalproject/supply/stock_list.html"

    def get_queryset(self):
        product = get_object_or_404(Product, pk=self.kwargs["pk"],  user=self.request.user)
        return product.stocks.all()

def register_view(request):
    if request.method == 'POST':
        user_form = RegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST)

        api_key = request.POST.get('ozon_api_key')
        seller_id = request.POST.get('ozon_client_id')

        if not api_key or not seller_id:
            return HttpResponse("API ключ и Seller ID обязательны.", status=400)

        ozon_api_url = 'https://api-seller.ozon.ru/v3/product/list'
        headers = {
            'Client-Id': seller_id,
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            "filter": {},
            "last_id": "",
            "limit": 1
        }

        response = requests.post(ozon_api_url, json=payload, headers=headers)

        if response.status_code != 200:
            messages.error(request, f"Ошибка запроса к Ozon API: {response.status_code}")
        if not user_form.is_valid() or not profile_form.is_valid():
            messages.error(request, f"Произошла ошибка при регистрации")
            logging.error("Ошибки валидации:")
            logging.error(user_form.errors)
            logging.error(profile_form.errors)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.ozon_client_id = seller_id
            profile.ozon_api_key = api_key
            profile.save()
            Input_data.objects.create(
                user=user,
                driver_name="",
                driver_mobilephone="",
                car_brand="",
                car_number="",
                car_max_weight=0,
                car_max_capacity=0,
                name_shipping_point="",
                type_shipping_point="",
                top_up_remaining_days=0,
                supply_on=0
            )
            clusters = [
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Санкт-Петербург и СЗО", "klaster_id": 2},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Урал", "klaster_id": 3},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Дальний Восток", "klaster_id": 7},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Калининград", "klaster_id": 12},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Воронеж", "klaster_id": 16},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Краснодар", "klaster_id": 17},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Тюмень", "klaster_id": 144},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Волгоград", "klaster_id": 146},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Ростов", "klaster_id": 147},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Уфа", "klaster_id": 148},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Казань", "klaster_id": 149},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Самара", "klaster_id": 150},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Новосибирск", "klaster_id": 151},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Омск", "klaster_id": 152},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Кавказ", "klaster_id": 153},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Москва, МО и Дальние регионы", "klaster_id": 154},
                {"type_supply": "Кроссдокинг", "shipping_point": "ПВЗ", "klaster_name": "Красноярск", "klaster_id": 155},
            ]

            Sales_analysis.objects.bulk_create([
                Sales_analysis(
                    user=user,
                    region_destination=cluster["klaster_name"],
                    klaster_id=cluster["klaster_id"]
                ) for cluster in clusters
            ])
            try:
                ozon_api = OzonAPI(profile)
                ozon_api.update_all_data()
                ozon_api.update_attributes_for_existing()
                profile.data_initialized = True
                profile.save()
            except Exception as e:
                profile.data_initialization_error = str(e)
                profile.save()
                messages.error(request, "Произошла ошибка при инициализации данных с Ozon. Проверьте API ключ и Client ID.")
                return redirect('registration')

            login(request, user)

            return redirect('products')

        return render(request, 'personalproject/registration/registration.html',
                      {'user_form': user_form, 'profile_form': profile_form})

    user_form = RegistrationForm()
    profile_form = ProfileForm()
    return render(request, 'personalproject/registration/registration.html',
                  {'user_form': user_form, 'profile_form': profile_form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect('products')
            else:
                messages.error(request, "Неверный логин или пароль")
        return render(request, 'personalproject/registration/login.html', {'form': form})
    form = LoginForm()
    return render(request, 'personalproject/registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


@require_POST
@csrf_protect
def update_sales_analysis(request, pk):
    obj = get_object_or_404(Sales_analysis, pk=pk)

    editable_fields = [
        "supply_name",
        "type_supply",
        "shipping_point",
        "warehouse_name",
        "top_up_the_balance",
        "put_days",
        "name_driver",
        "driver_mobile_number",
        "car_mark",
        "car_number",
        "capacity",
        "weight"
    ]

    for field in editable_fields:
        if field in request.POST:
            setattr(obj, field, request.POST[field])

    obj.save()
    return HttpResponse(status=204)

@login_required
def import_ozon_sales(request):
    value = "supply_st_1" 

    if request.method == 'GET':
        since_str = request.GET.get('since')
        to_str = request.GET.get('to')

        if not since_str or not to_str:
            messages.error(request, "Необходимо выбрать обе даты")
            return redirect(f'/products/?since={since_str}&to={to_str}')

        try:
            since_date = datetime.strptime(since_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_str, '%Y-%m-%d')

            logging.info(f"Параметры since: {since_str}, to: {to_str}")

            since_date = timezone.make_aware(since_date)
            to_date = timezone.make_aware(to_date)

            logging.info(f"Преобразованные даты: {since_date} - {to_date}")

            if since_date > to_date:
                messages.error(request, "Дата начала не может быть больше даты окончания")
                return redirect(f'/products/?since={since_str}&to={to_str}')

            if to_date > timezone.now():
                messages.error(request, "Дата окончания не может быть в будущем")
                return redirect(f'/products/?since={since_str}&to={to_str}')

            if (to_date - since_date).days > 46:
                messages.error(request, "Максимальный период выборки - 45 дней")
                return redirect(f'/products/?since={since_str}&to={to_str}')

            processed = fetch_ozon_sales(request.user, since_date, to_date, value)
            logging.info(f"Успешно обработано записей: {processed}")

        except ValueError:
            messages.error(request, "Неверный формат даты")
            return redirect(f'/products/?since={since_str}&to={to_str}')

        try:
            processed = fetch_ozon_sales(request.user, since_date, to_date, value)

        except Exception as e:
            messages.error(request, f"Ошибка импорта: {str(e)}")
        return redirect(f'/products/?since={since_str}&to={to_str}')

@csrf_exempt
def change_table(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            selected_ids = data.get("selected_ids", [])
            table_name = data.get("table_name", "")

            if not selected_ids:
                return JsonResponse({"success": False, "error": "Нет выбранных товаров"}, status=400)

            urgent = request.session.get("urgent_data", [])
            normal = request.session.get("normal_data", [])

            if table_name == "Срочные":
                from_list, to_list = urgent, normal
            elif table_name == "Плановые":
                from_list, to_list = normal, urgent
            else:
                return JsonResponse({"success": False, "error": "Неподдерживаемая таблица"}, status=400)

            moved = 0
            for product_id in selected_ids:
                if move_product_between_lists(product_id, from_list, to_list):
                    moved += 1

            request.session["urgent_data"] = urgent
            request.session["normal_data"] = normal

            updated_urgent = UrgentProductsTable(urgent).as_html(request)
            updated_normal = NormalProductsTable(normal).as_html(request)

            return JsonResponse({
                "success": True,
                "moved": moved,
                "urgent_table": updated_urgent,
                "normal_table": updated_normal
            })

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Ошибка обработки JSON"}, status=400)

    return JsonResponse({"success": False, "error": "Метод не разрешён"}, status=405)

def move_product_between_lists(product_id, from_list, to_list):
    for product in from_list:
        if product["id"] == product_id:
            from_list.remove(product)
            to_list.append(product)
            logging.info(f"Товар {product_id} перемещён в другую таблицу.")
            return True
    return False

@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = "personalproject/profile/profile_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        drivers_table = DriversTable(Sales_analysis.objects.filter(user=user))
        RequestConfig(self.request, paginate={"per_page": 4}).configure(drivers_table)
        context["DriversTable"] = drivers_table

        context["VehiclesTable"] = VehiclesTable(Sales_analysis.objects.filter(user=user))
        context["ShippingPointTable"] = ShippingPointTable(Input_data.objects.filter(user=user))
        context["KlasterTable"] = KlasterTable(Sales_analysis.objects.filter(user=user))
        context["ProductTable"] = ProductTable(Product.objects.filter(user=user))
        return context

def update_shipping_point_table(request, pk):
    if request.method == "POST":
        obj = get_object_or_404(Input_data, pk=pk)

        new_value = request.POST.get("type_shipping_point")
        if new_value in ["ПВЗ", "ППЗ", "СЦ"]:
            obj.type_shipping_point = new_value
            obj.save()

            return HttpResponse(f'''
            <select name="type_shipping_point" class="form-control"
                    hx-post="{request.path}"
                    hx-trigger="change delay:500ms"
                    hx-target="this"
                    hx-swap="outerHTML">
                <option value="ПВЗ" {'selected' if obj.type_shipping_point == "ПВЗ" else ''}>ПВЗ</option>
                <option value="ППЗ" {'selected' if obj.type_shipping_point == "ППЗ" else ''}>ППЗ</option>
                <option value="СЦ" {'selected' if obj.type_shipping_point == "СЦ" else ''}>СЦ</option>
            </select>
            ''')

    return JsonResponse({"success": False}, status=400)


@method_decorator(login_required, name='dispatch')
class ReferenceView(TemplateView):
    template_name = "personalproject/reference/reference_page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["ReferenceTable"] = ReferenceTable(Product.objects.filter(user=user))
        return context

def update_refernce_table(request, pk):
     if request.method == "POST":
         obj = get_object_or_404(Product, pk=pk)

         for field in ["model", "europallet","box_type", "box_xl", "box_l", "box_m", "box_s", "fit_from", "fit_to", "cost_price"]:
             if field in request.POST:
                 setattr(obj, field, request.POST[field])

         obj.save()
         return JsonResponse({"success": True})

     return JsonResponse({"success": False}, status=400)

@method_decorator(login_required, name='dispatch')
class GoodsView(TemplateView):
    template_name = "personalproject/goods/goods.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        since_str = self.request.GET.get('since')
        to_str = self.request.GET.get('to')
        name = self.request.GET.get("name")
        article = self.request.GET.get("article")

        if since_str and to_str:
            try:
                since_date = timezone.make_aware(datetime.strptime(since_str, '%Y-%m-%d'))
                to_date = timezone.make_aware(datetime.strptime(to_str, '%Y-%m-%d'))
            except ValueError:
                since_date = timezone.now() - timedelta(days=45)
                to_date = timezone.now()
        else:
            since_date = timezone.now() - timedelta(days=45)
            to_date = timezone.now()

        queryset = Product.objects.filter(user=user).values("name", "offer_id", "barcode", "image_url")
        queryset = queryset.annotate(
            total_stock=Sum(
                'stocks__valid_stock_count',
                filter=Q(stocks__product__user=user)
            )
        )

        if name:
            queryset = queryset.filter(name__icontains=name)
        if article:
            queryset = queryset.filter(offer_id__icontains=article)

        sales = list(
            Sale.objects
            .filter(
                user=user,
                created_at__range=(since_date, to_date)
            )
            .values('offer_id', 'klaster_id')
            .annotate(total_sold=Sum('quantity'), realized_by_revenue=Sum('price'))
        )

        sales_dict = {}
        price_dict = {}
        for sale in sales:
            offer_id = sale['offer_id']
            if offer_id in sales_dict:
                sales_dict[offer_id] += sale['total_sold']
                price_dict[offer_id] += sale['realized_by_revenue']
            else:
                sales_dict[offer_id] = sale['total_sold']
                price_dict[offer_id] = sale['realized_by_revenue']

        period_days = max((to_date - since_date).days, 1)
        merged_data = []
        for product in queryset:
            offer_id = product["offer_id"]
            product["total_sold"] = sales_dict.get(offer_id, 0)
            product["realized_by_revenue"] = price_dict.get(offer_id, 0)

            avg_sales = product["total_sold"] / period_days if period_days > 0 else 0
            total_stock = product["total_stock"] if product["total_stock"] is not None else 0
            days_left = total_stock / avg_sales if avg_sales > 0 else float('inf')

            cost_price = Product.objects.filter(offer_id=offer_id, user=user).values_list("cost_price", flat=True).first() or 0
            product["sold_at_cost"] = cost_price * product["total_sold"]

            product["days_end"] = round(days_left, 1)

            # image_url уже есть в queryset, если что - fallback
            product["image_url"] = product.get("image_url") or ""

            merged_data.append(product)

        table = ProductsTable(merged_data)
        RequestConfig(self.request).configure(table)

        if name or article:
            sales_data = (
                Sale.objects
                .filter(
                    user=user,
                    created_at__range=(since_date, to_date),
                    name__icontains=name,
                    offer_id__icontains=article
                )
                .values('created_at__date')
                .annotate(total_sold=Sum('quantity'))
                .order_by('created_at__date')
            )
        else:
            sales_data = (
                Sale.objects
                .filter(
                    user=user,
                    created_at__range=(since_date, to_date),
                )
                .values('created_at__date')
                .annotate(total_sold=Sum('quantity'))
                .order_by('created_at__date')
            )

        labels = [str(entry['created_at__date'].strftime('%Y-%m-%d')) for entry in sales_data]
        values = [entry['total_sold'] for entry in sales_data]

        context.update({
            "products_table": table,
            "since": since_date.strftime('%Y-%m-%d'),
            "to": to_date.strftime('%Y-%m-%d'),
            'labels': json.dumps(labels),
            'values': json.dumps(values)
        })

        return context

@login_required
def get_sales_for_goods(request): 
    value = "get_sales_for_goods"  

    if request.method == 'GET':
        since_str = request.GET.get('since')
        to_str = request.GET.get('to')
        name = request.GET.get("name")
        article = request.GET.get("article")

        if not since_str or not to_str:
            to_date = timezone.now()
            since_date = to_date - timedelta(days=45)
            since_str = since_date.strftime('%Y-%m-%d')
            to_str = to_date.strftime('%Y-%m-%d')

        if not since_str or not to_str:
            messages.error(request, "Необходимо выбрать обе даты")
            return redirect("goods")  

        try:
            since_date = datetime.strptime(since_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_str, '%Y-%m-%d')

            logging.info(f"Параметры since: {since_str}, to: {to_str}")

            since_date = timezone.make_aware(since_date)
            to_date = timezone.make_aware(to_date)

            logging.info(f"Преобразованные даты: {since_date} - {to_date}")

            if since_date > to_date:
                messages.error(request, "Дата начала не может быть больше даты окончания")
                return redirect("goods")

            if to_date > timezone.now():
                messages.error(request, "Дата окончания не может быть в будущем")
                return redirect("goods")

            if (to_date - since_date).days > 125:
                messages.error(request, "Максимальный период выборки - 120 дней")
                return redirect("goods")

            processed = fetch_ozon_sales(request.user, since_date, to_date, value)
            messages.success(request, f"Успешно обработано {processed} записей")

        except ValueError:
            messages.error(request, "Неверный формат даты")
            return redirect("goods")

        except Exception as e:
            messages.error(request, f"Ошибка импорта: {str(e)}")
            return redirect("goods")
        return redirect(f"/goods/?since={since_str}&to={to_str}&name={name}&article={article}&sort=-total_sold")


@method_decorator(login_required, name='dispatch')
class RegionsView(TemplateView):
    template_name = "personalproject/regions/regions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        since_str = self.request.GET.get('since')
        to_str = self.request.GET.get('to')
        name = self.request.GET.get("name", "").strip()
        article = self.request.GET.get("article", "").strip()
        reg_filter = self.request.GET.get("reg_filter", "all").strip()

        try:
            since_date = timezone.make_aware(datetime.strptime(since_str, '%Y-%m-%d'))
            to_date = timezone.make_aware(datetime.strptime(to_str, '%Y-%m-%d'))
        except (ValueError, TypeError):
            since_date = timezone.now() - timedelta(days=45)
            to_date = timezone.now()

        period_days = max((to_date - since_date).days, 1)

        regions = {
            "2": "Санкт-Петербург и СЗО",
            "3": "Урал",
            "7": "Дальний Восток",
            "12": "Калининград",
            "16": "Воронеж",
            "17": "Краснодар",
            "144": "Тюмень",
            "146": "Волгоград",
            "147": "Ростов",
            "148": "Уфа",
            "149": "Казань",
            "150": "Самара",
            "151": "Новосибирск",
            "152": "Омск",
            "153": "Кавказ",
            "154": "Москва, МО и Дальние регионы",
            "155": "Красноярск"
        }

        selected_regions = (
            list(regions.keys())
            if reg_filter.lower() == "all"
            else [r.strip() for r in reg_filter.split(",") if r.strip() in regions]
        )

        stocks_query = Stock.objects.filter(product__user=user)
        if article:
            stocks_query = stocks_query.filter(product__offer_id=article)
        if name:
            stocks_query = stocks_query.filter(product__name__icontains=name)

        stocks = stocks_query.values(
            'product__id',
            'product__name',
            'product__offer_id',
            'product__image_url',
            'klaster_id'
        ).annotate(total_stock=Sum('valid_stock_count'))

        sales_query = Sale.objects.filter(
            user=user,
            created_at__range=(since_date, to_date),
        )
        if article:
            sales_query = sales_query.filter(offer_id=article)
        if name:
            sales_query = sales_query.filter(name__icontains=name)

        sales = sales_query.values(
            'product__id',
            'klaster_id'
        ).annotate(total_sold=Sum('quantity'))

        # Получаем put_days по всем кластерам сразу
        put_days_by_klaster = {
            str(entry.klaster_id): (entry.put_days if entry.put_days is not None else 45)
            for entry in Sales_analysis.objects.filter(user=user)
        }

        products_data = {}

        for stock in stocks:
            product_id = stock['product__id']
            product_info = products_data.setdefault(product_id, {
                'name': stock['product__name'],
                'offer_id': stock['product__offer_id'],
                'image_url': stock['product__image_url'],
                'regions': {}
            })
            region_id = str(stock['klaster_id'])
            product_info['regions'][region_id] = {
                'stock': stock['total_stock'],
                'sales_per_period': 0,
                'sales_per_day': 0,
                'days_end': 0,
                'min_suply': 0
            }

        for sale in sales:
            product_id = sale['product__id']
            region_id = str(sale['klaster_id'])
            total_sold = sale['total_sold']

            if product_id in products_data and region_id in products_data[product_id]['regions']:
                region_data = products_data[product_id]['regions'][region_id]
                region_data['sales_per_period'] = total_sold
                region_data['sales_per_day'] = total_sold / period_days if period_days else 0
                region_data['days_end'] = region_data['stock'] / region_data['sales_per_day'] if region_data['sales_per_day'] else 0

                put_days = int(put_days_by_klaster.get(region_id, 45))

                region_data['min_suply'] = max(0, region_data['sales_per_day'] * put_days)

        table_data = []
        for product_id, product in products_data.items():
            row = {
                'name': product['name'],
                'offer_id': product['offer_id'],
                'image_url': product['image_url']
            }
            for region_id in regions:
                region_data = product['regions'].get(region_id, {})
                row.update({
                    f'stock_{region_id}': region_data.get('stock', 0),
                    f'sales_per_period_{region_id}': region_data.get('sales_per_period', 0),
                    f'seles_per_day_{region_id}': round(region_data.get('sales_per_day', 0), 1),
                    f'days_end_{region_id}': round(region_data.get('days_end', 0), 1),
                    f'min_suply_{region_id}': round(region_data.get('min_suply', 0))
                })
            table_data.append(row)

        DynamicRegionTable = generate_region_table(selected_regions)
        context['region_table'] = DynamicRegionTable(table_data)

        charts_data = []
        for region_id in selected_regions:
            region_name = regions.get(region_id, "Unknown Region")

            region_sales = sales_query.filter(
                klaster_id=region_id
            ).values('created_at__date').annotate(
                total_sold=Sum('quantity')
            ).order_by('created_at__date')

            total_stock = stocks.filter(klaster_id=region_id).aggregate(
                total=Sum('total_stock')
            )['total'] or 0

            total_sold = sales.filter(klaster_id=region_id).aggregate(
                total=Sum('total_sold')
            )['total'] or 0

            avg_sales = total_sold / period_days if period_days > 0 else 0
            days_left = round(total_stock / avg_sales, 1) if avg_sales > 0 else 0

            charts_data.append({
                "region_id": region_id,
                "region_name": region_name,
                "labels": [entry['created_at__date'].strftime('%m-%d') for entry in region_sales],
                "data": [entry['total_sold'] for entry in region_sales],
                "total_stock": total_stock,
                "days_end": days_left
            })

        context.update({
            "since": since_date.strftime('%Y-%m-%d'),
            "to": to_date.strftime('%Y-%m-%d'),
            "charts_data": charts_data,
            "regions": regions,
            "selected_regions": selected_regions
        })

        return context

def generate_region_table(selected_regions):
    class DynamicRegionTable(Table):
        name = tables.Column(verbose_name="Название",attrs={"td":{ "style": "min-width: 200px; max-width: 300px;  overflow: hidden; text-overflow: ellipsis;"}})
        offer_id = Column(verbose_name="Артикул")
        image_url = tables.TemplateColumn('<img src="{{ record.image_url }}" width="80" height="80" class="img-fluid rounded">',
        verbose_name="Фото")

        class Meta:
            template_name = "django_tables2/bootstrap4.html"
            attrs = {"class": "table table-striped table-sm small"}

    for region_id in selected_regions:
        DynamicRegionTable.base_columns[f'stock_{region_id}'] = Column(verbose_name="Остаток", attrs={"td": {"class": f"cluster-{region_id}"}})
        DynamicRegionTable.base_columns[f'sales_per_period_{region_id}'] = Column(verbose_name="Продаж за период", attrs={"td": {"class": f"cluster-{region_id}"}})
        DynamicRegionTable.base_columns[f'seles_per_day_{region_id}'] = Column(verbose_name="Продаж в день", attrs={"td": {"class": f"cluster-{region_id}"}})
        DynamicRegionTable.base_columns[f'days_end_{region_id}'] = Column(verbose_name="Закончится дней", attrs={"td": {"class": f"cluster-{region_id}"}})
        DynamicRegionTable.base_columns[f'min_suply_{region_id}'] = Column(verbose_name="Минимально поставить", attrs={"td": {"class": f"cluster-{region_id}"}})

    return DynamicRegionTable

@login_required
def regions_parametrs(request):
    value = "regions_parametrs"  

    if request.method == 'GET':
        since_str = request.GET.get('since')
        to_str = request.GET.get('to')
        name = request.GET.get("name")
        article = request.GET.get("article")
        reg_filter = request.GET.get('reg_filter', 'all')

        if not since_str or not to_str:
            to_date = timezone.now()
            since_date = to_date - timedelta(days=45)
            since_str = since_date.strftime('%Y-%m-%d')
            to_str = to_date.strftime('%Y-%m-%d')

        if not since_str or not to_str:
            messages.error(request, "Необходимо выбрать обе даты")
            return redirect("regions")  

        try:
            since_date = datetime.strptime(since_str, '%Y-%m-%d')
            to_date = datetime.strptime(to_str, '%Y-%m-%d')

            logging.info(f"Параметры since: {since_str}, to: {to_str}")

            since_date = timezone.make_aware(since_date)
            to_date = timezone.make_aware(to_date)

            logging.info(f"Преобразованные даты: {since_date} - {to_date}")

            if since_date > to_date:
                messages.error(request, "Дата начала не может быть больше даты окончания")
                return redirect("regions")

            if to_date > timezone.now():
                messages.error(request, "Дата окончания не может быть в будущем")
                return redirect("regions")

            if (to_date - since_date).days > 95:
                messages.error(request, "Максимальный период выборки - 90 дней")
                return redirect("regions")

            processed = fetch_ozon_sales(request.user, since_date, to_date, value)
            messages.success(request, f"Успешно обработано {processed} записей")

        except ValueError:
            messages.error(request, "Неверный формат даты")
            return redirect("regions")

        except Exception as e:
            messages.error(request, f"Ошибка импорта: {str(e)}")
            return redirect("regions")
        logging.info(f"reg_filter={reg_filter}")
        return redirect(f"/regions/?since={since_str}&to={to_str}&name={name}&article={article}&reg_filter={reg_filter}")


@method_decorator(login_required, name='dispatch')
class Products_stage_2View(TemplateView):
    template_name = "personalproject/supply/supply_stage2/products_stage_2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        urgent = self.request.session.get("urgent_data", []) 
        mark_sorted_status(self.request) 
        calculate_packaging(self.request) 
        calculate_mixpallets(self.request) 


        seen_offer_ids = set()
        summary_data = []
        total_cost = 0
        total_sales_amount = 0
        number_units = 0
        total_volume = 0
        total_weight = 0
        unique_regions = set()

        offer_id_map = defaultdict(list)
        for item in urgent:
            offer_id = item.get('offer_id')
            if offer_id:
                offer_id_map[offer_id].append(item)

        summary_data = []
        total_cost = 0
        total_sales_amount = 0
        number_units = 0
        total_volume = 0  
        total_weight = 0  
        regions_set = set()

        for i, (offer_id, items) in enumerate(offer_id_map.items(), 1):
            total_quantity = sum(item.get('quantity', 0) for item in items)
            [regions_set.add(item['klaster_name']) for item in items if item.get('klaster_name')]

            try:
                product = Product.objects.get(offer_id=offer_id, user=user)
            except Product.DoesNotExist:
                continue

            cost_price = product.cost_price or 0
            price = product.price or 0
            total_price = price * total_quantity
            total_cost_price = cost_price * total_quantity


            try:
                h, w, d = product.height, product.width, product.depth
                volume_m3 = (h * w * d) / 1_000_000_000
                total_volume += volume_m3 * total_quantity
            except:
                pass

            try:
                weight_kg = product.weight / 1000  #
                total_weight += weight_kg * total_quantity
            except:
                pass

            summary_data.append({
                'number': i,
                'name': product.name,
                'offer_id': offer_id,
                'image_url': product.image_url,
                'quantity': total_quantity,
                'cost_price': round(total_cost_price, 2),
                'total_price': round(total_price, 2)
            })

            total_cost += total_cost_price
            total_sales_amount += total_price
            number_units += total_quantity

        table = Total_supply_table(summary_data)
        RequestConfig(self.request).configure(table)
        context["total_supply_table"] = table

        context["total_supply"] = {
            "total_cost": round(total_cost, 2),
            "total_sales_amount": round(total_sales_amount, 2),
            "quantity_oriducts_sku": len(offer_id_map),
            "number_units": number_units,
            "total_volume": round(total_volume, 3),
            "total_weight": round(total_weight, 2),
            "quantity_regions": len(regions_set),
        }

        packaging_data = self.request.session.get("packaging_result", [])
        urgent = self.request.session.get("urgent_data", [])

        if not packaging_data or not urgent:
            context["shipments_data"] = []
            return context

        urgent_days_left = {
            (item['offer_id'], item['klaster_id']): item['days_left']
            for item in urgent
        }
        product_map = {
            p.offer_id: p for p in Product.objects.filter(
                offer_id__in={item['offer_id'] for item in packaging_data},
                user=user
            )
        }

        by_cluster = defaultdict(list)
        for entry in packaging_data:
            by_cluster[entry['klaster_id']].append(entry)

        supply_type_map = {
            row.klaster_id: row.type_supply
            for row in Sales_analysis.objects.filter(user=user)
        }
        dispatch_map = {
            row.klaster_id: row.shipping_point
            for row in Sales_analysis.objects.filter(user=user)
        }

        shipments_data = []
        for cluster_id, items in by_cluster.items():

            sku_set = set()
            cost, revenue, weight, volume, total_qty = 0, 0, 0, 0, 0
            mix_boxes, mono_pallets, mix_pallets = 0, 0, 0

            for item in items:
                offer_id = item['offer_id']
                quantity = item.get('quantity', 0)
                total_qty += quantity
                sku_set.add(offer_id)
                mix_boxes += item.get('box_xl', 0) + item.get('box_l', 0) + item.get('box_m', 0) + item.get('box_s', 0)
                mono_pallets += item.get('europallet', 0)
                mix_pallets += item.get('mixpallets', 0)

                product = product_map.get(offer_id)
                if not product:
                    continue

                cost += (product.cost_price or 0) * quantity
                revenue += (product.price or 0) * quantity

                if all([product.height, product.width, product.depth, product.weight]):
                    volume += (product.height * product.width * product.depth / 1_000_000_000) * quantity
                    weight += (product.weight / 1000) * quantity

            region_name = next((item['klaster_name'] for item in urgent if item['klaster_id'] == cluster_id), f"ID: {cluster_id}")

            products_table = Products_in_supply([
                {
                    "offer_id": item["offer_id"],
                    "klaster_id": item["klaster_id"],
                    "image_url": product_map[item["offer_id"]].image_url if item["offer_id"] in product_map else "",
                    "quantity": item["quantity"],
                    "days_to_end": urgent_days_left.get((item["offer_id"], cluster_id), 0),
                    "days_with_supply": (urgent_days_left.get((item["offer_id"], cluster_id), 0) + (item["quantity"] / item.get("avg_sales", 1))),
                    "cost_price": round(product_map[item["offer_id"]].cost_price or 0, 2) if item["offer_id"] in product_map else 0
                }
                for item in items
            ])
            RequestConfig(self.request).configure(products_table)

            packaging_result = self.request.session.get("packaging_result", [])
            cargo_status_map = {
                (p["offer_id"], p["klaster_id"]): p.get("cargo_create_status", "—")
                for p in packaging_result
            }

            cargo_table = Cargo_type_table([
                *[
                    {
                        "type": key.upper(),
                        "offer_id": item["offer_id"] if key.upper() != "MIXPALLETS" else "-",
                        "quantity": item.get(key, 0),
                        "status": cargo_status_map.get((item["offer_id"], cluster_id), "—")
                    }
                    for item in items
                    for key in ["box_xl", "box_l", "box_m", "box_s", "europallet", "mixpallets"]     
                    if item.get(key, 0) > 0
                ],
            ])
                
        
            draft_info = self.request.session.get("supply_api_calls", [])
            draft_map = {d["klaster_id"]: d for d in draft_info}
            status_map = {d["klaster_id"]: d for d in draft_info}

            sales_analyses = Sales_analysis.objects.filter(user=self.request.user)
            dispatch_map = {sa.klaster_id: sa.warehouse_name for sa in sales_analyses if sa.warehouse_name}
            session_draft_info = self.request.session.get("supply_api_calls", [])
            warehouse_name_map = {d["klaster_id"]: d.get("put_away_warehouse_name", "—") for d in session_draft_info}

            shipments_data.append({
                "dispatch": dispatch_map.get(cluster_id, "—"),
                "region": region_name,
                "klaster_id": cluster_id,
                "wirehouse": warehouse_name_map.get(cluster_id, "—"),
                "supplu_type": supply_type_map.get(cluster_id, "—"),
                "cost": round(cost, 2),
                "summrealiz": round(revenue, 2),
                "quantity_sku": len(sku_set),
                "quantity_units": total_qty,
                "weight": round(weight, 2),
                "volume": round(volume, 2),
                "mono_pallets": mono_pallets,
                "mix_pallets": mix_pallets,
                "mix_boxes": mix_boxes,
                "products_table": products_table,
                "cargo_table": cargo_table,
                "draft": draft_map.get(cluster_id, {}).get("status", "—"),
                "supply": status_map.get(cluster_id, {}).get("supply_status", "—"),
            })

        context["shipments_data"] = shipments_data
        context["deleted_urgent_by_klaster"] = self.request.session.get("deleted_urgent_by_klaster", [])
        
        self.request.session["supply_api_calls"] = []
        self.request.session.modified = True 
        return context

def mark_sorted_status(request):
    urgent_data = request.session.get("urgent_data", [])
    if not urgent_data:
        return

    offer_ids = list(set(item['offer_id'] for item in urgent_data))

    products = Product.objects.filter(offer_id__in=offer_ids)
    offer_to_sort_type = {}

    for product in products:
        height = product.height  
        width = product.width
        depth = product.depth
        weight = product.weight  

        if (
            weight <= 10000 and
            depth <= 450 and
            width <= 320 and
            height <= 320
        ):
            offer_to_sort_type[product.offer_id] = "sorted"
        elif (
            weight <= 25000 and
            450 <= depth <= 1200 and
            320 <= width <= 600 and
            320 <= height <= 600
        ):
            offer_to_sort_type[product.offer_id] = "non_sorted"
        else:
            offer_to_sort_type[product.offer_id] = "oversize" 

    for item in urgent_data:
        offer_id = item['offer_id']
        item['sort_type'] = offer_to_sort_type.get(offer_id, 'unknown')

    request.session["urgent_data"] = urgent_data

def calculate_mixpallets(request):
    PALLET_LENGTH = Decimal("1.2")  
    PALLET_WIDTH = Decimal("0.8")   
    PALLET_HEIGHT = Decimal("2.2")  
    PALLET_VOLUME = PALLET_LENGTH * PALLET_WIDTH * PALLET_HEIGHT
    MIN_FILL_PERCENT = Decimal("0.8")

    packaging_result = request.session.get("packaging_result", [])
    if not packaging_result:
        return

    klaster_ids = set(item["klaster_id"] for item in packaging_result)
    mixpallets_by_klaster = {}

    for klaster_id in klaster_ids:
        cluster_items = [i for i in packaging_result if i["klaster_id"] == klaster_id]
        loose_boxes = []

        for item in cluster_items:
            offer_id = item["offer_id"]
            try:
                product = Product.objects.get(offer_id=offer_id)
            except Product.DoesNotExist:
                continue

            dimensions = (
                Decimal(product.width or 0) / 1000,   # X
                Decimal(product.depth or 0) / 1000,   # Y
                Decimal(product.height or 0) / 1000   # Z
            )

            if not all(dimensions):
                continue  

            for box_type in ["box_xl", "box_l", "box_m", "box_s"]:
                quantity = item.get(box_type, 0)
                for _ in range(quantity):
                    loose_boxes.append({
                        "offer_id": offer_id,
                        "dimensions": dimensions,
                        "volume": dimensions[0] * dimensions[1] * dimensions[2],
                    })

        mix_pallets = []

        for box in loose_boxes:
            placed = False
            for pallet in mix_pallets:
                if can_fit_on_pallet(pallet, box, PALLET_HEIGHT, PALLET_LENGTH, PALLET_WIDTH):
                    pallet["boxes"].append(box)
                    pallet["total_height"] += box["dimensions"][2]
                    pallet["occupied_area"] += box["dimensions"][0] * box["dimensions"][1]
                    pallet["volume"] += box["volume"]
                    placed = True
                    break

            if not placed:
                new_pallet = {
                    "boxes": [box],
                    "total_height": box["dimensions"][2],
                    "occupied_area": box["dimensions"][0] * box["dimensions"][1],
                    "volume": box["volume"],
                }
                mix_pallets.append(new_pallet)

        valid_mix_pallets = [p for p in mix_pallets if p["volume"] >= PALLET_VOLUME * MIN_FILL_PERCENT]

        mixpallets_by_klaster[klaster_id] = {
            "count": len(valid_mix_pallets),
            "offers": list({b["offer_id"] for p in valid_mix_pallets for b in p["boxes"]}),
        }

    for klaster_id, mix_data in mixpallets_by_klaster.items():
        count = mix_data["count"]
        offers = mix_data["offers"]
        for item in packaging_result:
            if item["klaster_id"] == klaster_id:
                item["mixpallets"] = count
                item["mixpallets_offers"] = ", ".join(offers)
                break  

    request.session["packaging_result"] = packaging_result
    return packaging_result


def can_fit_on_pallet(pallet, box, max_height, max_length, max_width):
    new_total_height = pallet["total_height"] + box["dimensions"][2]
    new_occupied_area = pallet["occupied_area"] + (box["dimensions"][0] * box["dimensions"][1])
    max_area = max_length * max_width
    return new_total_height <= max_height and new_occupied_area <= max_area
    
def calculate_packaging(request):
    urgent_data = request.session.get("urgent_data", [])
    if not urgent_data:
        return

    grouped = defaultdict(lambda: {'sorted': [], 'non_sorted': [], 'oversize': []})
    for item in urgent_data:
        cluster = item.get('klaster_id')
        sort_type = item.get('sort_type')
        if cluster and sort_type:
            grouped[cluster][sort_type].append(item)

    all_offer_ids = {item['offer_id'] for cluster in grouped.values()
                     for items in cluster.values() for item in items}
    products = Product.objects.filter(offer_id__in=all_offer_ids)
    product_map = {p.offer_id: p for p in products}

    updated_urgent_data = []
    result = []

    for cluster_id, types in grouped.items():
        for sort_type, items in types.items():
            for item in items:
                offer_id = item['offer_id']
                quantity = item['quantity']
                if quantity == 0:
                    quantity = 1
                product = product_map.get(offer_id)

                if not product:
                    messages.error(request, f"Товар {offer_id} не найден")
                    continue

                required_fields = ['box_type', 'weight', 'europallet']
                if any(getattr(product, f) is None for f in required_fields):
                    messages.error(request, f"Не заполнены поля для товара {offer_id}")
                    continue

                box_type = product.box_type.upper()
                if box_type not in ['S', 'M', 'L', 'XL']:
                    messages.error(request, f"Неверный box_type у товара {offer_id}: {box_type}")
                    continue

                box_capacity = getattr(product, f'box_{box_type.lower()}', 0)
                if box_capacity <= 0:
                    messages.error(request, f"Не указана вместимость коробки типа {box_type} у товара {offer_id}")
                    continue

                item_weight_kg = product.weight / 1000
                if item_weight_kg <= 0:
                    messages.error(request, f"Некорректный вес товара {offer_id}")
                    continue

                max_weight_per_box = 25
                max_by_weight = math.floor(max_weight_per_box / item_weight_kg)
                effective_capacity = min(box_capacity, max_by_weight)

                if effective_capacity <= 0:
                    messages.error(request, f"Нельзя упаковать товар {offer_id} ни в одну коробку по весу")
                    continue

                box_count = math.ceil(quantity / effective_capacity)
                total_packed = box_count * effective_capacity

                item['quantity'] = total_packed
                updated_urgent_data.append(item)

                pallet_capacity = product.europallet
                full_pallets = 0
                if pallet_capacity > 0:
                    if quantity >= math.ceil(0.9 * pallet_capacity):
                        full_pallets = quantity // pallet_capacity
                        remainder = quantity % pallet_capacity
                        if remainder >= math.ceil(0.9 * pallet_capacity):
                            full_pallets += 1

                result.append({
                    'offer_id': offer_id,
                    'klaster_id': cluster_id,
                    'quantity': total_packed,
                    'sort_type': sort_type,
                    'box_xl': box_count if box_type == 'XL' else 0,
                    'box_l': box_count if box_type == 'L' else 0,
                    'box_m': box_count if box_type == 'M' else 0,
                    'box_s': box_count if box_type == 'S' else 0,
                    'europallet': full_pallets,
                })

    request.session['urgent_data'] = updated_urgent_data
    request.session['packaging_result'] = result


@require_POST
@csrf_protect
def update_products_in_supply_table(request):
    urgent_data = request.session.get("urgent_data", [])
    logging.info("Начало обработки POST-запроса")
    logging.info(f"POST данные: {dict(request.POST)}")

    updated_count = 0

    for key, value in request.POST.items():
        if key.startswith("quantity:"):
            try:
                parts = key.split(":") 
                logging.info(parts)
                offer_id = parts[1]
                klaster_id = parts[2]
                new_quantity = int(value)
                for item in urgent_data:
                    if str(item.get("offer_id")) == offer_id and str(item.get("klaster_id")) == klaster_id:
                        item["quantity"] = max(0, new_quantity)
                        updated_count += 1
                        break  
            except (IndexError, ValueError, TypeError) as e:
                logging.error(f"Ошибка обработки поля {key}: {e}")
                continue

    request.session["urgent_data"] = urgent_data
    request.session.modified = True

    logging.info(f"Обновлено записей: {updated_count}")
    return redirect('products_stage_2')


@require_POST
@csrf_protect
def delete_shipment_view(request): 
    klaster_id = str(request.POST.get("klaster_id"))

    urgent = request.session.get("urgent_data", [])
    deleted = request.session.get("deleted_urgent", [])

    updated_urgent = []
    for item in urgent:
        if str(item.get("klaster_id")) == klaster_id:
            deleted.append(item.copy())
            item["quantity"] = 0
        updated_urgent.append(item)

    request.session["urgent_data"] = updated_urgent
    request.session["deleted_urgent"] = deleted
    request.session.modified = True

    return redirect("products_stage_2")

@require_POST
@csrf_protect
def restore_shipment_view(request): #restore_cargo
    klaster_id = str(request.POST.get("klaster_id"))

    urgent = request.session.get("urgent_data", [])
    deleted = request.session.get("deleted_urgent", [])

    restored = []
    new_deleted = []

    for item in deleted:
        if str(item.get("klaster_id")) == klaster_id:
            restored.append(item)
        else:
            new_deleted.append(item)

    for restore_item in restored:
        for urgent_item in urgent:
            if urgent_item.get("offer_id") == restore_item.get("offer_id") and str(urgent_item.get("klaster_id")) == klaster_id:
                urgent_item["quantity"] = restore_item["quantity"]

    request.session["urgent_data"] = urgent
    request.session["deleted_urgent"] = new_deleted
    request.session.modified = True

    return redirect("products_stage_2")

@login_required
@transaction.atomic
def create_supply(request):
    user = request.user
    urgent_data = request.session.get("urgent_data", [])
    packaging_result = request.session.get("packaging_result", [])
    logging.info("начало создания поставки")

    if not urgent_data or not packaging_result:
        messages.error(request, "Кажется, что-то пошло не так")
        return redirect("products_stage_2")

    uid = str(uuid.uuid4())
    operation = None

    if SupplyOperation.objects.filter(user=user, uid=uid).exists():
        messages.warning(request, "Операция уже была выполнена ранее.")
        return redirect("products_stage_2")

    try:
        operation = SupplyOperation.objects.create(user=user, uid=uid)
        packaging_by_klaster = defaultdict(list)
        for item in packaging_result:
            packaging_by_klaster[item["klaster_id"]].append(item)

        for klaster_id, items in packaging_by_klaster.items():
            if Supply.objects.filter(user=user, operation=operation, klaster_id=klaster_id).exists():
                continue

            sales = Sales_analysis.objects.filter(klaster_id=klaster_id, user=user).first()
            if not sales:
                raise Exception(f"Нет данных Sales_analysis для кластера {klaster_id}")

            type_supply = sales.type_supply or "—"
            shipping_point = sales.shipping_point or "—"
            region_name = sales.region_destination or "—"
            warehouse = sales.supply_name or "—"

            mix_boxes = sum(
                item.get("box_xl", 0) + item.get("box_l", 0) + item.get("box_m", 0) + item.get("box_s", 0)
                for item in items
            )
            mix_pallets = sum(item.get("europallet", 0) for item in items)
            mono_pallets = 0  

            sku_set = set()
            total_units = 0
            total_volume = 0
            total_weight = 0
            total_cost = 0
            total_sales = 0

            for item in items:
                sku_set.add(item["offer_id"])
                total_units += item["quantity"]

                product = Product.objects.filter(offer_id=item["offer_id"], user=user).first()
                if product:
                    h, w, d = product.height, product.width, product.depth
                    weight = product.weight
                    cost_price = product.cost_price or 0
                    sales_price = product.price or 0

                    if all([h, w, d]):
                        volume_m3 = (h * w * d) / 1_000_000_000
                        total_volume += volume_m3 * item["quantity"]
                    if weight:
                        total_weight += (weight / 1000) * item["quantity"]

                    total_cost += cost_price * item["quantity"]
                    total_sales += sales_price * item["quantity"]

            supply = Supply.objects.create(
                user=user,
                operation=operation,
                name=f"Поставка {klaster_id}",
                shipping_point=shipping_point,
                region_name=region_name,
                klaster_id=klaster_id,
                warehouse=warehouse,
                type_supply=type_supply,
                sku_count=len(sku_set),
                units_count=total_units,
                weight=round(total_weight, 2),
                volume=round(total_volume, 3),
                mono_pallets=mono_pallets,
                mix_pallets=mix_pallets,
                mix_boxes=mix_boxes,
            )

            for item in items:
                product = Product.objects.filter(offer_id=item["offer_id"], user=user).first()
                if not product:
                    continue
                SupplyProduct.objects.create(
                    supply=supply,
                    klaster_id=klaster_id,
                    product_offer_id=item["offer_id"],
                    quantity=item["quantity"],
                    cost_price=product.cost_price or 0,
                    sales_sum=(product.price or 0) * item["quantity"],
                    weight=(product.weight or 0) * item["quantity"] / 1000,
                    volume=((product.height * product.width * product.depth) / 1_000_000_000) * item["quantity"]
                    if all([product.height, product.width, product.depth]) else 0,
                )

            for item in items:
                for key in ["box_xl", "box_l", "box_m", "box_s", "europallet"]:
                    if item.get(key, 0) > 0:
                        CargoItem.objects.create(
                            supply=supply,
                            product_offer_id=item["offer_id"],
                            cargo_type=key.upper(),
                            total_quantity_in_cargo=item["quantity"],
                            cargo_count=item[key],
                        )

        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            messages.error(request, "Профиль пользователя не найден")
            return 0

        client_id = profile.ozon_client_id
        api_key = profile.ozon_api_key

        headers = {
            "Client-Id": client_id,
            "Api-Key": api_key,
            "Content-Type": "application/json"
        }

        supply_create_api_calls(request, user, operation, headers)
        create_supply_from_draft(request, user, headers)
        create_full_supply_process(request, user, headers)

    except Exception as e:
        SupplyOperation.objects.filter(uid=uid, user=user).delete()
        if operation:
            Supply.objects.filter(operation=operation).delete()
            operation.delete()
        messages.error(request, f"Произошла ошибка при создании поставки: {str(e)}")
        return redirect("products_stage_2")

    messages.success(request, "Поставка успешно создана.")
    return redirect("products_stage_2")


def supply_create_api_calls(request, user, operation, headers):
    supplies = Supply.objects.filter(user=user, draft_create_operation_id__isnull=True)
    
    for supply in supplies:
        items = []
        for product in supply.products.all():
            try:
                product_obj = Product.objects.get(user=supply.user, offer_id=product.product_offer_id)
                sku = product_obj.sku
            except Product.DoesNotExist:
                continue
            if not sku:
                continue

            items.append({
                "quantity": product.quantity,
                "sku": sku
            })

        payload = ""

        if supply.type_supply == "Кроссдокинг":
            try:
                analysis = Sales_analysis.objects.filter(user=supply.user, klaster_id=supply.klaster_id).first()
                warehouse_name = analysis.warehouse_name.strip() if analysis and analysis.warehouse_name else ""
            except Sales_analysis.DoesNotExist:
                messages.error(request, f"Не найдены данные анализа продаж для supply {supply.id}")
                continue

            search_payload = {
                "filter_by_supply_type": ["CREATE_TYPE_CROSSDOCK"],
                "search": warehouse_name
            }

            response = requests.post("https://api-seller.ozon.ru/v1/warehouse/fbo/list", headers=headers, json=search_payload)

            if response.status_code != 200:
                messages.error(request, f"Ошибка запроса складов Ozon: {response.text}")
                continue
            
            search_results = response.json().get("search", [])
            warehouse_id = None
            for wh in search_results:
                if wh["name"].strip().lower() == warehouse_name.lower():
                    warehouse_id = wh["warehouse_id"]
                    break
                
            if not warehouse_id:
                messages.error(request, f"Склад с названием '{warehouse_name}' не найден. Проверьте правильность.")
                continue
            
            supply.warehouse = warehouse_id
            supply.save(update_fields=["warehouse"])

            payload = {
                "cluster_ids": [str(supply.klaster_id)],
                "drop_off_point_warehouse_id": int(warehouse_id),
                "items": items,
                "type": "CREATE_TYPE_CROSSDOCK"
            }
            time.sleep(1)
            draft_response = requests.post("https://api-seller.ozon.ru/v1/draft/create", headers=headers, json=payload)

        elif supply.type_supply == "Прямая":
            payload = {
                "cluster_ids": [str(supply.klaster_id)],
                "items": items,
                "type": "CREATE_TYPE_DIRECT"
            }
            time.sleep(1)
            draft_response = requests.post("https://api-seller.ozon.ru/v1/draft/create", headers=headers, json=payload)
        else:
            messages.error(request, "Ошибка, проверьте указанные данные")
            continue  


        if draft_response.status_code != 200:
            if draft_response.text == '{"code":7,"message":"Api-Key is missing a required role for a method","details":[]}':
                messages.error(request, "Ошибка, проверьте доступы API ключа")
                return 0
            logging.error(f"Ошибка создания черновика для supply {supply.id}: {draft_response.text}")
            continue

        operation_id = draft_response.json().get("operation_id")
        if not operation_id:
            logging.error("Операция не вернула operation_id")
            continue

        supply.draft_create_operation_id = operation_id
        supply.save()

        get_supply_info_api(operation_id, headers, supply, request)

def get_supply_info_api(operation_id, headers, supply, request):
    session_draft_info = []
    try:
        attempts = 0
        draft_id = 0

        while attempts < 3:  # максимум 3 попытки
            status_payload = {"operation_id": operation_id}
            info_response = requests.post("https://api-seller.ozon.ru/v1/draft/create/info", headers=headers, json=status_payload)

            if info_response.status_code == 200:
                data = info_response.json()
                status = data.get("status")
                draft_id = data.get("draft_id", 0)
                clusters = data.get("clusters", [])

                if draft_id and draft_id != 0:
                    supply.draft = status
                    supply.draft_id = draft_id
                    supply.save()

                    warehouses = []
                    for cluster in clusters:
                        cluster_warehouses = cluster.get("warehouses", [])
                        for warehouse in cluster_warehouses:
                            supply_warehouse = warehouse.get("supply_warehouse")
                            if supply_warehouse:
                                warehouse_id = supply_warehouse.get("warehouse_id")
                                if warehouse_id:
                                    warehouses.append(warehouse_id)

                    session_draft_info.append({
                        "supply_id": supply.id,
                        "klaster_id": supply.klaster_id,
                        "operation_id": operation_id,
                        "status": status,
                        "draft_id": draft_id,
                        "warehouse_ids": warehouses,
                    })
                    break
                else:
                    if attempts < 2:
                        time.sleep(10)  # ждём 30 секунд перед следующей попыткой
                    attempts += 1
            else:
                logging.error(f"Ошибка получения статуса для operation_id {operation_id}")
                break
    except Exception as e:
        logging.error(f"Ошибка в get_supply_info_api: {str(e)}")
        messages.error(request, "Произошла ошибка при получении статуса черновика")
    
    request.session["supply_api_calls"] = session_draft_info
    request.session.modified = True

    get_timeslot_info(request, operation_id, headers)


def chunked(iterable, size):
    it = iter(iterable)
    return iter(lambda: list(islice(it, size)), [])

def get_timeslot_info(request, operation_id, headers):
    session_draft_info = request.session.get("supply_api_calls", [])
    draft_info = next((item for item in session_draft_info if item.get("operation_id") == operation_id), None)

    if not draft_info:
        #messages.error(request, "Что то пошло не так")
        logging.warning(f"Не найдена информация о черновике для операции {operation_id}")
        return None

    draft_id = draft_info.get("draft_id")
    warehouse_ids = draft_info.get("warehouse_ids", [])

    if not draft_id or not warehouse_ids:
        messages.error(request, "Недостаточно данных для получения таймслота")
        return None

    now = datetime.utcnow()
    date_from = now + timedelta(days=3)
    date_to = date_from + timedelta(days=7)

    date_from_str = date_from.isoformat() + "Z"
    date_to_str = date_to.isoformat() + "Z"

    url = "https://api-seller.ozon.ru/v1/draft/timeslot/info"
    selected = None
    data = {}

    for i, chunk in enumerate(chunked(warehouse_ids, 10), start=1):
        payload = {
            "date_from": date_from_str,
            "date_to": date_to_str,
            "draft_id": draft_id,
            "warehouse_ids": chunk,
        }

        logging.info(f"Отправляем чанк #{i}: {chunk}")
        logging.info(f"Payload: {payload}")

        try:
            time.sleep(2.5)
            response = requests.post(url, headers=headers, json=payload)
            data = response.json()
            if response.status_code != 200:
                logging.error(f"Ответ от API на чанк #{i}: {data}")
        except Exception as e:
            logging.error(f"Ошибка запроса к API на чанк #{i}: {e}")
            continue

        if response.status_code == 200:
            timeslots_data = data.get("drop_off_warehouse_timeslots", [])

            for warehouse_info in timeslots_data:
                days = warehouse_info.get("days", [])
                if not days:
                    continue

                for day in days:
                    timeslots = day.get("timeslots", [])
                    if timeslots:
                        first_slot = timeslots[0]
                        selected = {
                            "drop_off_warehouse_id": warehouse_info.get("drop_off_warehouse_id"),
                            "from_in_timezone": first_slot.get("from_in_timezone"),
                            "to_in_timezone": first_slot.get("to_in_timezone"),
                        }
                        logging.info(f"Найден таймслот на чанк #{i}: {selected}")
                        break
                if selected:
                    break
        if selected:
            break  # выход если найдено

    if selected:
        try:
            supply = Supply.objects.get(draft_id=draft_id)
            supply.drop_off_warehouse_id = selected["drop_off_warehouse_id"]
            supply.delivery_time_from = selected["from_in_timezone"]
            supply.delivery_time_to = selected["to_in_timezone"]
            supply.save()
            logging.info(f"Успешно сохранили таймслот для supply {supply.id}")
        except Supply.DoesNotExist:
            logging.error(f"Не найден supply с draft_id {draft_id}")
    else:
        logging.info(f"Не найден доступный таймслот для draft_id={draft_id}")
        messages.error(request, "В ближайшие 10 дней не найден доступный таймслот для кластера")
        return None

    return data

def create_supply_from_draft(request, user, headers):

    supplies = Supply.objects.filter(
        user=user,
        draft_id__isnull=False,
        draft_create_operation_id__isnull=False,
        drop_off_warehouse_id__isnull=False,
        delivery_time_from__isnull=False,
        delivery_time_to__isnull=False,
        create_supply_from_draft_operation_id__isnull=True
    )
    
    session_draft_info = request.session.get("supply_api_calls", [])
    MAX_ATTEMPTS = 3

    for supply in supplies:
        if supply.type_supply == "Прямая":
            payload = {
                "draft_id": supply.draft_id,
                "timeslot": {
                    "from_in_timezone": supply.delivery_time_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "to_in_timezone": supply.delivery_time_to.strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "warehouse_id": supply.drop_off_warehouse_id
            }
        elif supply.type_supply == "Кроссдокинг":
            warehouses = Warehouse.objects.filter(klaster_id=supply.klaster_id)
            for warehouse in warehouses:
                payload = {
                    "draft_id": supply.draft_id,
                    "timeslot": {
                        "from_in_timezone": supply.delivery_time_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to_in_timezone": supply.delivery_time_to.strftime("%Y-%m-%dT%H:%M:%SZ")
                    },
                    "warehouse_id": warehouse.warehouse_id
                }

                response = requests.post(
                    "https://api-seller.ozon.ru/v1/draft/supply/create",
                    json=payload,
                    headers=headers
                )

                data = response.json()

                if "operation_id" in data:
                    supply.warehouse = warehouse.warehouse_id
                    supply.save()
                    session_draft_info = request.session.get("supply_api_calls", [])
                    for entry in session_draft_info:
                        if entry.get("supply_id") == supply.id:
                            entry["put_away_warehouse_name"] = warehouse.name
                            break
                        
                    request.session["supply_api_calls"] = session_draft_info
                    request.session.modified = True
                    break  


        logging.info(f"payload на создание поставки по черновику для supply {supply.id}: {payload}")

        for attempt in range(MAX_ATTEMPTS):
            response_create = requests.post("https://api-seller.ozon.ru/v1/draft/supply/create", headers=headers, json=payload)

            if response_create.status_code == 200:
                data = response_create.json()
                operation_id = data.get("operation_id")

                if operation_id:
                    supply.create_supply_from_draft_operation_id = operation_id
                    supply.save()
                    logging.info(f"Успешно создали заявку на поставку по черновику для supply {supply.id}")
                    
                    time.sleep(3)  
                    
                    for status_attempt in range(MAX_ATTEMPTS):
                        status_payload = {"operation_id": operation_id}
                        url_status = "https://api-seller.ozon.ru/v1/draft/supply/create/status"
                        response_status = requests.post(url_status, headers=headers, json=status_payload)

                        if response_status.status_code == 200:
                            status_data = response_status.json()
                            supply_status = status_data.get("status", "UNKNOWN")

                            supply.supply_status = supply_status
                            supply.save()

                            for item in session_draft_info:
                                if item.get("supply_id") == supply.id:
                                    item["supply_status"] = supply_status
                                    break

                            logging.info(f"Успешно получили статус для supply {supply.id}: {supply_status}")
                            break  
                        else:
                            logging.error(f"Ошибка получения статуса заявки для supply {supply.id}: {response_status.status_code} {response_status.text}")
                            if status_attempt < MAX_ATTEMPTS - 1:
                                logging.info(f"Повторная попытка получить статус... Ждем 3 секунды.")
                                time.sleep(3)
                            else:
                                messages.error(request, f"Ошибка получения статуса создания заявки для поставки {supply.name}")

                    break 
                else:
                    logging.error(f"Ответ без operation_id для supply {supply.id}")
                    if attempt < MAX_ATTEMPTS - 1:
                        logging.info(f"Повторная попытка создания заявки... Ждем 3 секунды.")
                        time.sleep(3)
                    else:
                        messages.error(request, f"Ошибка создания заявки для поставки {supply.name}")
            else:
                logging.error(f"Ошибка запроса к API: {response_create.status_code} {response_create.text}")
                if response_create.status_code in (429, 409) and attempt < MAX_ATTEMPTS - 1:
                    logging.error(f"Ошибка {response_create.status_code}, повторная попытка... Ждем 3 секунды.")
                    time.sleep(3)
                else:
                    messages.error(request, f"Ошибка создания заявки для поставки {supply.name}")
                    break

    request.session["supply_api_calls"] = session_draft_info
    request.session.modified = True


def create_full_supply_process(request, user, headers):
    supplies = Supply.objects.filter(
        user=user,
        draft_id__isnull=False,
        draft_create_operation_id__isnull=False,
        drop_off_warehouse_id__isnull=False,
        delivery_time_from__isnull=False,
        delivery_time_to__isnull=False,
        create_supply_from_draft_operation_id__isnull=False,
        supply_id__isnull=True,
    )

    session_draft_info = request.session.get("supply_api_calls", [])
    packaging_result = request.session.get("packaging_result", [])

    for supply in supplies:
        attempts = 0
        while attempts < 3:
            status_payload = {"operation_id": supply.create_supply_from_draft_operation_id}
            status_url = "https://api-seller.ozon.ru/v1/draft/supply/create/status"
            response_status = requests.post(status_url, headers=headers, json=status_payload)

            status_data = response_status.json()
            if status_data.get("status") == "DraftSupplyCreateStatusInProgress":
                time.sleep(6)
                attempts +=1
            elif status_data.get("status") == "DraftSupplyCreateStatusSuccess":
                attempts = 3

            
            

        if response_status.status_code == 200:
            status_data = response_status.json()
            supply_status = status_data.get("status", "UNKNOWN")
            order_ids = status_data.get("result", {}).get("order_ids", [])

            if not order_ids:
                messages.error(request, f"Нет order_ids для поставки {supply.id}")
                return 0
                continue

            supply.supply_status = supply_status
            supply.save()

            
            order_url = "https://api-seller.ozon.ru/v2/supply-order/get"
            order_payload = {"order_ids": order_ids}
            response_order = requests.post(order_url, headers=headers, json=order_payload)

            if response_order.status_code == 200:
                order_data = response_order.json()
                orders = order_data.get("orders", [])
                if orders:
                    supply_id = orders[0].get("supplies", [])[0].get("supply_id")
                    first_order = orders[0]
                    supply_order_id = first_order.get("supply_order_id") # for cargo
                    if supply_id:
                        supply.supply_id = supply_id
                        supply.supply_order_id = supply_order_id
                        logging.info(f'supply_order_id{supply_order_id}')
                        supply.save()
                        logging.info(f"Получили и сохранили supply_id для supply {supply.id}: {supply_id}")
                    else:
                        logging.error(f"Не найден supply_id для supply {supply.id}")
                        continue
                else:
                    logging.error(f"Нет orders в ответе для supply {supply.id}")
                    continue
            else:
                logging.error(f"Ошибка получения заказа по order_ids для supply {supply.id}: {response_order.text}")
                continue

            # 3. Создать грузоместа (cargoes)
            cargo_payload = {
                "cargoes": [
                    {
                        "key": f"supply-{supply.id}-box-1",
                        "value": {
                            "items": [],
                            "type": "BOX"
                        }
                    }
                ],
                "delete_current_version": False,
                "supply_id": supply.supply_id
            }

            for product in supply.products.all():
                try:
                    product_obj = Product.objects.get(user=user, offer_id=product.product_offer_id)
                except Product.DoesNotExist:
                    continue

                item_data = {
                    "barcode": product_obj.barcode or "",
                    "quantity": product.quantity,
                    "quant": 1
                }

                if product_obj.fit_to:
                    item_data["expires_at"] = product_obj.fit_to.strftime("%Y-%m-%dT%H:%M:%SZ")

                cargo_payload["cargoes"][0]["value"]["items"].append(item_data)
            time.sleep(5)
            cargo_url = "https://api-seller.ozon.ru/v1/cargoes/create"
            response_cargo = requests.post(cargo_url, headers=headers, json=cargo_payload)

            if response_cargo.status_code == 200:
                cargo_data = response_cargo.json()
                cargo_operation_id = cargo_data.get("operation_id")
                if cargo_operation_id:
                    supply.cargo_create_operation_id = cargo_operation_id
                    supply.save()
                    logging.info(f"Успешно создали грузоместа для supply {supply.id}")

                    cargo_info_url = "https://api-seller.ozon.ru/v1/cargoes/create/info"
                    cargo_info_payload = {"operation_id": cargo_operation_id}
                    response_cargo_info = requests.post(cargo_info_url, headers=headers, json=cargo_info_payload)
                    if response_cargo_info.status_code == 200:
                        cargo_info_data = response_cargo_info.json()
                        cargo_status = cargo_info_data.get("status", "UNKNOWN")
                        logging.info(f"Статус создания грузомест для supply {supply.id}: {cargo_status}")
                        for supply_product in supply.products.all():
                            offer_id = supply_product.product_offer_id
                            for pack in packaging_result:
                                if pack.get("offer_id") == offer_id and pack.get("klaster_id") == supply.klaster_id:
                                    pack["cargo_create_status"] = cargo_status
                        logging.info(f"Обновили cargo_status в packaging_result для supply {supply.id}")

                    else:
                        logging.error(f"Ошибка получения информации о грузоместах для supply {supply.id}: {response_cargo_info.text}")
                else:
                    logging.error(f"Ошибка: нет operation_id в ответе от cargoes.create")
            else:
                logging.error(f"Ошибка создания грузоместа для supply {supply.id}: {response_cargo.text}")
            try:
                sales = Sales_analysis.objects.filter(
                    klaster_id=supply.klaster_id,
                    user=user
                ).first()

                if not sales:
                    logging.error(f"Не найдены данные Sales_analysis для supply {supply.id}")
                    continue
                
                name_driver = sales.name_driver or ""
                driver_mobile_number = sales.driver_mobile_number or ""
                car_mark = sales.car_mark or ""
                car_number = sales.car_number or ""

                if not all([name_driver, driver_mobile_number, car_mark, car_number]):
                    logging.error(f"Не все данные для водителя заполнены для поставки {supply.id}")
                    messages.error(request, f"Указаны не все данные для водителя")
                    continue
                
                pass_payload = {
                    "supply_order_id": supply.supply_order_id,
                    "vehicle": {
                        "driver_name": name_driver,
                        "driver_phone": driver_mobile_number,
                        "vehicle_model": car_mark,
                        "vehicle_number": car_number,
                    }
                }

                logging.info(f"pass_payload для supply {supply.id}: {pass_payload}")

                pass_url = "https://api-seller.ozon.ru/v1/supply-order/pass/create"
                response_pass = requests.post(pass_url, headers=headers, json=pass_payload)

                if response_pass.status_code == 200:
                    logging.info(f"Водитель указан для supply {supply.id}")
                else:
                    logging.error(f"Ошибка указании водителя для supply {supply.id}: {response_pass.text}")
                    messages.error(request, f"Произошла ошибка при указании водителя{response_pass.text}")

            except Exception as e:
                logging.error(f"Ошибка при указании водителя {supply.id}: {str(e)}")

            for item in session_draft_info:
                if item.get("supply_id") == supply.id:
                    item["supply_status"] = supply.supply_status
                    break

        else:
            logging.error(f"Ошибка получения статуса создания заявки для supply {supply.id}: {response_status.text}")

    request.session["supply_api_calls"] = session_draft_info
    request.session["packaging_result"] = packaging_result 
    request.session.modified = True
    



@require_POST
@csrf_protect
def delete_shipment_view_by_claster(request): 
    klaster_id = str(request.POST.get("klaster_id"))
    
    urgent = request.session.get("urgent_data", [])
    deleted = request.session.get("deleted_urgent_by_klaster", [])

    new_urgent = []
    for item in urgent:
        if str(item.get("klaster_id")) == klaster_id:
            deleted.append(item)
        else:
            new_urgent.append(item)

    request.session["urgent_data"] = new_urgent
    request.session["deleted_urgent_by_klaster"] = deleted
    request.session.modified = True
    return redirect("products_stage_2")


@require_POST
@csrf_protect
def restore_shipment_view_by_claster(request): 
    klaster_id = str(request.POST.get("klaster_id"))
    
    urgent = request.session.get("urgent_data", [])
    deleted = request.session.get("deleted_urgent_by_klaster", [])

    new_deleted = []
    for item in deleted:
        if str(item.get("klaster_id")) == klaster_id:
            urgent.append(item)
        else:
            new_deleted.append(item)

    request.session["urgent_data"] = urgent
    request.session["deleted_urgent_by_klaster"] = new_deleted
    request.session.modified = True
    return redirect("products_stage_2")





