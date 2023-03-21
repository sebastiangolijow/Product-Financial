from django.contrib import admin

from core_management.admin import HIDE_TAB

from .models import Bill


admin.site.register(Bill, HIDE_TAB)
