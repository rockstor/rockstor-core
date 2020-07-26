"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from django.conf import settings
from django.db.models import Count
import rest_framework_custom as rfc


class GenericSProbeView(rfc.GenericView):
    content_negotiation_class = rfc.IgnoreClient

    def get_queryset(self):
        limit = self.request.query_params.get(
            "limit", settings.REST_FRAMEWORK["MAX_LIMIT"]
        )
        limit = int(limit)
        t1 = self.request.query_params.get("t1", None)
        t2 = self.request.query_params.get("t2", None)
        group_field = self.request.query_params.get("group", None)
        if group_field is not None:
            qs = []
            distinct_fields = self.model_obj.objects.values(group_field).annotate(
                c=Count(group_field)
            )
            filter_field = "%s__exact" % group_field
            for d in distinct_fields:
                qs.extend(
                    self.model_obj.objects.filter(
                        **{filter_field: d[group_field]}
                    ).order_by("-ts")[0:limit]
                )
            return qs
        if t1 is not None and t2 is not None:
            return self.model_obj.objects.filter(ts__gt=t1, ts__lte=t2)

        sort_col = self.request.query_params.get("sortby", None)
        if sort_col is not None:
            reverse = self.request.query_params.get("reverse", "no")
            if reverse == "yes":
                reverse = True
            else:
                reverse = False
            return self._sorted_results(sort_col, reverse)
        return self.model_obj.objects.all().order_by("-ts")[0:limit]
