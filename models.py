from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# ===== MODEL 1: User Profile =====
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    currency = models.CharField(
        max_length=3,
        choices=[('USD', 'US Dollar'), ('IDR', 'Indonesian Rupiah')],
        default='USD'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


# ===== MODEL 2: Asset Type =====
class AssetType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Asset Type'
        verbose_name_plural = 'Asset Types'


# ===== MODEL 3: Portfolio =====
class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_totals(self):
        """Hitung total portfolio"""
        assets = self.assets.all()
        self.total_value = sum(float(asset.get_current_value()) for asset in assets)
        self.total_investment = sum(float(asset.quantity * asset.purchase_price) for asset in assets)
        self.save()

    @property
    def total_gain_loss(self):
        return self.total_value - self.total_investment

    @property
    def gain_loss_percentage(self):
        if self.total_investment == 0:
            return 0
        return (self.total_gain_loss / self.total_investment) * 100

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

    class Meta:
        verbose_name = 'Portfolio'
        verbose_name_plural = 'Portfolios'


# ===== MODEL 4: Asset =====
class Asset(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='assets')
    asset_type = models.ForeignKey(AssetType, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=20, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    quantity = models.DecimalField(max_digits=15, decimal_places=8)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    purchase_date = models.DateField()

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_current_value(self):
        return float(self.quantity) * float(self.current_price)

    def get_investment_amount(self):
        return float(self.quantity) * float(self.purchase_price)

    def get_gain_loss(self):
        return self.get_current_value() - self.get_investment_amount()

    @property
    def gain_loss_percentage(self):
        investment = self.get_investment_amount()
        if investment == 0:
            return 0
        return (self.get_gain_loss() / investment) * 100

    def __str__(self):
        return f"{self.name} ({self.symbol})" if self.symbol else self.name

    class Meta:
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['-created_at']


# ===== MODEL 5: Price History =====
class PriceHistory(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='price_history')
    price = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.price} on {self.date}"

    class Meta:
        verbose_name = 'Price History'
        verbose_name_plural = 'Price Histories'
        ordering = ['-date']
        unique_together = ['asset', 'date']


# ===== MODEL 6: Voucher =====
class Voucher(models.Model):
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    discount_percentage = models.IntegerField(default=10)
    max_uses = models.IntegerField(default=100)
    current_uses = models.IntegerField(default=0)
    expiry_date = models.DateField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_valid(self):
        today = timezone.now().date()
        return self.is_active and self.expiry_date >= today and self.current_uses < self.max_uses

    def __str__(self):
        return f"{self.code} - {self.discount_percentage}%"

    class Meta:
        verbose_name = 'Voucher'
        verbose_name_plural = 'Vouchers'


# ===== MODEL 7: Voucher Redemption =====
class VoucherRedemption(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'voucher']
        verbose_name = 'Voucher Redemption'
        verbose_name_plural = 'Voucher Redemptions'

    def __str__(self):
        return f"{self.user.username} redeemed {self.voucher.code}"


# ===== MODEL 8: Watchlist =====
class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'asset']
        verbose_name = 'Watchlist'
        verbose_name_plural = 'Watchlists'

    def __str__(self):
        return f"{self.user.username} watching {self.asset.name}"


# ===== MODEL 9: Price Alert =====
class PriceAlert(models.Model):
    CONDITION_CHOICES = [
        ('above', 'Price Above'),
        ('below', 'Price Below'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    condition = models.CharField(max_length=10, choices=CONDITION_CHOICES)
    target_price = models.DecimalField(max_digits=15, decimal_places=2)
    is_triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'

    def __str__(self):
        return f"{self.user.username} - {self.asset.name} {self.condition} {self.target_price}"


# ===== MODEL 10: Transaction =====
class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('dividend', 'Dividend'),
    ]

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    quantity = models.DecimalField(max_digits=15, decimal_places=8)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    transaction_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.asset.name} - {self.transaction_type} ({self.quantity})"