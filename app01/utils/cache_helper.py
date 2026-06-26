from functools import wraps

from django.core.cache import cache
from django.views.decorators.cache import cache_page


def cache_page_for_anonymous(timeout, key_prefix=None):
    """仅对未登录用户缓存页面，登录用户始终执行原视图，避免缓存用户个性化内容。"""
    def decorator(view_func):
        cached_view = cache_page(timeout, key_prefix=key_prefix)(view_func)

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            return cached_view(request, *args, **kwargs)

        return wrapper

    return decorator


def clear_cache_patterns(*patterns):
    """按前缀清除 Redis 缓存，django-redis 支持 delete_pattern。"""
    for pattern in patterns:
        cache.delete_pattern(f"*{pattern}*")
