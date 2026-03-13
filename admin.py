from django.contrib import admin
from .models import (
    UserProfile, AssetType, Portfolio, Asset, PriceHistory,
    Voucher, VoucherRedemption, Watchlist, PriceAlert, Transaction
)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'currency', 'created_at')
    search_fields = ('user__username',)

@admin.register(AssetType)
class AssetTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_value', 'total_gain_loss', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('total_value', 'total_investment', 'created_at', 'updated_at')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'asset_type', 'quantity', 'current_price', 'created_at')
    search_fields = ('name', 'symbol')
    list_filter = ('asset_type', 'created_at')

@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('asset', 'price', 'date')
    search_fields = ('asset__name',)
    list_filter = ('date',)

@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'is_active', 'current_uses', 'max_uses', 'expiry_date')
    search_fields = ('code',)
    list_filter = ('is_active', 'expiry_date')

@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'voucher', 'redeemed_at')
    search_fields = ('user__username', 'voucher__code')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'added_at')
    search_fields = ('user__username', 'asset__name')

@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'asset', 'condition', 'target_price', 'is_triggered')
    search_fields = ('user__username', 'asset__name')
    list_filter = ('condition', 'is_triggered')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('asset', 'transaction_type', 'quantity', 'price', 'transaction_date')
    search_fields = ('asset__name',)
    list_filter = ('transaction_type', 'transaction_date')---