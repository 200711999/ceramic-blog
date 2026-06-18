"""
    自定义装饰圈
"""
from django.http import HttpResponse, JsonResponse

# 方法专用 登录装饰器
def is_login_func(func):
    def inner(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'code': 400, 'msg': '用户未登录，请先登录后操作'})
        return func(request, *args, **kwargs)

    return inner

# 函数专用 登录装饰器
def is_login_method(func):
    def inner(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'code': 400, 'msg': '用户未登录，请先登录后操作'})
        return func(self, request, *args, **kwargs)

    return inner
