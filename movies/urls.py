from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.movie_list, name='movie_list'),
    path('movie/<int:movie_id>/', views.theater_list, name='theater_list'),
    path('theater/<int:theater_id>/seats/book/', views.book_seats, name='book_seats'),
    path('pay/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
