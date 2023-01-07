from django.urls import path

from .views import index, good, purchase, order, gift, support, guarantees, how, privacy, confidentiality, terms

app_name = 'shop'

urlpatterns = [
    path('', index, name='index'),
    path('goods/<int:good_pk>/', good, name='good'),
    path('purchase/g/<int:good_pk>/', purchase, name='purchase'),
    path('purchase/g/<slug:slug>/', order, name='order'),

    path('gift/', gift, name='gift'),
    path('support/', support, name='support'),
    path('guarantees/', guarantees, name='guarantees'),
    path('how/', how, name='how'),
    path('privacy/', privacy, name='privacy'),
    path('confidentiality/', confidentiality, name='confidentiality'),
    path('terms/', terms, name='terms'),
]
