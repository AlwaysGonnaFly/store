from django.urls import path

from .views import auth, email_activation_send, email_activation, profile, deauth

app_name = 'user'

urlpatterns = [
    path('auth/', auth, name='auth'),
    path('auth/result', email_activation_send, name='email_activation_send'),
    path('auth/<uidb64>/<token>', email_activation, name='email_activation'),
    path('profile/', profile, name='profile'),
    path('auth/deauth', deauth, name='deauth'),
]
