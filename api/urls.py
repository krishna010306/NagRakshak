from django.urls import path
from django.http import HttpResponse

from .views import (
    accept_request,
    ambulance_requests,
    get_driver_requests,
    get_hospitals,
    hospital_alerts,
    login_user,
    nearest_hospital,
    register_ambulance,
    register_user,
    register_volunteer,
    role_lookup,
    send_alert,
    smart_emergency,
    sos,
    users_endpoint,
    volunteer_requests,
)

def home(request):
    return HttpResponse("Backend is running 🚀")

urlpatterns = [
    path('login/', login_user),
    path('login-role/', role_lookup),
    path('user-role/', role_lookup),
    path('role/', role_lookup),
    path('sos/', sos),
    path('hospitals/', get_hospitals),
    path('signup/', register_user),
    path('register/', register_user),
    path('ambulance/register/', register_ambulance),
    path('volunteer/register/', register_volunteer),
    path('users/', users_endpoint),
    path('user/by-phone/', users_endpoint),
    path('user-create/', register_user),
    path('alert/', send_alert),
    path('nearest/', nearest_hospital),
    path('smart/', smart_emergency),
    path('driver-requests/', get_driver_requests),
    path('ambulance-request/', ambulance_requests),
    path('accept/', accept_request),
    path('volunteer/', volunteer_requests),
    path('hospital/', hospital_alerts),
    path('', home),
]