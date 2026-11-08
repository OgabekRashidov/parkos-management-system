from django.urls import path
from . import views

urlpatterns = [
    path("",                            views.dashboard,           name="dashboard"),
    path("register/",                   views.register,            name="register"),
    path("enter/",                      views.enter_vehicle,       name="enter_vehicle"),
    path("exit/<str:plate>/",           views.exit_vehicle,        name="exit_vehicle"),
    path("history/",                    views.history,             name="history"),
    path("history/export/",             views.export_history_csv,  name="export_history"),
    path("report/",                     views.report,              name="report"),
    path("report/expense/",             views.add_expense,         name="add_expense"),
    path("report/reset/",               views.reset_finance,       name="reset_finance"),
    path("capacity/",                   views.set_capacity,        name="set_capacity"),
    path("types/",                      views.vehicle_types,       name="vehicle_types"),
    path("types/add/",                  views.add_vehicle_type,    name="add_vehicle_type"),
    path("types/<int:pk>/edit/",        views.edit_vehicle_type,   name="edit_vehicle_type"),
    path("types/<int:pk>/delete/",      views.delete_vehicle_type, name="delete_vehicle_type"),
    path("search/",                     views.search_vehicle,      name="search_vehicle"),
    path("profile/",                    views.profile,             name="profile"),
]
