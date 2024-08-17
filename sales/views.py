from rest_framework import viewsets, generics
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from .models import Sale, Shop, UserProfile
from .serializers import SaleSerializer, ShopSerializer, UserProfileSerializer, UserSerializer
from django.db.models import Sum
from rest_framework_simplejwt.tokens import RefreshToken

class ShopViewSet(viewsets.ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                return super().get_queryset()
            else:
                try:
                    user_profile = user.userprofile
                    return super().get_queryset().filter(id=user_profile.shop.id)
                except UserProfile.DoesNotExist:
                    return Shop.objects.none()
        else:
            return super().get_queryset()

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    # Removed authentication_classes and permission_classes

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [AllowAny]  # Ensures that no authentication is required

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.is_superuser:
                return super().get_queryset()
            else:
                try:
                    user_profile = user.userprofile
                    return super().get_queryset().filter(shop=user_profile.shop)
                except UserProfile.DoesNotExist:
                    return Sale.objects.none()
        else:
            return super().get_queryset()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Create JWT tokens for the new user
        user = serializer.instance
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        headers = self.get_success_headers(serializer.data)
        return Response({
            'refresh': refresh_token,
            'access': access_token,
            'user': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)

class SaleListView(generics.ListCreateAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [AllowAny]  # Ensures that no authentication is required

class PerformanceListView(generics.ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [AllowAny]  # Ensures that no authentication is required

@api_view(['GET'])
def performance_summary_api(request):
    shops = Shop.objects.all()
    shop_data = []
    total_target = 100000  # Example target amount per day

    for shop in shops:
        total_days = Sale.objects.filter(shop=shop).values('date').distinct().count()
        total_cash_in = Sale.objects.filter(shop=shop).aggregate(Sum('cash_in'))['cash_in__sum'] or 0
        total_till_in = Sale.objects.filter(shop=shop).aggregate(Sum('till_in'))['till_in__sum'] or 0
        total_cash_out = Sale.objects.filter(shop=shop).aggregate(Sum('cash_out'))['cash_out__sum'] or 0
        total_till_out = Sale.objects.filter(shop=shop).aggregate(Sum('till_out'))['till_out__sum'] or 0
        total_cash = total_cash_in + total_till_in - total_cash_out - total_till_out

        # Avoid division by zero
        if total_days == 0:
            average_sales_per_day = 0
            sales_to_target_ratio = 0
        else:
            average_sales_per_day = total_cash / total_days
            sales_to_target_ratio = (total_cash / (total_target * total_days)) * 100

        profit_margin = 0  # Assuming you have a formula to calculate profit margin
        # Calculate profit margin if necessary
        if total_cash > 0:
            profit_margin = ((total_cash - total_cash_out - total_till_out) / total_cash) * 100

        shop_data.append({
            'shop': shop.name,
            'total_cash_in': total_cash_in,
            'total_till_in': total_till_in,
            'total_cash_out': total_cash_out,
            'total_till_out': total_till_out,
            'total_cash': total_cash,
            'average_sales_per_day': average_sales_per_day,
            'sales_to_target_ratio': sales_to_target_ratio,
            'profit_margin': profit_margin
        })

    # Your chart_data generation code goes here
    chart_data = {
        "labels": ["January", "February", "March"],  # Example labels
        "datasets": [
            {
                "label": "Sales Performance",
                "data": [1000, 2000, 1500],  # Example data
                "borderColor": "rgb(75, 192, 192)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "fill": True
            }
        ]
    }

    # Your alerts generation code goes here
    alerts = []  # Example alerts

    return Response({
        'shop_data': shop_data,
        'chart_data': chart_data,
        'alerts': alerts
    })
