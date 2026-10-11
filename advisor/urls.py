from django.urls import path

from advisor import views

urlpatterns = [
    path('', views.advisor_home, name='advisor-home'),
    path('capabilities/', views.capabilities, name='advisor-capabilities'),
    path('summary/', views.summary, name='advisor-summary'),
    path('chat/', views.chat, name='advisor-chat'),
    path('convs/', views.conversations, name='advisor-convs'),
    path('convs/<int:conv_id>/', views.conversation_delete, name='advisor-conv-delete'),
    path('convs/<int:conv_id>/title/', views.conversation_title, name='advisor-conv-title'),
    path('convs/<int:conv_id>/messages/', views.conversation_messages, name='advisor-conv-messages'),
    path('share/email/', views.share_email, name='advisor-share-email'),
    path('share/pdf/', views.share_pdf, name='advisor-share-pdf'),
]
