from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import AnonymousUser

class AdminSessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        is_admin = request.path.startswith('/admin/') or request.path.startswith('/Dashboard_')
        
        if is_admin:
            request.session_cookie_name = settings.ADMIN_SESSION_COOKIE_NAME
        else:
            request.session_cookie_name = settings.SESSION_COOKIE_NAME

        # Call parent process_request
        super().process_request(request)

        # Handle admin access control
        if is_admin and hasattr(request, 'user') and not request.user.is_staff:
            request.user = AnonymousUser()
            if hasattr(request, 'session'):
                request.session.flush()

    def process_response(self, request, response):
        is_admin = request.path.startswith('/admin/') or request.path.startswith('/Dashboard_')
        
        if is_admin:
            request.session_cookie_name = settings.ADMIN_SESSION_COOKIE_NAME
        else:
            request.session_cookie_name = settings.SESSION_COOKIE_NAME

        return super().process_response(request, response)