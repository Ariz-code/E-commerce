from django.urls import path
from .views import CartView, PlaceOrderView, UserOrdersView, UpdateOrderStatusView

urlpatterns = [
    path('cart/', CartView.as_view()),
    path('place-order/', PlaceOrderView.as_view()),
    path('my-orders/', UserOrdersView.as_view()),
    path('update-status/<int:order_id>/', UpdateOrderStatusView.as_view()),
]


