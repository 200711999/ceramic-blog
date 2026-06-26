from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views import View

from app01.models import Article, Category, Tag, Comment, Follow, Notification
from app01.utils.dors import is_login_method
from app01.utils.text_similarity import find_most_similar_article
from app01.utils.image_processor import convert_base64_images
from app01.utils.cache_helper import clear_cache_patterns


class Backend(View):
    @is_login_method
    def get(self, request):
        user_obj = request.user
        blog = user_obj.blog

        article_queryset = Article.objects.filter(blog=blog, is_delete=False)
        category_queryset = Category.objects.filter(blog=blog)
        tag_queryset = Tag.objects.filter(blog=blog)
        comment_queryset = Comment.objects.filter(article__blog=blog).select_related('user', 'article')

        return render(request, 'backend/backend.html', locals())


class AddArticle(View):
    @is_login_method
    def get(self, request):
        user_obj = request.user
        blog = user_obj.blog
        category_queryset = Category.objects.filter(blog=blog)
        tag_queryset = Tag.objects.filter(blog=blog)
        return render(request, 'backend/add_article.html', locals())

    @is_login_method
    def post(self, request):
        user_obj = request.user
        blog = user_obj.blog

        title = (request.POST.get('title') or '').strip()
        content = (request.POST.get('content') or '').strip()
        category_id = request.POST.get('category_id')
        tag_id = request.POST.getlist('tag_id')
        status = request.POST.get('status', 'published')
        if status not in ('draft', 'published'):
            status = 'published'

        error = ''
        if not title:
            error = '标题不能为空'
        elif len(title) > 128:
            error = '标题不能超过 32 个字符'
        elif not content:
            error = '正文不能为空'
        elif not category_id:
            error = '请选择分类'

        if error:
            category_queryset = Category.objects.filter(blog=blog)
            tag_queryset = Tag.objects.filter(blog=blog)
            return render(request, 'backend/add_article.html', {
                'error': error,
                'title': request.POST.get('title', ''),
                'content': request.POST.get('content', ''),
                'category_id': category_id,
                'tag_id': tag_id,
                'category_queryset': category_queryset,
                'tag_queryset': tag_queryset,
            })

        SIMILARITY_THRESHOLD = 0.8
        existing_articles = Article.objects.filter(blog=blog).exclude(title=title)
        has_similar, similar_article, similarity = find_most_similar_article(
            content, existing_articles, threshold=SIMILARITY_THRESHOLD
        )

        if has_similar:
            category_queryset = Category.objects.filter(blog=blog)
            tag_queryset = Tag.objects.filter(blog=blog)
            similarity_percent = int(similarity * 100)
            error = f'检测到与文章《{similar_article.title}》的相似度为 {similarity_percent}%，超过阈值 {int(SIMILARITY_THRESHOLD * 100)}%，请修改内容后重试'
            return render(request, 'backend/add_article.html', {
                'error': error,
                'title': title,
                'content': content,
                'category_id': category_id,
                'tag_id': tag_id,
                'category_queryset': category_queryset,
                'tag_queryset': tag_queryset,
            })

        article_obj = Article.objects.create(
            title=title,
            content=convert_base64_images(content),
            blog=blog,
            category_id=category_id,
            status=status,
        )
        if tag_id:
            article_obj.tags.set(tag_id)

        # 通知所有关注者（仅已发布文章）
        if status == 'published':
            follower_ids = Follow.objects.filter(followed=user_obj).values_list('follower_id', flat=True)
            notifications = [
                Notification(recipient_id=fid, actor=user_obj, verb='published', article=article_obj)
                for fid in follower_ids
            ]
            Notification.objects.bulk_create(notifications)

        clear_cache_patterns('index', 'site', 'article')
        return redirect(f"/index/{user_obj.username}/p/{article_obj.pk}/")


