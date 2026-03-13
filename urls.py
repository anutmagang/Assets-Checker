from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    # Public
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard & Analytics
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    
    # Asset Management
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/<int:pk>/edit/', views.asset_edit, name='asset_edit'),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    
    # Watchlist
    path('watchlist/', views.watchlist_view, name='watchlist_view'),
    path('watchlist/add/<int:pk>/', views.watchlist_add, name='watchlist_add'),
    path('watchlist/remove/<int:pk>/', views.watchlist_remove, name='watchlist_remove'),
    
    # Price Alerts
    path('alerts/', views.price_alert_list, name='price_alert_list'),
    path('alerts/create/<int:pk>/', views.price_alert_create, name='price_alert_create'),
    
    # Transactions
    path('transactions/<int:asset_pk>/', views.transaction_list, name='transaction_list'),
    path('transactions/<int:asset_pk>/create/', views.transaction_create, name='transaction_create'),
    
    # User Settings
    path('settings/', views.settings, name='settings'),
    path('settings/password/', views.change_password, name='change_password'),
    
    # Vouchers
    path('vouchers/', views.voucher_list, name='voucher_list'),
    path('vouchers/redeem/', views.redeem_voucher, name='redeem_voucher'),
    path('vouchers/manage/', views.voucher_manager, name='voucher_manager'),
    
    # API
    path('api/portfolio/', views.api_portfolio_data, name='api_portfolio'),
    path('api/assets/', views.api_assets_data, name='api_assets'),
]