from django.urls import path
from .views import RegisterView, UserListView, users_page, add_user,LoginView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users-page/', users_page, name='users-page'),
    path('add-user/', add_user, name='add-user'),
    path('login/', LoginView.as_view(), name='login'),
]
