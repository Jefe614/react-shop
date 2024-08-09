from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Sale, Shop, UserProfile
from .forms import SaleForm, CustomLoginForm, CustomUserCreationForm
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.http import HttpResponseForbidden, HttpResponse
import json
from decimal import Decimal
from django.db.models.functions import TruncMonth
import random
from django.contrib.auth.mixins import LoginRequiredMixin

# Login view
def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                return HttpResponseForbidden("User profile does not exist. Please contact support.")
            auth_login(request, user)
            return redirect('sale-list')
    else:
        form = CustomLoginForm()
    return render(request, 'registration/login.html', {'form': form})

# Signup view
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            auth_login(request, user)
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

# Sale list view
class SaleListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sale_list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        queryset = super().get_queryset()

        # If the user is not a superuser, filter by their assigned shop
        if not self.request.user.is_superuser:
            try:
                user_profile = self.request.user.userprofile
                queryset = queryset.filter(shop=user_profile.shop)
            except UserProfile.DoesNotExist:
                queryset = queryset.none()

        # Filter by shop if a shop is selected from the filter form
        shop_id = self.request.GET.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)

        # Sort the sales by date in descending order (most recent first)
        queryset = queryset.order_by('-date')

        return queryset

# Sale detail view
class SaleDetailView(DetailView):
    model = Sale
    template_name = 'sale_detail.html'
    context_object_name = 'sale'

