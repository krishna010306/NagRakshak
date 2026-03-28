from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(users)
admin.site.register(ambulance)
admin.site.register(volunteer)
admin.site.register(hospital)
admin.site.register(EmergencyAlert)