"""asambleasite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from asamblea import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('signup/init', views.init_signup, name='init_signup'),
    path('login/init', views.init_login, name='init_login'),
    path('profile/store/self', views.store_profile, name='store_profile'),
    path('profile/get/full', views.get_full_profile, name='get_full_profile'),
    path('profile/invite', views.next_invite, name='next_invite'),
    path('profile/store/intersection', views.store_intersection, name="store_intersection"),
    path('profile/get/requests', views.get_intersect_requests, name="get_intersect_requests"),
    path('profile/get/intersection', views.get_intersection, name="get_intersection"),
    path('profile/clear/request', views.clear_intersect_request, name="clear_intersect_request")
]