# Sale create view
class SaleCreateView(CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sale_form.html'
    success_url = reverse_lazy('sale-list')

    def form_valid(self, form):
        # Check if the user is not a superuser
        if not self.request.user.is_superuser:
            try:
                # Get the shop associated with the user
                user_profile = self.request.user.userprofile
                shop_assigned_to_user = user_profile.shop

                # Check if the shop in the form matches the user's shop
                if form.instance.shop != shop_assigned_to_user:
                    form.add_error('shop', 'You are not allowed to add sales for this shop.')
                    return self.form_invalid(form)

            except UserProfile.DoesNotExist:
                # Handle the case where the user does not have a profile or shop assigned
                form.add_error(None, 'You do not have permission to add sales as you are not assigned to any shop.')
                return self.form_invalid(form)

        # If the user is a superuser or the shop matches, proceed as normal
        response = super().form_valid(form)
        messages.success(self.request, 'Sale successfully added.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Failed to add sale. Please correct the errors below.')
        return super().form_invalid(form)

# Sale update view
class SaleUpdateView(UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sale_form.html'
    success_url = reverse_lazy('sale-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Sale successfully updated.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Failed to update sale. Please correct the errors below.')
        return super().form_invalid(form)

# Sale delete view
class SaleDeleteView(DeleteView):
    model = Sale
    template_name = 'sale_confirm_delete.html'
    success_url = reverse_lazy('sale-list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Sale successfully deleted.')
        return response

# Shop performance view
@login_required
def performance(request):
    user = request.user
    target_amount = 30000  # Example target amount

    shop_data = []
    alerts = []
    monthly_sales = []

    def convert_decimal_to_float(decimal_value):
        return float(decimal_value) if isinstance(decimal_value, Decimal) else decimal_value

    def generate_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    if user.is_staff:
        shops = Shop.objects.all()

        for shop in shops:
            total_cash_in = Sale.objects.filter(shop=shop).aggregate(total=Sum('cash_in'))['total'] or Decimal('0.00')
            total_till_in = Sale.objects.filter(shop=shop).aggregate(total=Sum('till_in'))['total'] or Decimal('0.00')
            total_cash_out = Sale.objects.filter(shop=shop).aggregate(total=Sum('cash_out'))['total'] or Decimal('0.00')
            total_till_out = Sale.objects.filter(shop=shop).aggregate(total=Sum('till_out'))['total'] or Decimal('0.00')
            
            total_cash = (total_cash_in + total_till_in) - (total_cash_out + total_till_out)
            profit_loss = total_cash

            days = Sale.objects.filter(shop=shop).values('date').distinct().count()
            average_sales_per_day = round(convert_decimal_to_float(total_cash_in) / days) if days > 0 else 0
            sales_to_target_ratio = round((convert_decimal_to_float(total_cash_in) / target_amount) * 100, 2)
            profit_margin = round((convert_decimal_to_float(profit_loss) / convert_decimal_to_float(total_cash_in) * 100)) if total_cash_in > 0 else 0

            below_target = total_cash_in < target_amount
            if below_target:
                alerts.append(f'{shop.name}: Sales are below the target of KSH {target_amount}.')

            shop_data.append({
                'shop': shop.name,
                'total_cash_in': convert_decimal_to_float(total_cash_in),
                'total_till_in': convert_decimal_to_float(total_till_in),
                'total_cash_out': convert_decimal_to_float(total_cash_out),
                'total_till_out': convert_decimal_to_float(total_till_out),
                'total_cash': convert_decimal_to_float(total_cash),
                'profit_loss': convert_decimal_to_float(profit_loss),
                'average_sales_per_day': average_sales_per_day,
                'sales_to_target_ratio': sales_to_target_ratio,
                'profit_margin': profit_margin,
                'below_target': below_target,
                'color': generate_color()
            })

            sales_data = Sale.objects.filter(shop=shop)\
                .annotate(month=TruncMonth('date'))\
                .values('month')\
                .annotate(total_cash_in=Sum('cash_in'))\
                .order_by('month')\
                .values('month', 'total_cash_in')

            monthly_sales.append({
                'shop': shop.name,
                'sales': list(sales_data)
            })

    else:
        try:
            profile = UserProfile.objects.get(user=user)
            shop = profile.shop

            total_cash_in = Sale.objects.filter(shop=shop).aggregate(total=Sum('cash_in'))['total'] or Decimal('0.00')
            total_till_in = Sale.objects.filter(shop=shop).aggregate(total=Sum('till_in'))['total'] or Decimal('0.00')
            total_cash_out = Sale.objects.filter(shop=shop).aggregate(total=Sum('cash_out'))['total'] or Decimal('0.00')
            total_till_out = Sale.objects.filter(shop=shop).aggregate(total=Sum('till_out'))['total'] or Decimal('0.00')
            
            total_cash = (total_cash_in + total_till_in) - (total_cash_out + total_till_out)
            profit_loss = total_cash

            num_days = 30
            average_sales_per_day = round(convert_decimal_to_float(total_cash_in) / num_days)
            sales_to_target_ratio = round((convert_decimal_to_float(total_cash_in) / target_amount) * 100, 2)
            profit_margin = round((convert_decimal_to_float(profit_loss) / convert_decimal_to_float(total_cash_in) * 100)) if total_cash_in else 0

            below_target = total_cash_in < target_amount

            shop_data = [{
                'shop': shop.name,
                'total_cash_in': convert_decimal_to_float(total_cash_in),
                'total_till_in': convert_decimal_to_float(total_till_in),
                'total_cash_out': convert_decimal_to_float(total_cash_out),
                'total_till_out': convert_decimal_to_float(total_till_out),
                'total_cash': convert_decimal_to_float(total_cash),
                'profit_loss': convert_decimal_to_float(profit_loss),
                'average_sales_per_day': average_sales_per_day,
                'sales_to_target_ratio': sales_to_target_ratio,
                'profit_margin': profit_margin,
                'below_target': below_target,
                'color': generate_color()
            }]

            if below_target:
                alerts.append(f'Sales for your shop are below the target of KSH {target_amount}.')

            sales_data = Sale.objects.filter(shop=shop)\
                .annotate(month=TruncMonth('date'))\
                .values('month')\
                .annotate(total_cash_in=Sum('cash_in'))\
                .order_by('month')\
                .values('month', 'total_cash_in')

            monthly_sales.append({
                'shop': shop.name,
                'sales': list(sales_data)
            })

        except UserProfile.DoesNotExist:
            return HttpResponseForbidden("Only admin can access this page!!!")

    # Prepare chart data
    chart_data = {
        'labels': sorted({record['month'].strftime('%b %Y') for record in sales_data}),
        'datasets': []
    }

    for shop_sales in monthly_sales:
        shop_name = shop_sales['shop']
        shop_color = next((item['color'] for item in shop_data if item['shop'] == shop_name), '#000000')
        sales = [convert_decimal_to_float(record['total_cash_in']) for record in shop_sales['sales']]
        chart_data['datasets'].append({
            'label': shop_name,
            'data': sales,
            'borderColor': shop_color,
            'backgroundColor': shop_color + '33',  # Adding transparency to the background color
            'fill': False
        })

    context = {
        'shop_data': shop_data,
        'alerts': alerts,
        'target_amount': target_amount,
        'chart_data': json.dumps(chart_data)
    }
    return render(request, 'shop_performance.html', context)

# Export sales to CSV
