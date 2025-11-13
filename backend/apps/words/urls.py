from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.words_list_view, name='words-list'),
]

