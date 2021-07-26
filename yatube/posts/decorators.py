from functools import wraps
from django.db.models import F
from django.db import transaction

from .models import PageHit


def counted(f):
    @wraps(f)
    def decorator(request, *args, **kwargs):
        with transaction.atomic():
            if request.user.is_authenticated:
                counter, created = PageHit.objects.get_or_create(
                    client=request.user, url=request.path
                )
                counter.count = F('count') + 1
                counter.save()
        return f(request, *args, **kwargs)
    return decorator
