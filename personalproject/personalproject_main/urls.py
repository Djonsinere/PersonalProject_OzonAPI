from django.contrib import admin
from django.urls import path, include
from .views import ProductListView, StockListView, register_view, login_view, logout_view, update_sales_analysis, import_ozon_sales, change_table, ProfileView, update_shipping_point_table, ReferenceView, update_refernce_table, GoodsView, Products_stage_2View, get_sales_for_goods, RegionsView, regions_parametrs, update_products_in_supply_table, delete_shipment_view, restore_shipment_view, create_supply, restore_shipment_view_by_claster, delete_shipment_view_by_claster, base_redirect
from django.contrib.auth.decorators import login_required
handler404 = "personalproject_main.views.custom_404"
handler500 = "personalproject_main.views.custom_500"
handler403 = "personalproject_main.views.custom_403"
handler400 = "personalproject_main.views.custom_400"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', base_redirect),
    path("registration/", register_view, name="register"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("products/", login_required(ProductListView.as_view()), name="products"),
    path("stocks/<int:pk>/", StockListView.as_view(), name="stock_list"),
    path('update-sales-analysis/<int:pk>/', update_sales_analysis, name='update_sales_analysis'),
    path('import-sales/', import_ozon_sales, name='import_sales'),
    path("change_table/", change_table, name="update_sales"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path('update_shipping_point_table/<int:pk>/', update_shipping_point_table, name='update_shipping_point_table'),
    path("reference/", login_required(ReferenceView.as_view()), name="reference"),
    path('update_refernce_table/<int:pk>/', update_refernce_table, name='update_refernce_table'),
    path('products_stage_2/', login_required(Products_stage_2View.as_view()), name="products_stage_2"),
    path('create_supply/', create_supply, name='create_supply'),
    path('update_products_in_supply_table/', update_products_in_supply_table, name='update_products_in_supply_table'),
    path('goods/', login_required(GoodsView.as_view()), name='goods'),
    path('goods_parametrs/', login_required(get_sales_for_goods), name='goods_get_sales'),
    path('regions/', login_required(RegionsView.as_view()), name='regions'),
    path('regions_parametrs/', login_required(regions_parametrs), name='regions_parametrs'),
    path("delete_shipment/", delete_shipment_view, name="delete_shipment"),
    path("restore_shipment/", restore_shipment_view, name="restore_shipment"),
    path("restore_shipment_by_klaster/", restore_shipment_view_by_claster, name="restore_shipment_by_klaster"),
    path("delete_shipment_by_klaster/", delete_shipment_view_by_claster, name="delete_shipment_by_klaster"),
    
]