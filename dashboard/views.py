"""Dashboard views."""

import datetime

from dateutil.relativedelta import relativedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.views import generic

from django.contrib.auth import mixins as auth_mixins

from modoboa_public_api import models

from . import tools

MONTH_FORMAT = "%m%Y"

# Instances older than this one do not report any statistic.
MIN_STATS_VERSION = (1, 6, 0)


class DashboardView(auth_mixins.LoginRequiredMixin, generic.TemplateView):
    """Dashboard view."""

    template_name = "dashboard/base.html"

    def get_requested_month(self, now):
        """Return the month to display, ignoring an invalid GET parameter."""
        raw_month = self.request.GET.get("month")
        if raw_month:
            try:
                month = datetime.datetime.strptime(raw_month, MONTH_FORMAT)
            except ValueError:
                pass
            else:
                # Keep the value in a range relativedelta can safely walk.
                if 2000 <= month.year <= now.year + 1:
                    return month
        return datetime.datetime(now.year, now.month, 1)

    def get_context_data(self, **kwargs):
        """Add data to context."""
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        month = self.get_requested_month(now)
        # "Active instance" is defined once, by the model manager.
        version_counts = list(
            models.ModoboaInstance.objects.active()
            .values("known_version")
            .annotate(instance_count=Count("id"))
            .order_by("-instance_count")
        )
        instances_per_version = [
            [str(item["known_version"]), item["instance_count"]]
            for item in version_counts[:5]
        ]
        active_instances = sum(
            item["instance_count"] for item in version_counts)
        # known_version is free-form text, so versions must be compared as
        # tuples: "1.10.0" >= "1.6.0" is false for a plain string comparison.
        instances_sending_stats = sum(
            item["instance_count"] for item in version_counts
            if tools.version_tuple(item["known_version"]) >= MIN_STATS_VERSION
        )

        from_datetime = timezone.make_aware(month)
        end_date = min(
            (from_datetime + relativedelta(months=1, days=-1)).date(),
            now.date())
        day_counts = dict(
            models.ModoboaInstance.objects
            .filter(created__gte=from_datetime, created__date__lte=end_date)
            .annotate(day=TruncDate("created"))
            .values("day")
            .annotate(day_count=Count("id"))
            .values_list("day", "day_count")
        )
        new_instances_per_day = {}
        cur_date = from_datetime.date()
        while cur_date <= end_date:
            new_instances_per_day[cur_date.isoformat()] = (
                day_counts.get(cur_date, 0))
            cur_date += relativedelta(days=1)
        new_instances_this_month = sum(day_counts.values())
        prev_month = (month - relativedelta(months=1)).strftime("%m%Y")
        next_month = (month + relativedelta(months=1)).strftime("%m%Y")
        counters = models.ModoboaInstance.objects.all().aggregate(
            total=Count("pk"),
            domain_counter=Sum("domain_counter"),
            mailbox_counter=Sum("mailbox_counter"),
            alias_counter=Sum("alias_counter"),
        )

        extension_counters = []
        extensions = models.ModoboaExtension.objects.extensions().annotate(
            total=Count("modoboainstance"))
        for extension in extensions:
            extension_counters.append([str(extension.name), extension.total])

        services, period = tools.parse_access_logs()
        hits_by_service = []
        ips_by_service = []
        total_hits = 0
        for service, stats in services.items():
            total_hits += stats["total"]
            hits_by_service.append([service, stats["total"]])
            ips_by_service.append([service, len(stats["ips"])])
        duration = (period[1] - period[0]).total_seconds() if period else 0
        # A duration of 0 means every hit happened within the same second.
        hits_by_second = total_hits / duration if duration else total_hits
        # The daily serie is inclusive on both ends, hence the + 1.
        nb_days = max((end_date - from_datetime.date()).days + 1, 1)
        context.update({
            "month": month.strftime("%b %Y"),
            "prev_month": prev_month,
            "next_month": next_month,
            "counters": counters,
            "active_instances": active_instances,
            "instances_sending_stats": instances_sending_stats,
            "new_instances_this_month": new_instances_this_month,
            "average_instance_per_day": new_instances_this_month / nb_days,
            "instances_per_version": instances_per_version,
            "new_instances_per_day": new_instances_per_day,
            "extension_counters": extension_counters,
            "hits_by_service": hits_by_service,
            "ips_by_service": ips_by_service,
            "hits_by_second": hits_by_second,
            "logs_period": period
        })
        return context
