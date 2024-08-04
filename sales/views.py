from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from .models import Sale, Expense, Shop, UserProfile
from .forms import SaleForm, ExpenseForm, CustomLoginForm, CustomUserCreationForm
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.http import HttpResponseForbidden, HttpResponse
import csv
import json
from decimal import Decimal
from django.db.models.functions import TruncMonth
import random

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            try:
                UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                # Handle the missing UserProfile scenario
                return HttpResponseForbidden("User profile does not exist. Please contact support.")
            auth_login(request, user)
            return redirect('sale-list')  # Redirect to your desired page
    else:
        form = CustomLoginForm()
    return render(request, 'registration/login.html', {'form': form})
def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a UserProfile for the new user
            UserProfile.objects.create(user=user)
            auth_login(request, user)
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

class SaleListView(ListView):
    model = Sale
    template_name = 'sale_list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        queryset = super().get_queryset()
        shop_id = self.request.GET.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shops'] = Shop.objects.all()
        return context

class SaleDetailView(DetailView):
    model = Sale
    template_name = 'sale_detail.html'
    context_object_name = 'sale'

class ExpenseDetailView(DetailView):
    model = Expense
    template_name = 'expense_detail.html'
    context_object_name = 'expense'

class ExpenseListView(ListView):
    model = Expense
    template_name = 'expense_list.html'
    context_object_name = 'expenses'

    def get_queryset(self):
        queryset = super().get_queryset()
        shop_id = self.request.GET.get('shop')
        if shop_id:
            queryset = queryset.filter(shop_id=shop_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['shops'] = Shop.objects.all()
        return context

class SaleCreateView(CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'sale_form.html'
    success_url = reverse_lazy('sale-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Sale successfully added.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Failed to add sale. Please correct the errors below.')
        return super().form_invalid(form)

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

class ExpenseUpdateView(UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense_form.html'
    success_url = reverse_lazy('expense-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Expense successfully updated.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Failed to update expense. Please correct the errors below.')
        return super().form_invalid(form)

class ExpenseCreateView(CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense_form.html'
    success_url = reverse_lazy('expense-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Expense successfully added.')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Failed to add expense. Please correct the errors below.')
        return super().form_invalid(form)

class SaleDeleteView(DeleteView):
    model = Sale
    template_name = 'sale_confirm_delete.html'
    success_url = reverse_lazy('sale-list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Sale successfully deleted.')
        return response

class ExpenseDeleteView(DeleteView):
    model = Expense
    template_name = 'expense_confirm_delete.html'
    success_url = reverse_lazy('expense-list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'Expense successfully deleted.')
        return response

@login_required
def performance(request):
    user = request.user
    shops = Shop.objects.all()
    target_amount = 30000  # Example target amount

    shop_data = []
    alerts = []
    monthly_sales = {}
    expense_data = []

    def convert_decimal_to_float(decimal_value):
        return float(decimal_value) if isinstance(decimal_value, Decimal) else decimal_value

    def generate_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    if user.is_staff:
        for shop in shops:
            total_sales = Sale.objects.filter(shop=shop).aggregate(total=Sum('amount'))['total'] or 0
            total_expenses = Expense.objects.filter(shop=shop).aggregate(total=Sum('amount'))['total'] or 0
            profit_loss = total_sales - total_expenses

            days = Sale.objects.filter(shop=shop).values('date').distinct().count()
            average_sales_per_day = round(convert_decimal_to_float(total_sales) / days) if days > 0 else 0
            expense_ratio = round((convert_decimal_to_float(total_expenses) / convert_decimal_to_float(total_sales) * 100)) if total_sales > 0 else 0
            profit_margin = round((convert_decimal_to_float(profit_loss) / convert_decimal_to_float(total_sales) * 100)) if total_sales > 0 else 0

            below_target = total_sales < target_amount
            if below_target:
                alerts.append(f'{shop.name}: Sales are below the target of KSH {target_amount}.')

            shop_data.append({
                'shop': shop.name,  # Use `shop.name` directly
                'total_sales': convert_decimal_to_float(total_sales),
                'total_expenses': convert_decimal_to_float(total_expenses),
                'profit_loss': convert_decimal_to_float(profit_loss),
                'average_sales_per_day': average_sales_per_day,
                'expense_ratio': expense_ratio,
                'profit_margin': profit_margin,
                'below_target': below_target,
                'color': generate_color()
            })

            sales_data = Sale.objects.filter(shop=shop)\
                .annotate(month=TruncMonth('date'))\
                .values('month')\
                .annotate(total_sales=Sum('amount'))\
                .order_by('month')\
                .values('month', 'total_sales')

            monthly_sales[shop.id] = list(sales_data)  # Convert QuerySet to list

            expenses = Expense.objects.filter(shop=shop).values('description').annotate(total=Sum('amount'))
            expense_data.append({
                'shop': shop.name,  # Use `shop.name` directly
                'expenses': list(expenses)
            })

    else:
        try:
            profile = UserProfile.objects.get(user=user)
            shop = profile.shop
            total_sales = Sale.objects.filter(shop=shop).aggregate(total=Sum('amount'))['total'] or 0
            total_expenses = Expense.objects.filter(shop=shop).aggregate(total=Sum('amount'))['total'] or 0
            profit_loss = total_sales - total_expenses

            num_days = 30
            average_sales_per_day = round(convert_decimal_to_float(total_sales) / num_days)
            expense_ratio = round((convert_decimal_to_float(total_expenses) / convert_decimal_to_float(total_sales) * 100)) if total_sales else 0
            profit_margin = round((convert_decimal_to_float(profit_loss) / convert_decimal_to_float(total_sales) * 100)) if total_sales else 0

            below_target = total_sales < target_amount

            shop_data = [{
                'shop': shop.name,  # Use `shop.name` directly
                'total_sales': convert_decimal_to_float(total_sales),
                'total_expenses': convert_decimal_to_float(total_expenses),
                'profit_loss': convert_decimal_to_float(profit_loss),
                'average_sales_per_day': average_sales_per_day,
                'expense_ratio': expense_ratio,
                'profit_margin': profit_margin,
                'below_target': below_target,
                'color': generate_color()
            }]

            if below_target:
                alerts.append(f'Sales for your shop are below the target of KSH {target_amount}.')

            sales_data = Sale.objects.filter(shop=shop)\
                .annotate(month=TruncMonth('date'))\
                .values('month')\
                .annotate(total_sales=Sum('amount'))\
                .order_by('month')\
                .values('month', 'total_sales')

            monthly_sales[shop.id] = list(sales_data)  # Convert QuerySet to list

            expenses = Expense.objects.filter(shop=shop).values('description').annotate(total=Sum('amount'))
            expense_data.append({
                'shop': shop.name,  # Use `shop.name` directly
                'expenses': list(expenses)
            })

        except UserProfile.DoesNotExist:
            return HttpResponseForbidden("Only admin can access this page!!!")

    # Prepare chart data
    chart_data = {
        'labels': [],
        'datasets': []
    }
    months_set = set()
    for shop_id, sales_data in monthly_sales.items():
        shop = Shop.objects.get(id=shop_id)
        shop_name = shop.name  # Use `shop.name` directly
        shop_color = next((item['color'] for item in shop_data if item['shop'] == shop_name), '#000000')
        sales = [0] * len(sales_data)
        months = []
        for record in sales_data:
            month_str = record['month'].strftime('%b %Y')
            months.append(month_str)
            sales[months.index(month_str)] = convert_decimal_to_float(record['total_sales'])
            months_set.add(month_str)
        chart_data['labels'] = sorted(list(months_set))  # Ensure labels are sorted
        chart_data['datasets'].append({
            'label': shop_name,
            'data': [sales[chart_data['labels'].index(month)] for month in chart_data['labels']],
            'borderColor': shop_color,
            'backgroundColor': shop_color + '33',  # Adding transparency to the background color
            'fill': False
        })

    context = {
        'shop_data': shop_data,
        'alerts': alerts,
        'target_amount': target_amount,
        'chart_data': json.dumps(chart_data),  # Serialize to JSON for use in the template
        'expense_data': expense_data
    }
    return render(request, 'shop_performance.html', context)

def export_sales(request):
    # Create the HttpResponse object with the CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=sales.csv'

    writer = csv.writer(response)
    writer.writerow(['Shop', 'Date', 'Amount', 'Description', 'Image URL'])

    # Fetch sales data based on filters if needed
    sales = Sale.objects.all()
    if 'shop' in request.GET and request.GET['shop']:
        sales = sales.filter(shop_id=request.GET['shop'])
    if 'search' in request.GET and request.GET['search']:
        sales = sales.filter(description__icontains=request.GET['search'])
    
    for sale in sales:
        writer.writerow([
            sale.shop.name,
            sale.date,
            sale.amount,
            sale.description,
            sale.image.url if sale.image else ''
        ])

    return response
