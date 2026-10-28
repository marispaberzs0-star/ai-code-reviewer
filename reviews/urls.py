# reviews/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),                            # Galvenā vizītkarte
    path('reviews/', views.review_list, name='review_list'),       # Visi pārskati
    path('create/', views.review_create, name='review_create'),    # Jauna pārbaude
    path('register/', views.register, name='register'),            # Reģistrācija
    path('review/<int:pk>/', views.review_detail, name='review_detail'),
    path('review/<int:pk>/delete/', views.review_delete, name='review_delete'),
]