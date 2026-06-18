from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View
from django.contrib import auth

from app01.forms.my_forms import RegisterForm, LoginForm
from app01.models import User, Blog
from app01.utils.dors import is_login_method


class Register(View):
    def get(self, request):
        return render(request, 'register.html', locals())

    def post(self, request):
        backend = {
            'code': 200,
            'msg': '注册成功',
        }

        username = request.POST['username']
        password = request.POST['password']
        re_password = request.POST['re_password']
        email = request.POST.get('email')
        site_title = request.POST.get('site_title')
        avatar = request.FILES.get('avatar')

        form = RegisterForm(request.POST)
        if not form.is_valid():
            backend['code'] = 400
            backend['msg'] = form.errors
            return JsonResponse(backend)

        form.cleaned_data.pop('re_password')
        if not avatar:
            avatar = 'avatar/default.png'

        form.cleaned_data['avatar'] = avatar
        form.cleaned_data.pop('site_title')

        blog_obj = Blog.objects.create(
            site_name=username,
            site_title=site_title,
        )
        User.objects.create_user(
            **form.cleaned_data, blog=blog_obj
        )

        return JsonResponse(backend)


class Login(View):
    def get(self, request):
        return render(request, 'login.html', locals())

    def post(self, request):
        backend = {
            'code': 400,
            'msg': '',
        }

        username = request.POST.get('username')
        password = request.POST.get('password')
        code = request.POST.get('code')

        if request.session.get('code').upper() != code.upper():
            backend['msg'] = {'code': ['验证码错误']}
            return JsonResponse(backend)

        form = LoginForm(request.POST)
        if not form.is_valid():
            backend['msg'] = form.errors
            return JsonResponse(backend)

        user_obj = auth.authenticate(username=username, password=password)
        if not user_obj:
            backend['msg'] = {'password': ['账号或密码错误']}
            return JsonResponse(backend)

        auth.login(request, user_obj)

        backend['code'] = 200
        backend['msg'] = '登录成功'
        return JsonResponse(backend)


class Logout(View):
    @is_login_method
    def get(self, request):
        auth.logout(request)
        return redirect('/login')


class SetPassword(View):
    @is_login_method
    def post(self, request):
        backend = {
            'code': 400,
            'msg': '',
        }

        user = request.user

        old_password = request.POST.get('old_password')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')

        if password != re_password:
            backend['msg'] = '两次密码不一致，请重新输入'
            return JsonResponse(backend)
        if not (old_password and password and re_password):
            backend['msg'] = '请填写完整信息'
            return JsonResponse(backend)

        if not user.check_password(old_password):
            backend['msg'] = '旧密码错误，请重新输入'
            return JsonResponse(backend)

        user.set_password(password)
        user.save()

        backend['code'] = 200
        backend['msg'] = '密码修改成功'
        return JsonResponse(backend)


class SetAvatar(View):
    @is_login_method
    def get(self, request):
        user_obj = request.user
        return render(request, 'set_avatar.html', locals())

    @is_login_method
    def post(self, request):
        user_obj = request.user
        avatar = request.FILES.get('avatar')
        user_obj.avatar = avatar
        user_obj.save()
        return redirect('index')


class EditProfile(View):
    @is_login_method
    def post(self, request):
        backend = {'code': 400, 'msg': ''}

        email = (request.POST.get('email') or '').strip()
        age = (request.POST.get('age') or '').strip()
        gender = (request.POST.get('gender') or '').strip()
        phone = (request.POST.get('phone') or '').strip()

        if email and ('@' not in email or '.' not in email):
            backend['msg'] = '邮箱格式不正确'
            return JsonResponse(backend)

        age_val = None
        if age:
            if not age.isdigit():
                backend['msg'] = '年龄必须为整数'
                return JsonResponse(backend)
            age_val = int(age)
            if not (1 <= age_val <= 150):
                backend['msg'] = '年龄需在 1~150 之间'
                return JsonResponse(backend)

        if phone and (not phone.isdigit() or len(phone) != 11):
            backend['msg'] = '手机号需为 11 位数字'
            return JsonResponse(backend)

        if len(gender) > 10:
            backend['msg'] = '性别字段过长'
            return JsonResponse(backend)

        user = request.user
        user.email = email
        user.age = age_val
        user.gender = gender or None
        user.phone = phone or None
        user.save()

        backend['code'] = 200
        backend['msg'] = '保存成功'
        return JsonResponse(backend)
