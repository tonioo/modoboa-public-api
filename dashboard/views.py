"""Dashboard views."""

from collections import OrderedDict
import datetime

from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.views import generic

from django.contrib.auth import mixins as auth_mixins

from modoboa_public_api import models

MONTH_FORMAT = "%m%Y"


class DashboardView(auth_mixins.LoginRequiredMixin, generic.TemplateView):
    """Dashboard view."""

    template_name = "dashboard/base.html"

    def get_context_data(self, **kwargs):
        """Add data to context."""
        context = super(DashboardView, self).get_context_data(**kwargs)
        instances_per_version = OrderedDict()
        now = timezone.now()
        month = datetime.datetime.strptime(
            self.request.GET.get("month", now.strftime(MONTH_FORMAT)),
            MONTH_FORMAT)
        qset = models.ModoboaInstance.objects.filter(
            last_request__gte=now - relativedelta(months=1)).order_by(
                "known_version")
        active_instances = qset.count()
        for instance in qset:
            key = str(instance.known_version)
            if key not in instances_per_version:
                instances_per_version[key] = 0
            instances_per_version[key] += 1
        instances_per_version = [
            [str(version), counter]
            for version, counter in instances_per_version.items()]

        temp_dict = {}
        tz = timezone.get_current_timezone()
        from_datetime = tz.localize(month)
        end_date = (from_datetime + relativedelta(months=1, days=-1)).date()
        qset = models.ModoboaInstance.objects.filter(
            created__gte=from_datetime, created__date__lte=end_date)
        for instance in qset:
            date = instance.created.date()
            if date not in temp_dict:
                temp_dict[date] = 0
            temp_dict[date] += 1
        new_instances_per_day = OrderedDict()
        cur_date = from_datetime.date()
        while cur_date <= end_date:
            new_instances_per_day[cur_date.isoformat()] = (
                temp_dict.get(cur_date, 0))
            cur_date += relativedelta(days=1)
        prev_month = (month - relativedelta(months=1)).strftime("%m%Y")
        next_month = (month + relativedelta(months=1)).strftime("%m%Y")
        context.update({
            "month": month.strftime("%b %Y"),
            "prev_month": prev_month,
            "next_month": next_month,
            "instances": models.ModoboaInstance.objects.count(),
            "active_instances": active_instances,
            "new_instances_this_month": qset.count(),
            "average_instance_per_day": (
                qset.count() / (end_date - from_datetime.date()).days),
            "instances_per_version": instances_per_version,
            "new_instances_per_day": new_instances_per_day
        })
        return context
