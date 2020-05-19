from django.utils import timezone


class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = request.session.get('django_timezone', "UTC") or "UTC"
        timezone.activate(tz)

        response = self.get_response(request)
        return response
