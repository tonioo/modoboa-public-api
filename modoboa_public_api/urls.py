"""
API urls.
"""
from django.conf.urls import patterns, url

from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = patterns(
    '',
    url(r'^current_version/$', views.CurrentVersionView.as_view()),
    url(r'^extensions/$', views.ExtensionListView.as_view()),
)

urlpatterns = format_suffix_patterns(urlpatterns)
