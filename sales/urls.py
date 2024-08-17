from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ShopViewSet,
    UserProfileViewSet,
    SaleViewSet,
    RegisterView,
    SaleListView,
    performance_summary_api
)

router = DefaultRouter()
router.register(r'shops', ShopViewSet, basename='shop')
router.register(r'userprofiles', UserProfileViewSet, basename='userprofile')
router.register(r'sales', SaleViewSet, basename='sale')

urlpatterns = [
    path('', include(router.urls)),
    path('signup/', RegisterView.as_view(), name='signup'),
    path('sales-list/', SaleListView.as_view(), name='sale-list'),
    path('api/performance/', performance_summary_api, name='performance-summary-api'),


]
