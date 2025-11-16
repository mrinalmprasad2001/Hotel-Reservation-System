from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_categories/', views.manage_categories, name='manage_categories'),
    path('manage_rooms/', views.manage_rooms, name='manage_rooms'),
    path('edit_room/<int:room_id>/', views.edit_room, name='edit_room'),
    path('delete_room/<int:room_id>/', views.delete_room, name='delete_room'),
    path('manage_rates/', views.manage_rates, name='manage_rates'),
    path('confirm_booking/<int:room_id>/<str:start>/<str:end>/', views.confirm_booking, name='confirm_booking'),
    path('booking_success/', views.booking_success, name='booking_success')
]