class EditArticle(View):
    @is_login_method
    def get(self, request, article_id):
        user = request.user
        blog = user.blog
        article_obj = Article.objects.filter(id=article_id, blog=blog).first()
        if not article_obj:
            return redirect('/backend/')
        category_queryset = Category.objects.filter(blog=blog)
        tag_queryset = Tag.objects.filter(blog=blog)
        return render(request, 'backend/edit_article.html', locals())

    @is_login_method
    def post(self, request, article_id):
        user = request.user
        blog = user.blog

        title = (request.POST.get('title') or '').strip()
        content = (request.POST.get('content') or '').strip()
        category_id = request.POST.get('category_id')
        tag_id = request.POST.getlist('tag_id')

        article_obj = Article.objects.filter(pk=article_id, blog=blog).first()
        if not article_obj:
            return redirect('/backend/')

        error = ''
        if not title:
            error = '标题不能为空'
        elif len(title) > 128:
            error = '标题不能超过 32 个字符'
        elif not content:
            error = '正文不能为空'
        elif not category_id:
            error = '请选择分类'

        if error:
            category_queryset = Category.objects.filter(blog=blog)
            tag_queryset = Tag.objects.filter(blog=blog)
            return render(request, 'backend/edit_article.html', {
                'error': error,
                'article_obj': article_obj,
                'category_queryset': category_queryset,
                'tag_queryset': tag_queryset,
            })

        content_changed = (article_obj.content != content)
        if content_changed:
            SIMILARITY_THRESHOLD = 0.8
            other_articles = Article.objects.filter(blog=blog).exclude(pk=article_id)
            has_similar, similar_article, similarity = find_most_similar_article(
                content, other_articles, threshold=SIMILARITY_THRESHOLD
            )
            if has_similar:
                category_queryset = Category.objects.filter(blog=blog)
                tag_queryset = Tag.objects.filter(blog=blog)
                similarity_percent = int(similarity * 100)
                error = f'检测到与文章《{similar_article.title}》的相似度为 {similarity_percent}%，超过阈值 {int(SIMILARITY_THRESHOLD * 100)}%，请修改内容后重试'
                return render(request, 'backend/edit_article.html', {
                    'error': error,
                    'article_obj': article_obj,
                    'category_queryset': category_queryset,
                    'tag_queryset': tag_queryset,
                })

        article_obj.title = title
        article_obj.content = convert_base64_images(content)
        article_obj.category_id = category_id
        article_obj.status = request.POST.get('status', article_obj.status)
        article_obj.save()
        article_obj.tags.set(tag_id)
        clear_cache_patterns('index', 'site', 'article')
        return redirect(f"/index/{user.username}/p/{article_obj.pk}/")


class DeleteArticle(View):
    @is_login_method
    def post(self, request):
        user = request.user
        article_id = request.POST.get('article_id')
        article_obj = Article.objects.filter(pk=article_id, blog=user.blog).first()
        if not article_obj:
            return JsonResponse(
                {'code': 400, 'msg': '文章不存在或无权操作'}
            )

        article_obj.is_delete = True
        article_obj.save()
        clear_cache_patterns('index', 'site', 'article')
        return JsonResponse(
            {'code': 200, 'msg': '删除成功'}
        )


class EditUser(View):
    @is_login_method
    def post(self, request):
        username = request.POST.get('username')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')

        site_name = request.POST.get('site_name')
        site_title = request.POST.get('site_title')
        site_theme = request.FILES.get('site_theme')

        user = request.user
        blog = user.blog

        user.username = username
        user.age = age
        user.gender = gender
        user.phone = phone
        user.save()

        blog.site_title = site_title
        blog.site_name = site_name
        if site_theme:
            blog.site_theme = site_theme
        blog.save()

        return redirect('/backend/')


class AddCategory(View):
    @is_login_method
    def get(self, request):
        return render(request, 'backend/add_category.html', locals())

    @is_login_method
    def post(self, request):
        blog = request.user.blog
        name = (request.POST.get('name') or '').strip()
        error = ''
        if not name:
            error = '分类名称不能为空'
        elif len(name) > 10:
            error = '分类名称不能超过 10 个字符'
        elif Category.objects.filter(blog=blog, name=name).exists():
            error = '该分类已存在'
        if error:
            return render(request, 'backend/add_category.html', {'error': error, 'name': name})
        Category.objects.create(name=name, blog=blog)
        clear_cache_patterns('site')
        return redirect('/backend/')


