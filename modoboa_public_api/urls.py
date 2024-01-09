"""API urls."""

from django.urls import path

from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register("instances", views.InstanceViewSet, basename="instance")
router.register("versions", views.VersionViewSet, basename="version")

# Legacy API
router.register(
    "extensions", views.ExtensionListViewSet, basename="extension")
urlpatterns = [
    path('current_version/', views.CurrentVersionView.as_view(),
         name="current_version"),
]

urlpatterns += router.urls
