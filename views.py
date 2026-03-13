# FULL KODE: tracker/views.py
# Copy-paste SEMUA kode berikut ke file tracker/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Sum
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

from .models import (
    Asset, Portfolio, AssetType, Voucher, VoucherRedemption,
    UserProfile, Watchlist, PriceAlert, Transaction, PriceHistory
)
from .forms import (
    RegisterForm, AssetForm, ProfileForm, PasswordChangeForm,
    VoucherRedemptionForm
)


# ============================================================================
# PUBLIC VIEWS
# ============================================================================

def home(request):
    """Halaman home"""
    context = {
        'total_users': User.objects.count(),
        'total_assets': Asset.objects.count(),
    }
    return render(request, 'tracker/home.html', context)


def register(request):
    """Register user baru"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # Buat profile dan portfolio
            UserProfile.objects.create(user=user)
            Portfolio.objects.create(user=user)
            
            messages.success(request, 'Register berhasil! Silakan login.')
            return redirect('tracker:login')
    else:
        form = RegisterForm()
    
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    """Login user"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Selamat datang, {user.username}!')
            return redirect('tracker:dashboard')
        else:
            messages.error(request, 'Username atau password salah!')
    
    return render(request, 'tracker/login.html')


def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'Anda telah logout.')
    return redirect('tracker:home')


# ============================================================================
# DASHBOARD
# ============================================================================

@login_required(login_url='tracker:login')
def dashboard(request):
    """Dashboard dengan portfolio overview"""
    try:
        portfolio = request.user.portfolio
    except Portfolio.DoesNotExist:
        portfolio = Portfolio.objects.create(user=request.user)
    
    # Calculate totals
    portfolio.calculate_totals()
    
    assets = portfolio.assets.all()
    alerts = PriceAlert.objects.filter(user=request.user, is_triggered=False)
    
    context = {
        'portfolio': portfolio,
        'assets': assets,
        'assets_count': assets.count(),
        'alerts': alerts,
        'total_value': portfolio.total_value,
        'total_gain_loss': portfolio.total_gain_loss,
        'gain_loss_percentage': portfolio.gain_loss_percentage,
    }
    
    return render(request, 'tracker/dashboard.html', context)


# ============================================================================
# ASSET MANAGEMENT (CRUD)
# ============================================================================

@login_required(login_url='tracker:login')
def asset_list(request):
    """List semua assets user"""
    try:
        portfolio = request.user.portfolio
    except Portfolio.DoesNotExist:
        portfolio = Portfolio.objects.create(user=request.user)
    
    assets = portfolio.assets.all()
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query) |
            Q(symbol__icontains=search_query)
        )
    
    # Filter by type
    asset_type = request.GET.get('type')
    if asset_type:
        assets = assets.filter(asset_type__id=asset_type)
    
    context = {
        'assets': assets,
        'asset_types': AssetType.objects.all(),
        'search_query': search_query,
    }
    
    return render(request, 'tracker/asset_list.html', context)


@login_required(login_url='tracker:login')
def asset_create(request):
    """Create asset baru"""
    try:
        portfolio = request.user.portfolio
    except Portfolio.DoesNotExist:
        portfolio = Portfolio.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.portfolio = portfolio
            asset.save()
            
            # Create price history
            PriceHistory.objects.create(
                asset=asset,
                price=asset.current_price,
                date=asset.purchase_date
            )
            
            messages.success(request, f'Asset "{asset.name}" berhasil ditambahkan!')
            return redirect('tracker:asset_list')
    else:
        form = AssetForm()
    
    return render(request, 'tracker/asset_form.html', {'form': form, 'title': 'Add Asset'})


@login_required(login_url='tracker:login')
def asset_detail(request, pk):
    """View detail asset"""
    asset = get_object_or_404(Asset, pk=pk, portfolio__user=request.user)
    
    # Get price history
    price_history = asset.price_history.all()[:30]
    
    # Get transactions
    transactions = asset.transactions.all()
    
    context = {
        'asset': asset,
        'price_history': price_history,
        'transactions': transactions,
        'gain_loss': asset.get_gain_loss(),
        'gain_loss_percentage': asset.gain_loss_percentage,
    }
    
    return render(request, 'tracker/asset_detail.html', context)


