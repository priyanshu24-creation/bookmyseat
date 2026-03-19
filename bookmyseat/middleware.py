import logging
from functools import partial

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import DatabaseError, OperationalError
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject


logger = logging.getLogger(__name__)
AUTH_DATABASE_ERRORS = (OperationalError, DatabaseError)


def _safe_get_user(request):
    try:
        if not hasattr(request, "_cached_user"):
            request._cached_user = auth.get_user(request)
        return request._cached_user
    except AUTH_DATABASE_ERRORS:
        logger.warning(
            "Authentication lookup failed; treating the request as anonymous.",
            exc_info=True,
        )
        request._cached_user = AnonymousUser()
        return request._cached_user


async def _safe_aget_user(request):
    try:
        if not hasattr(request, "_acached_user"):
            request._acached_user = await auth.aget_user(request)
        return request._acached_user
    except AUTH_DATABASE_ERRORS:
        logger.warning(
            "Async authentication lookup failed; treating the request as anonymous.",
            exc_info=True,
        )
        request._acached_user = AnonymousUser()
        return request._acached_user


class SafeAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The Django authentication middleware requires session middleware "
                "to be installed before it."
            )

        request.user = SimpleLazyObject(lambda: _safe_get_user(request))
        request.auser = partial(_safe_aget_user, request)
