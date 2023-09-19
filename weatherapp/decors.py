
from functools import wraps
from django.core.exceptions import PermissionDenied
def ajax_required(view):
    @wraps(view)
    def _wrapped_view(request, *args, **kwargs):
        if request.is_ajax():
            return view(request, *args, **kwargs)
        else:
            raise PermissionDenied()
    return _wrapped_view