class AddTag(View):
    @is_login_method
    def get(self, request):
        return render(request, 'backend/add_tag.html', locals())

    @is_login_method
    def post(self, request):
        blog = request.user.blog
        name = (request.POST.get('name') or '').strip()
        error = ''
        if not name:
            error = '标签名称不能为空'
        elif len(name) > 10:
            error = '标签名称不能超过 10 个字符'
        elif Tag.objects.filter(blog=blog, name=name).exists():
            error = '该标签已存在'
        if error:
            return render(request, 'backend/add_tag.html', {'error': error, 'name': name})
        Tag.objects.create(name=name, blog=blog)
        clear_cache_patterns('site')
        return redirect('/backend/')


class EditCategory(View):
    @is_login_method
    def post(self, request):
        blog = request.user.blog
        category_id = request.POST.get('category_id')
        name = (request.POST.get('name') or '').strip()

        if not name:
            return JsonResponse({'code': 400, 'msg': '分类名称不能为空'})
        if len(name) > 10:
            return JsonResponse({'code': 400, 'msg': '分类名称不能超过 10 个字符'})
        if Category.objects.filter(blog=blog, name=name).exclude(pk=category_id).exists():
            return JsonResponse({'code': 400, 'msg': '该分类已存在'})

        category_obj = Category.objects.filter(pk=category_id, blog=blog).first()
        if not category_obj:
            return JsonResponse({'code': 400, 'msg': '分类不存在'})

        category_obj.name = name
        category_obj.save()
        clear_cache_patterns('site')
        return JsonResponse({'code': 200, 'msg': '修改成功'})


class DeleteCategory(View):
    @is_login_method
    def post(self, request):
        blog = request.user.blog
        category_id = request.POST.get('category_id')

        category_obj = Category.objects.filter(pk=category_id, blog=blog).first()
        if not category_obj:
            return JsonResponse({'code': 400, 'msg': '分类不存在'})

        if Article.objects.filter(category=category_obj).exists():
            return JsonResponse({'code': 400, 'msg': '该分类下有文章，无法删除'})

        category_obj.delete()
        clear_cache_patterns('site')
        return JsonResponse({'code': 200, 'msg': '删除成功'})


class EditTag(View):
    @is_login_method
    def post(self, request):
        blog = request.user.blog
        tag_id = request.POST.get('tag_id')
        name = (request.POST.get('name') or '').strip()

        if not name:
            return JsonResponse({'code': 400, 'msg': '标签名称不能为空'})
        if len(name) > 10:
            return JsonResponse({'code': 400, 'msg': '标签名称不能超过 10 个字符'})
        if Tag.objects.filter(blog=blog, name=name).exclude(pk=tag_id).exists():
            return JsonResponse({'code': 400, 'msg': '该标签已存在'})

        tag_obj = Tag.objects.filter(pk=tag_id, blog=blog).first()
        if not tag_obj:
            return JsonResponse({'code': 400, 'msg': '标签不存在'})

        tag_obj.name = name
        tag_obj.save()
        clear_cache_patterns('site')
        return JsonResponse({'code': 200, 'msg': '修改成功'})


class DeleteTag(View):
    @is_login_method
    def post(self, request):
        blog = request.user.blog
        tag_id = request.POST.get('tag_id')

        tag_obj = Tag.objects.filter(pk=tag_id, blog=blog).first()
        if not tag_obj:
            return JsonResponse({'code': 400, 'msg': '标签不存在'})

        tag_obj.delete()
        clear_cache_patterns('site')
        return JsonResponse({'code': 200, 'msg': '删除成功'})


class ManageCommentDelete(View):
    @is_login_method
    def post(self, request):
        blog = request.user.blog
        comment_id = request.POST.get('comment_id')

        comment_obj = Comment.objects.filter(pk=comment_id, article__blog=blog).first()
        if not comment_obj:
            return JsonResponse({'code': 400, 'msg': '评论不存在'})

        article_obj = comment_obj.article
        comment_obj.delete()

        comment_num = Comment.objects.filter(article=article_obj).count()
        article_obj.comment_num = comment_num
        article_obj.save()
        clear_cache_patterns('article')

        return JsonResponse({'code': 200, 'msg': '删除成功', 'comment_num': comment_num})
