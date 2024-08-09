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

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username

class Sale(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    date = models.DateField()
    cash_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cash_out = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    till_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    till_out = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image = models.ImageField(upload_to='sales_images/', null=True, blank=True)

    def __str__(self):
        return f"{self.shop} - {self.date} - KSH {self.closing_balance}"