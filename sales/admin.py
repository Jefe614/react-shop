from django.contrib import admin
from .models import Shop, Sale, Expense, UserProfile

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('shop', 'date', 'amount', 'description', 'image')

admin.site.register(Shop)
admin.site.register(Expense)
admin.site.register(UserProfile)