@login_required(login_url='tracker:login')
def asset_edit(request, pk):
    """Edit asset"""
    asset = get_object_or_404(Asset, pk=pk, portfolio__user=request.user)
    
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            
            # Update price history
            PriceHistory.objects.create(
                asset=asset,
                price=asset.current_price,
                date=asset.updated_at.date()
            )
            
            messages.success(request, f'Asset "{asset.name}" berhasil diupdate!')
            return redirect('tracker:asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
    
    return render(request, 'tracker/asset_form.html', {'form': form, 'asset': asset, 'title': 'Edit Asset'})


@login_required(login_url='tracker:login')
def asset_delete(request, pk):
    """Delete asset"""
    asset = get_object_or_404(Asset, pk=pk, portfolio__user=request.user)
    
    if request.method == 'POST':
        asset_name = asset.name
        asset.delete()
        messages.success(request, f'Asset "{asset_name}" berhasil dihapus!')
        return redirect('tracker:asset_list')
    
    return render(request, 'tracker/asset_confirm_delete.html', {'asset': asset})


# ============================================================================
# ANALYTICS
# ============================================================================

@login_required(login_url='tracker:login')
def analytics(request):
    """Portfolio analytics"""
    try:
        portfolio = request.user.portfolio
    except Portfolio.DoesNotExist:
        portfolio = Portfolio.objects.create(user=request.user)
    
    portfolio.calculate_totals()
    assets = portfolio.assets.all()
    
    # Statistics
    total_assets = assets.count()
    best_asset = max(assets, key=lambda x: x.get_gain_loss(), default=None) if assets else None
    worst_asset = min(assets, key=lambda x: x.get_gain_loss(), default=None) if assets else None
    
    # Asset type distribution
    asset_types_dict = {}
    for asset in assets:
        type_name = asset.asset_type.name if asset.asset_type else 'Other'
        if type_name not in asset_types_dict:
            asset_types_dict[type_name] = 0
        asset_types_dict[type_name] += float(asset.get_current_value())
    
    context = {
        'portfolio': portfolio,
        'assets': assets,
        'total_assets': total_assets,
        'best_asset': best_asset,
        'worst_asset': worst_asset,
        'asset_types': asset_types_dict,
    }
    
    return render(request, 'tracker/analytics.html', context)


# ============================================================================
# WATCHLIST
# ============================================================================

@login_required(login_url='tracker:login')
def watchlist_view(request):
    """View watchlist"""
    watchlist_items = Watchlist.objects.filter(user=request.user).select_related('asset')
    
    context = {
        'watchlist': watchlist_items,
    }
    
    return render(request, 'tracker/watchlist.html', context)


@login_required(login_url='tracker:login')
def watchlist_add(request, pk):
    """Add to watchlist"""
    asset = get_object_or_404(Asset, pk=pk)
    
    watchlist_item, created = Watchlist.objects.get_or_create(
        user=request.user,
        asset=asset
    )
    
    if created:
        messages.success(request, f'{asset.name} ditambahkan ke watchlist!')
    else:
        messages.info(request, f'{asset.name} sudah ada di watchlist!')
    
    return redirect('tracker:asset_detail', pk=pk)


@login_required(login_url='tracker:login')
def watchlist_remove(request, pk):
    """Remove dari watchlist"""
    watchlist_item = get_object_or_404(Watchlist, pk=pk, user=request.user)
    asset_name = watchlist_item.asset.name
    watchlist_item.delete()
    
    messages.success(request, f'{asset_name} dihapus dari watchlist!')
    return redirect('tracker:watchlist_view')


# ============================================================================
# PRICE ALERTS
# ============================================================================

@login_required(login_url='tracker:login')
def price_alert_list(request):
    """List price alerts"""
    alerts = PriceAlert.objects.filter(user=request.user)
    
    context = {
        'alerts': alerts,
    }
    
    return render(request, 'tracker/price_alert_list.html', context)


@login_required(login_url='tracker:login')
def price_alert_create(request, pk):
    """Create price alert"""
    asset = get_object_or_404(Asset, pk=pk, portfolio__user=request.user)
    
    if request.method == 'POST':
        condition = request.POST.get('condition')
        target_price = request.POST.get('target_price')
        
        if condition and target_price:
            PriceAlert.objects.create(
                user=request.user,
                asset=asset,
                condition=condition,
                target_price=target_price
            )
            messages.success(request, 'Price alert dibuat!')
            return redirect('tracker:asset_detail', pk=pk)
    
    return render(request, 'tracker/price_alert_form.html', {'asset': asset})


# ============================================================================
# TRANSACTIONS
# ============================================================================

@login_required(login_url='tracker:login')
def transaction_list(request, asset_pk):
    """List transactions untuk asset"""
    asset = get_object_or_404(Asset, pk=asset_pk, portfolio__user=request.user)
    transactions = asset.transactions.all()
    
    context = {
        'asset': asset,
        'transactions': transactions,
    }
    
    return render(request, 'tracker/transaction_list.html', context)


@login_required(login_url='tracker:login')
def transaction_create(request, asset_pk):
    """Create transaction"""
    asset = get_object_or_404(Asset, pk=asset_pk, portfolio__user=request.user)
    
    if request.method == 'POST':
        transaction_type = request.POST.get('transaction_type')
        quantity = request.POST.get('quantity')
        price = request.POST.get('price')
        notes = request.POST.get('notes')
        transaction_date = request.POST.get('transaction_date')
        
        if all([transaction_type, quantity, price, transaction_date]):
            total = float(quantity) * float(price)
            
            Transaction.objects.create(
                asset=asset,
                transaction_type=transaction_type,
                quantity=quantity,
                price=price,
                total=total,
                notes=notes,
                transaction_date=transaction_date
            )
            
            messages.success(request, 'Transaksi berhasil dicatat!')
            return redirect('tracker:transaction_list', asset_pk=asset_pk)
    
    context = {
        'asset': asset,
    }
    
    return render(request, 'tracker/transaction_form.html', context)


# ============================================================================
# USER SETTINGS & PROFILE
# ============================================================================

@login_required(login_url='tracker:login')
def settings(request):
    """User settings"""
    user = request.user
    try:
        profile = user.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # Update user info
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.save()
            
            messages.success(request, 'Profil berhasil diupdate!')
            return redirect('tracker:settings')
    else:
        form = ProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
    }
    
    return render(request, 'tracker/settings.html', context)


