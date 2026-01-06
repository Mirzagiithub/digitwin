from django.utils.deprecation import MiddlewareMixin
from .threadlocals import set_request, clear_request


class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        set_request(request)

    def process_response(self, request, response):
        if request.user.is_authenticated:
            request.user.update_last_activity()
        clear_request()
        return response
