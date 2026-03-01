from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    """Wrap every successful response in a consistent ``{"data": ...}`` envelope.

    Responses that already contain a ``data`` or ``count`` key (paginated, or
    manually wrapped in views) are left untouched.  Error responses (4xx/5xx)
    are also passed through as-is so DRF's standard error body is preserved.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        if response and response.status_code >= 400:
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and ("data" in data or "count" in data):
            return super().render(data, accepted_media_type, renderer_context)

        wrapped = {"data": data}
        return super().render(wrapped, accepted_media_type, renderer_context)
