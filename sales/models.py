from django.db import models
from django.conf import settings

class Shop(models.Model):
    SHOP_CHOICES = [
        ('cyber', 'Cyber'),
        ('milk_shop', 'Milk Shop'),
        ('retail_shop', 'Retail Shop'),
    ]

    name = models.CharField(max_length=100, choices=SHOP_CHOICES, unique=True)
    location = models.CharField(max_length=100)

    def __str__(self):
        return self.get_name_display()
    
    @property
    def total_sales(self):
        return self.sale_set.aggregate(total=models.Sum('amount'))['total'] or 0

    @property
    def total_expenses(self):
        return self.expense_set.aggregate(total=models.Sum('amount'))['total'] or 0

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Sale(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='sales_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.shop.get_name_display()} - {self.date}"

class Expense(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.shop.get_name_display()} - {self.date}"
