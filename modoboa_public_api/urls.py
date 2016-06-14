"""API urls."""

from django.conf.urls import url

from rest_framework import routers

from . import views


router = routers.SimpleRouter()
router.register("instances", views.InstanceViewSet, base_name="instance")
router.register("versions", views.VersionViewSet, base_name="version")

# Legacy API
router.register(
    "extensions", views.ExtensionListViewSet, base_name="extension")
urlpatterns = [
    url(r'^current_version/$', views.CurrentVersionView.as_view(),
        name="current_version"),
]

urlpatterns += router.urls
