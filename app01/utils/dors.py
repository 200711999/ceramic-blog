"""
    自定义装饰器
"""
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.conf import settings


def _is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def _wants_html(request):
    return request.method == 'GET' and request.accepts('text/html') and not _is_ajax(request)


def _unauthenticated_response(request):
    """未登录时：访问 HTML 页面则跳转到登录页，AJAX/接口请求返回 JSON。"""
    if _wants_html(request):
        return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")
    return JsonResponse({'code': 400, 'msg': '用户未登录，请先登录后操作'})


# 函数专用 登录装饰器
def is_login_func(func):
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)
        return func(request, *args, **kwargs)

    return inner


# 方法专用 登录装饰器
def is_login_method(func):
    def inner(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return _unauthenticated_response(request)
        return func(self, request, *args, **kwargs)

    return inner
