from django import forms

"""
    form只用于后端校验（不用前端标签生成）
"""
from app01.models import User
import re


# 注册表单类
class RegisterForm(forms.Form):
    # 用户名字段验证
    username = forms.CharField(label='用户名', min_length=2, max_length=8,
                               error_messages={
                                   'required': '用户名不能为空',
                                   'min_length': '用户名最少2位',
                                   'max_length': '用户名最多8位'
                               })
    password = forms.CharField(label='密码', min_length=3, max_length=12,
                               error_messages={
                                   'min_length': '密码不能少于3位',
                                   'max_length': '密码不能大于12位',
                                   'required': '密码不能为空'
                               })
    re_password = forms.CharField(label='确认密码', min_length=3, max_length=12,
                                  error_messages={
                                      'min_length': '确认密码不能少于3位',
                                      'max_length': '确认密码不能大于12位',
                                      'required': '确认密码不能为空'
                                  })
    email = forms.EmailField(label='邮箱', error_messages={
        'required': '邮箱不能为空',
        'invalid': '邮箱格式错误',
    })
    site_title = forms.CharField(label='站点标题', min_length=2, max_length=16,
                                 error_messages={
                                     'min_length': '站点标题不能2位',
                                     'max_length': '站点标题不能大于16位',
                                     'required': '站点标题不能为空',
                                 })

    # 局部钩子函数:clean_字段名(self) 该字段标准校验后执行的函数
    def clean_username(self):
        # 1.从self.cleaned_data 提取用户名字段值
        username = self.cleaned_data['username']
        # 2.用户名是否已经被注册(需要去数据库查询 ORM)
        user_obj = User.objects.filter(username=username).first()
        if user_obj:
            self.add_error('username', '用户名已被注册')
        # 3.用户名必须是 英文、数字、下划线组成
        if not re.match(r'^\w+$', username):
            self.add_error('username', '用户名必须是 英文、数字、下划线组成')

        return username

    # 全局沟子
    def clean(self):
        password = self.cleaned_data.get('password')
        re_password = self.cleaned_data.get('re_password')
        if password != re_password:
            self.add_error('re_password', '两次密码不一致')

        return self.cleaned_data


# 登录表单类
class LoginForm(forms.Form):
    # 用户名字段验证
    username = forms.CharField(label='用户名', min_length=2, max_length=8,
                               error_messages={
                                   'required': '用户名不能为空',
                                   'min_length': '用户名最少2位',
                                   'max_length': '用户名最多8位'
                               })
    password = forms.CharField(label='密码', min_length=3, max_length=12,
                               error_messages={
                                   'min_length': '密码不能少于3位',
                                   'max_length': '密码不能大于12位',
                                   'required': '密码不能为空'
                               })
