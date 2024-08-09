from django.urls import path
from .views import (
    SaleListView, SaleCreateView, SaleDetailView, 
    SaleUpdateView, SaleDeleteView,signup_view
)
from .views import performance
from django.contrib.auth import views as auth_views

urlpatterns = [
        path('', SaleListView.as_view(), name='sale-list'),
    path('sales/new/', SaleCreateView.as_view(), name='sale-create'),
    path('sales/<int:pk>/', SaleDetailView.as_view(), name='sale-detail'),
    path('sales/<int:pk>/edit/', SaleUpdateView.as_view(), name='sale-update'),
    path('sales/<int:pk>/delete/', SaleDeleteView.as_view(), name='sale-delete'),
    path('performance/', performance, name='shop-performance'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup_view, name='signup'),


]
