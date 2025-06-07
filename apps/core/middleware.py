from uuid import uuid4
from threading import local

_thread_locals = local()


def get_current_request():
    return getattr(_thread_locals, "request", None)


def get_current_user():
    request = get_current_request()
    if request:
        return getattr(request, "user", None)
    return None


def get_current_user_id() -> int:
    user = get_current_user()
    if user and user.id:
        return user.id
    return 0


class PopulateLocalsThreadMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        _thread_locals.request = None
        return response