@login_required(login_url='tracker:login')
def change_password(request):
    """Change password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            
            if not user.check_password(old_password):
                messages.error(request, 'Password lama salah!')
                return redirect('tracker:change_password')
            
            user.set_password(new_password)
            user.save()
            
            # Re-login
            login(request, user)
            messages.success(request, 'Password berhasil diubah!')
            return redirect('tracker:settings')
    else:
        form = PasswordChangeForm()
    
    return render(request, 'tracker/change_password.html', {'form': form})


# ============================================================================
# VOUCHER SYSTEM
# ============================================================================

@login_required(login_url='tracker:login')
def voucher_list(request):
    """List available vouchers"""
    vouchers = Voucher.objects.filter(is_active=True)
    
    # Check which ones user already redeemed
    redeemed_codes = VoucherRedemption.objects.filter(
        user=request.user
    ).values_list('voucher__code', flat=True)
    
    context = {
        'vouchers': vouchers,
        'redeemed_codes': redeemed_codes,
    }
    
    return render(request, 'tracker/voucher_list.html', context)


@login_required(login_url='tracker:login')
def redeem_voucher(request):
    """Redeem voucher code"""
    if request.method == 'POST':
        form = VoucherRedemptionForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            
            try:
                voucher = Voucher.objects.get(code=code)
                
                # Check if already redeemed
                if VoucherRedemption.objects.filter(user=request.user, voucher=voucher).exists():
                    messages.error(request, 'Anda sudah redeem voucher ini!')
                    return redirect('tracker:redeem_voucher')
                
                # Create redemption
                VoucherRedemption.objects.create(user=request.user, voucher=voucher)
                voucher.current_uses += 1
                voucher.save()
                
                messages.success(request, f'Voucher berhasil di-redeem! Diskon: {voucher.discount_percentage}%')
                return redirect('tracker:voucher_list')
            
            except Voucher.DoesNotExist:
                messages.error(request, 'Kode voucher tidak ditemukan!')
    else:
        form = VoucherRedemptionForm()
    
    return render(request, 'tracker/redeem_voucher.html', {'form': form})


# ============================================================================
# ADMIN VIEWS
# ============================================================================

@login_required(login_url='tracker:login')
def voucher_manager(request):
    """Admin: Manage vouchers"""
    if not request.user.is_staff:
        messages.error(request, 'Anda tidak punya akses!')
        return redirect('tracker:dashboard')
    
    vouchers = Voucher.objects.all()
    
    context = {
        'vouchers': vouchers,
    }
    
    return render(request, 'tracker/voucher_manager.html', context)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@login_required(login_url='tracker:login')
def api_portfolio_data(request):
    """API: Get portfolio data as JSON"""
    try:
        portfolio = request.user.portfolio
    except Portfolio.DoesNotExist:
        return JsonResponse({'error': 'Portfolio not found'}, status=404)
    
    portfolio.calculate_totals()
    
    data = {
        'total_value': float(portfolio.total_value),
        'total_investment': float(portfolio.total_investment),
        'total_gain_loss': float(portfolio.total_gain_loss),
        'gain_loss_percentage': float(portfolio.gain_loss_percentage),
    }
    
    return JsonResponse(data)


@login_required(login_url='tracker:login')
def api_assets_data(request):
    """API: Get assets data as JSON"""
    try:
        portfolio = request.user.portfolio
    except Portfolio.DoesNotExist:
        return JsonResponse({'error': 'Portfolio not found'}, status=404)
    
    assets = portfolio.assets.all()
    
    data = []
    for asset in assets:
        data.append({
            'id': asset.id,
            'name': asset.name,
            'symbol': asset.symbol,
            'quantity': float(asset.quantity),
            'current_price': float(asset.current_price),
            'current_value': float(asset.get_current_value()),
            'gain_loss': float(asset.get_gain_loss()),
            'gain_loss_percentage': float(asset.gain_loss_percentage),
        })
    
    return JsonResponse({'assets': data})