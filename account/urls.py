from django.urls import path
from django.contrib.auth import views as auth_views
from .views import SignUpView, ProfileView, EditProfileView, ForbiddenView

urlpatterns = [
    path('sign-up/', SignUpView.as_view(), name='sign-up'),
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='account/logout.html'), name='logout'),
    path('<int:pk>/profile/', ProfileView.as_view(), name='profile'),
    path('<int:pk>/edit-profile/', EditProfileView.as_view(), name='edit-profile'),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='account/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='account/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='account/password_reset_confirm.html'),
         name='password_reset_confirm'),
     path('mischievous-act/', ForbiddenView.as_view(), name='forbidden'),
] 
