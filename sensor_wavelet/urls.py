from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
   
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('upload_signal/', views.upload_signal, name='upload_signal'),
    path('predict/<int:signal_id>/', views.predict_result, name='predict_result'),
    path('admin_train/', views.admin_train_dataset, name='admin_train'),
    path('view_history/', views.view_history, name='view_history'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('view_profile/', views.view_profile, name='view_profile'),
    path('predict_signal/', views.predict_signal, name='predict_signal'),
    path('logout/', views.logout_view, name='logout'),
    path('batch_predict/', views.batch_predict_signals, name='batch_predict'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('user_login/', views.user_login, name='user_login'),
    path('admin_logout/', views.admin_logout, name='admin_logout'),
    path('view_all_users/', views.view_all_users, name='view_all_users'),
    path('toggle_user/<int:user_id>/', views.toggle_user, name='toggle_user'),
    path('view_all_predictions/', views.view_all_predictions, name='view_all_predictions'),
    path('view_trained_models/', views.view_trained_models, name='view_trained_models'),
    path('admin_upload_dataset/', views.admin_upload_dataset, name='admin_upload_dataset'),


    path('user_register/', views.user_register, name='user_register'),

]
