
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import RegisterView, ProfileView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', TokenObtainPairView.as_view()),  # login
    path('token/refresh/', TokenRefreshView.as_view()),  # refresh token
    path('profile/', ProfileView.as_view()),
]
