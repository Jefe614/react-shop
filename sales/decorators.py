# decorators.py

from django.core.exceptions import PermissionDenied

def manager_required(function):
    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied
        return function(request, *args, **kwargs)
    return wrap
