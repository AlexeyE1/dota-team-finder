from django.urls import path
from .views import CustomLogoutView, ProfileView

app_name = 'accounts'

urlpatterns = [
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/<slug:slug_profile>/', ProfileView.as_view(), name='profile'),
]