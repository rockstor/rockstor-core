"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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

from rest_framework.renderers import JSONRenderer
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.utils import encoders
from django.http.multipartparser import parse_header
import json
from rest_framework.utils.mediatypes import (order_by_precedence,
                                             media_type_matches)
from rest_framework.utils.mediatypes import _MediaType
from rest_framework import exceptions


class DownloadRenderer(JSONRenderer):
    media_type = 'application/rockstor-probedata'
    format = 'json'
    encoder_class = encoders.JSONEncoder

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `obj` into json.
        """
        if data is None:
            return ''

        indent = renderer_context.get('indent', None)
        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result.
            base_media_type, params = parse_header(accepted_media_type)
            indent = params.get('indent', indent)
            try:
                indent = max(min(int(indent), 8), 0)
            except (ValueError, TypeError):
                indent = None

        return json.dumps(data, cls=self.encoder_class, indent=indent)


class IgnoreClient(DefaultContentNegotiation):

    def select_renderer(self, request, renderers, format_suffix=None):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).
        """
        if (request.GET.get('download') is not None):
            r = DownloadRenderer()
            return (r, r.media_type)

        # Allow URL style format override.  eg. "?format=json
        format_query_param = self.settings.URL_FORMAT_OVERRIDE
        format = format_suffix or request.GET.get(format_query_param)

        if format:
            renderers = self.filter_renderers(renderers, format)

        accepts = self.get_accept_list(request)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) *
        #     len(self.renderers)
        for media_type_set in order_by_precedence(accepts):
            for renderer in renderers:
                for media_type in media_type_set:
                    if media_type_matches(renderer.media_type, media_type):
                        # Return the most specific media type as accepted.
                        if (_MediaType(renderer.media_type).precedence >
                                _MediaType(media_type).precedence):
                            # Eg client requests '*/*'
                            # Accepted media type is 'application/json'
                            return renderer, renderer.media_type
                        else:
                            # Eg client requests 'application/json; indent=8'
                            # Accepted media type is 'application/json;
                            # indent=8'
                            return renderer, media_type

        raise exceptions.NotAcceptable(available_renderers=renderers)

    def select_renderer2(self, request, renderers, format_suffix):
        download = request.GET.get('download')
        if (download is not None):
            r = DownloadRenderer()
            return (r, r.media_type)
        f = request.GET.get('format')
        if (f is not None and f == 'json'):
            return (renderers[0], renderers[0].media_type)
        return (renderers[1], renderers[1].media_type)
