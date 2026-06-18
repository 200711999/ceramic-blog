"""
    视图函数也可以专门是一张图片
"""
from django.http import HttpResponse
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO  # BytesIO 二进制内存流

import random


# 返回一个随机的RGB元组
def random_color():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return (r, g, b)


# 获取验证码图片视图类
def get_code(request):
    if request.method == 'GET':
        """
            1.随机生成验证码值(random)
            2.根据验证码的值生成验证码图片(pillow)
            3.将验证码值保存到session中
            4.返回验证码图片二进制数据
        """
        # 1.创建常量
        width, height = 200, 40

        # 2.创建图片对象
        img = Image.new('RGB', (width, height), (255, 255, 255))
        # 3.创建字体对象
        font = ImageFont.truetype(r"static/font/aashenyeshitang.ttf", 20)
        # 4.创建画笔对象写字
        draw = ImageDraw.Draw(img)

        # 手动定义一个包含所有字母和数字的字符串
        all_char = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        list_code = random.choices(all_char, k=4)
        str_code = "".join(list_code)  # 将列表中元素连接转为字符串
        print("验证码随机字符串:", str_code)
        for i in range(4):
            draw.text((30 + 40 * i, 7), str_code[i], fill='red', font=font)

        # 随机生成300个点
        for i in range(300):
            x = random.randint(0, width)
            y = random.randint(0, height)
            draw.point((x, y), fill=random_color())

        # 随机20条线
        for i in range(15):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = random.randint(0, width), random.randint(0, height)
            draw.line((x1, y1, x2, y2), fill=random_color())

        # 为了下次在login的post请求中也能记住验证码值，通过session保存验证码值
        request.session['code'] = str_code

        # 利用内存 存储二进制图片数据
        io = BytesIO()  # 创建一个 内存流对象
        img.save(io, "PNG")  # 将图片保存到内存流中
        content = io.getvalue()  # 从内存中取出二进制数据
        return HttpResponse(content, content_type='image/png')
    else:
        return HttpResponse('请求方法错误')
