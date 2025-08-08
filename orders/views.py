from django.shortcuts import render

# Create your views here.


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Cart, Order, OrderItem
from products.models import Product
from .serializers import CartSerializer, OrderSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# --------- CART ---------
class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data)

    def post(self, request):
        request.data['user'] = request.user.id
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response({"detail": "Cart cleared."})

# --------- PLACE ORDER ---------
class PlaceOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"detail": "Cart is empty."}, status=400)

        total = 0
        for item in cart_items:
            if item.product.stock < item.quantity:
                return Response({"detail": f"{item.product.name} is out of stock."}, status=400)
            total += item.product.price * item.quantity

        order = Order.objects.create(user=request.user, total_price=total)

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart_items.delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=201)

# --------- USER ORDER HISTORY ---------
class UserOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

# --------- ADMIN UPDATE ORDER STATUS ---------
class UpdateOrderStatusView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "Order not found."}, status=404)

        status_ = request.data.get("status")
        if status_ not in dict(Order.STATUS_CHOICES):
            return Response({"detail": "Invalid status."}, status=400)

        order.status = status_
        order.save()

        # Notify user via WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{order.user.id}",
            {
                "type": "send_order_status",
                "order_id": order.id,
                "status": order.status
            }
        )

        return Response({"detail": f"Order status updated to {status_}."})
