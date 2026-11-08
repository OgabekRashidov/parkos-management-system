from django.contrib import admin
from .models import Vehicle, VehicleType, ParkingHistory, Settings

@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "price"]

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["plate", "vehicle_type", "enter_time"]

@admin.register(ParkingHistory)
class HistoryAdmin(admin.ModelAdmin):
    list_display  = ["plate", "vehicle_type", "hours", "price", "date"]
    list_filter   = ["date", "vehicle_type"]
    search_fields = ["plate"]

@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ["key", "value"]
