from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from parking import views as parking_views

urlpatterns = [
    path("admin/",    admin.site.urls),
    path("setup/",    parking_views.setup_admin,         name="setup_admin"),
    path("reset-admin/", parking_views.reset_superuser,  name="reset_superuser"),
    path("login/",    parking_views.login_page,          name="login"),
    path("login/operator/", parking_views.login_operator, name="login_operator"),
    path("login/superuser/", parking_views.login_superuser, name="login_superuser"),
    path("logout/",   auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("admin-panel/",                          parking_views.admin_panel,           name="admin_panel"),
    path("admin-panel/operators/add/",            parking_views.admin_add_operator,    name="admin_add_operator"),
    path("admin-panel/operators/<int:pk>/edit/",  parking_views.admin_edit_operator,   name="admin_edit_operator"),
    path("admin-panel/operators/<int:pk>/toggle/",parking_views.admin_toggle_operator, name="admin_toggle_operator"),
    path("admin-panel/operators/<int:pk>/switch/", parking_views.switch_user,   name="switch_user"),
    path("admin-panel/restore/",                   parking_views.restore_user,       name="restore_user"),
    path("admin-panel/edit-superuser/",            parking_views.admin_edit_superuser, name="admin_edit_superuser"),
    path("admin-panel/operators/<int:pk>/delete/",parking_views.admin_delete_operator, name="admin_delete_operator"),
    path("",          include("parking.urls")),
]
