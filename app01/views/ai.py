import os
import uuid
from datetime import datetime

from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View

from app01.models import Category, Tag
from app01.utils.dors import is_login_method
from app01.utils.ai_helper import (
    call_ai_generate, call_ai_classify, call_ai_chat,
    call_ai_summarize, call_ai_continue,
)


class ImageUpload(View):
    """编辑器图片上传 — 支持拖拽、粘贴、点选"""
    @is_login_method
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'errno': 1, 'message': '未选择文件'})

        allowed = {'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'}
        if file.content_type not in allowed:
            return JsonResponse({'errno': 1, 'message': '仅支持 JPG / PNG / GIF / WebP 格式'})

        if file.size > 10 * 1024 * 1024:
            return JsonResponse({'errno': 1, 'message': '图片大小不能超过 10MB'})

        now = datetime.now()
        ext = os.path.splitext(file.name)[1] or '.jpg'
        filename = f"{uuid.uuid4().hex}{ext}"
        rel_dir = f"article_images/{now.year}/{now.month:02d}"

        save_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
        os.makedirs(save_dir, exist_ok=True)

        save_path = os.path.join(save_dir, filename)
        with open(save_path, 'wb+') as f:
            for chunk in file.chunks():
                f.write(chunk)

        url = '/' + '/'.join(
            [settings.MEDIA_URL.strip('/'), rel_dir, filename]
        )
        return JsonResponse({'errno': 0, 'data': {'url': url, 'alt': file.name, 'href': url}})


class AIAutoTag(View):
    @is_login_method
    def post(self, request):
        title = (request.POST.get('title') or '').strip()
        content = (request.POST.get('content') or '').strip()

        if not title and not content:
            return JsonResponse({'code': 400, 'msg': '请先填写标题或正文'})

        blog = request.user.blog
        categories = list(Category.objects.filter(blog=blog).values('id', 'name'))
        tags = list(Tag.objects.filter(blog=blog).values('id', 'name'))

        result = call_ai_classify(title=title, content=content, categories=categories, tags=tags)
        if result.get('error'):
            return JsonResponse({'code': 500, 'msg': result['error']})

        category_id = result.get('category_id')
        new_category_name = result.get('new_category_name')
        tag_ids = result.get('tag_ids', [])
        new_tag_names = result.get('new_tag_names', [])

        # Track newly created items so the frontend can insert them into the DOM
        new_category = None  # {id, name} or None

        if category_id is None and new_category_name:
            name = new_category_name.strip()[:10]
            existing = Category.objects.filter(blog=blog, name=name).first()
            if existing:
                category_id = existing.pk
            else:
                cat = Category.objects.create(blog=blog, name=name)
                category_id = cat.pk
                new_category = {'id': cat.pk, 'name': cat.name}

        new_tags = []  # [{id, name}, ...]
        for tag_name in new_tag_names:
            name = tag_name.strip()[:10]
            if not name:
                continue
            existing = Tag.objects.filter(blog=blog, name=name).first()
            if existing:
                if existing.pk not in tag_ids:
                    tag_ids.append(existing.pk)
            else:
                tag_obj = Tag.objects.create(blog=blog, name=name)
                tag_ids.append(tag_obj.pk)
                new_tags.append({'id': tag_obj.pk, 'name': tag_obj.name})

        return JsonResponse({
            'code': 200,
            'category_id': category_id,
            'tag_ids': tag_ids,
            'new_category': new_category,
            'new_tags': new_tags,
        })


class AIChat(View):
    def get(self, request):
        return render(request, 'ai_chat.html')

    def post(self, request):
        question = (request.POST.get('question') or '').strip()
        if not question:
            return JsonResponse({'code': 400, 'msg': '请输入问题'})

        if question == '__clear__':
            request.session['ai_chat_history'] = []
            return JsonResponse({'code': 200, 'answer': '对话已清空'})

        history = request.session.get('ai_chat_history', [])

        result = call_ai_chat(question=question, history=history)
        if result.get('error'):
            return JsonResponse({'code': 500, 'msg': result['error']})

        history.append({'role': 'user', 'content': question})
        history.append({'role': 'assistant', 'content': result['answer']})
        request.session['ai_chat_history'] = history[-20:]

        return JsonResponse({'code': 200, 'answer': result['answer']})


class AIGenerate(View):
    @is_login_method
    def post(self, request):
        keywords = (request.POST.get('keywords') or '').strip()
        style = request.POST.get('style', '干货帖子')
        existing = (request.POST.get('existing') or '').strip()
        wc_min = (request.POST.get('wc_min') or '').strip()
        wc_max = (request.POST.get('wc_max') or '').strip()

        if not keywords and not existing:
            return JsonResponse({'code': 400, 'msg': '请输入关键词或正文'})

        result = call_ai_generate(keywords=keywords, style=style, existing_content=existing, wc_min=wc_min, wc_max=wc_max)
        if result.get('error'):
            return JsonResponse({'code': 500, 'msg': result['error']})
        return JsonResponse({
            'code': 200,
            'title': result.get('title', ''),
            'content': result.get('content', ''),
        })


class AISummarize(View):
    @is_login_method
    def post(self, request):
        content = (request.POST.get('content') or '').strip()
        if not content:
            return JsonResponse({'code': 400, 'msg': '正文不能为空'})

        result = call_ai_summarize(content=content)
        if result.get('error'):
            return JsonResponse({'code': 500, 'msg': result['error']})
        return JsonResponse({
            'code': 200,
            'summary': result.get('summary', ''),
        })


class AIContinue(View):
    @is_login_method
    def post(self, request):
        content = (request.POST.get('content') or '').strip()
        if not content:
            return JsonResponse({'code': 400, 'msg': '正文不能为空'})

        result = call_ai_continue(content=content)
        if result.get('error'):
            return JsonResponse({'code': 500, 'msg': result['error']})
        return JsonResponse({
            'code': 200,
            'continuation': result.get('continuation', ''),
        })
