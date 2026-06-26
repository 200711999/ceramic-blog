from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.db.models import F, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import method_decorator

from app01.models import User, Blog, Article, UpAndDown, Comment, Follow
from app01.utils.dors import is_login_method
from app01.utils.cache_helper import cache_page_for_anonymous, clear_cache_patterns


@method_decorator(cache_page_for_anonymous(60 * 5, key_prefix='index'), name='get')
class Index(View):
    def get(self, request):
        user = request.user
        q = (request.GET.get('q') or '').strip()
        sort = request.GET.get('sort', 'latest')
        if sort not in ('latest', 'hot'):
            sort = 'latest'

        article_queryset = Article.objects.filter(is_delete=False, status='published')
        if q:
            article_queryset = article_queryset.filter(
                Q(title__icontains=q) | Q(content__icontains=q) | Q(tags__name__icontains=q)
            ).distinct()

        if sort == 'hot':
            article_queryset = article_queryset.annotate(
                hot_score=F('up_num') * 3 + F('comment_num') * 2 + F('view_count')
            ).order_by('-hot_score', '-create_time')
        else:
            article_queryset = article_queryset.order_by('-create_time')

        followed_articles = []
        if user.is_authenticated and not q:
            followed_ids = Follow.objects.filter(follower=user).values_list('followed_id', flat=True)
            if followed_ids:
                followed_articles = Article.objects.filter(
                    blog__user__pk__in=followed_ids,
                    is_delete=False, status='published',
                ).select_related('blog', 'blog__user').order_by('-create_time')[:5]

        total = article_queryset.count()

        query_params = f'sort={sort}'
        if q:
            query_params += f'&q={q}'

        per_page = 10
        paginator = Paginator(article_queryset, per_page)
        page_number = request.GET.get('page') or 1
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        current = page_obj.number
        total_pages = paginator.num_pages
        window = 2
        start = max(1, current - window)
        end = min(total_pages, current + window)
        page_range = list(range(start, end + 1))
        show_first = start > 1
        show_first_ellipsis = start > 2
        show_last = end < total_pages
        show_last_ellipsis = end < total_pages - 1

        article_queryset = page_obj.object_list

        return render(request, 'index.html', locals())


@method_decorator(cache_page_for_anonymous(60 * 15, key_prefix='exhibition'), name='get')
class Exhibition(View):
    def get(self, request):
        NEW_IMGS = [
        'image/show/08bcc8619da15841e5aa61dfe57ec74f.jpg',
        'image/show/18bd9fe8a237fecc57204213c1328450.jpg',
        'image/show/2c8e1f49a4f67ad56657a3dfe2e71c93.jpg',
        'image/show/3b12bc46d0035a3ef30c6f5702449ad9.jpg',
        'image/show/5bc6c730ed2d3cadb26c4eb4e0df6b91.jpg',
        'image/show/7ae53568e6275529e22ab34d920da2d5.jpg',
        'image/show/96ec779f16ac1641472842f10ca10ebd.jpg',
        'image/show/d47ff5556cb210646a12b660795e0225.jpg',
    ]
        items = [
        {
            'id': 1,
            'title': '青瓷梅瓶',
            'desc': '龙泉窑青瓷，梅子青色温润如玉，小口丰肩，造型典雅。',
            'cover': 'image/show/1.jpg',
            'model': 'models/exhibit_1.glb',
        },
        {
            'id': 2,
            'title': '青瓷斗笠碗',
            'desc': '形如斗笠，釉色青翠，线条简洁流畅，宋人点茶之器。',
            'cover': 'image/show/2.jpg',
            'model': 'models/exhibit_2.glb',
        },
        {
            'id': 3,
            'title': '青瓷刻花盖罐',
            'desc': '器型饱满，刻花精细，釉层肥厚，青瓷艺术之佳作。',
            'cover': 'image/show/3.jpg',
            'model': 'models/exhibit_3.glb',
        },
        {
            'id': 4,
            'title': '青瓷刻花平盘',
            'desc': '盘面开阔，刻花纹饰细腻，釉色莹润如玉。',
            'cover': 'image/show/4.jpg',
            'model': 'models/exhibit_4.glb',
        },
        {
            'id': 5,
            'title': '定窑白瓷小杯',
            'desc': '定窑白釉，胎薄质细，釉色白中泛黄，古朴典雅。',
            'cover': 'image/show/5.jpg',
            'model': 'models/exhibit_5.glb',
        },
        {
            'id': 6,
            'title': '青花瓷',
            'desc': '青花发色浓艳，纹饰精美，白釉蓝彩，相得益彰。',
            'cover': 'image/show/6.png',
            'model': 'models/exhibit_6.glb',
        },
        {
            'id': 7,
            'title': '陶瓷艺术摆件',
            'desc': '高精度三维模型，光影质感细腻，展台陈列之佳品。',
            'cover': 'image/show/7.jpg',
            'model': 'models/exhibit_7.glb',
        },
        {
            'id': 8,
            'title': '陶瓷艺术器皿',
            'desc': '高精度三维模型，材质还原真实，细节层次丰富。',
            'cover': 'image/show/8.jpg',
            'model': 'models/exhibit_8.glb',
        },
        {
            'id': 9,
            'title': '陶瓷艺术瓶器',
            'desc': '高精度三维模型，釉面光泽自然，沉浸式三维鉴赏。',
            'cover': 'image/show/9.jpg',
            'model': 'models/exhibit_9.glb',
        },
        {
            'id': 10,
            'title': '陶瓷艺术雕塑',
            'desc': '高精度三维模型，纹理贴图完整，质感表现力强。',
            'cover': 'image/show/10.jpg',
            'model': 'models/exhibit_10.glb',
        },
        {
            'id': 11,
            'title': '紫砂茶壶',
            'desc': '宜兴紫砂，泥质细腻，深红泥质，壶身圆润，泡茶利器。',
            'cover': 'image/show/11.jpg',
            'model': 'models/exhibit_11.glb',
        },
        {
            'id': 12,
            'title': '釉里红高足杯',
            'desc': '元代釉里红，红中泛紫，极为罕见，烧制难度极高。',
            'cover': 'image/show/12.jpg',
            'model': 'models/exhibit_12.glb',
        },
        {
            'id': 13,
            'title': '斗彩鸡缸杯',
            'desc': '明代成化斗彩，色彩艳丽，小巧玲珑，拍卖天价传奇。',
            'cover': 'image/show/13.jpg',
            'model': 'models/exhibit_13.glb',
        },
        {
            'id': 14,
            'title': '龙泉青瓷梅瓶',
            'desc': '南宋龙泉窑，小口丰肩，釉层肥厚，梅子青色温润如玉。',
            'cover': 'image/show/14.jpg',
            'model': 'models/exhibit_14.glb',
        },
    ]
        return render(request, 'exhibition.html', {'items': items})


@method_decorator(cache_page_for_anonymous(60 * 5, key_prefix='site'), name='get')
class Site(View):
    def get(self, request, username, condition=None, value=None):
        user_obj = User.objects.filter(username=username).first()
        if not user_obj:
            return render(request, 'error.html', {'error_type': 'site_not_found', 'error_message': '该站点不存在'}, status=404)
        blog = user_obj.blog
        is_own = request.user.is_authenticated and request.user.pk == user_obj.pk
        article_queryset = blog.articles.filter(is_delete=False)
        if not is_own:
            article_queryset = article_queryset.filter(status='published')

        if condition and value:
            if condition == 'tag':
                article_queryset = article_queryset.filter(tags__pk=value)
            elif condition == 'category':
                article_queryset = article_queryset.filter(category__pk=value)
            else:
                year, month = value.split("-")
                article_queryset = article_queryset.filter(create_time__year=year, create_time__month=month)

        liked_articles = []
        if is_own:
            liked_articles = (
                Article.objects.filter(
                    upanddown__user=request.user,
                    upanddown__is_up=True,
                    is_delete=False,
                ).distinct().order_by('-create_time')[:10]
            )

        follower_count = Follow.objects.filter(followed=user_obj).count()
        following_count = Follow.objects.filter(follower=user_obj).count()
        is_following = request.user.is_authenticated and Follow.objects.filter(
            follower=request.user, followed=user_obj,
        ).exists()

        following_users = []
        follower_users = []
        if is_own:
            following_users = User.objects.filter(
                follower_relations__follower=user_obj,
            ).only('id', 'username', 'avatar')[:10]
            follower_users = User.objects.filter(
                following_relations__followed=user_obj,
            ).only('id', 'username', 'avatar')[:10]

        return render(request, 'site.html', locals())


@method_decorator(cache_page_for_anonymous(60 * 2, key_prefix='article'), name='get')
class ArticleDetail(View):
    def get(self, request, username, article_id):
        user_obj = User.objects.filter(username=username).first()
        if not user_obj:
            return render(request, 'error.html', status=404)
        blog = user_obj.blog
        is_own = request.user.is_authenticated and request.user.pk == user_obj.pk
        article_obj = Article.objects.filter(blog=blog, pk=article_id).first()
        if not article_obj:
            return render(request, 'error.html', status=404)
        if article_obj.status == 'draft' and not is_own:
            return render(request, 'error.html', status=404)

        # 浏览量 +1 (原子更新,避免竞态)
        Article.objects.filter(pk=article_obj.pk).update(view_count=F('view_count') + 1)
        article_obj.view_count += 1  # 内存中的对象也同步

        author_follower_count = Follow.objects.filter(followed=user_obj).count()
        author_following_count = Follow.objects.filter(follower=user_obj).count()
        author_article_count = Article.objects.filter(blog=blog, is_delete=False, status='published').count()
        is_following_author = request.user.is_authenticated and Follow.objects.filter(
            follower=request.user, followed=user_obj,
        ).exists()

        comment_queryset = Comment.objects.filter(article=article_obj).select_related('user')
        comment_map = {c.pk: c for c in comment_queryset}

        def get_root_id(c):
            while c.parent_id and c.parent_id in comment_map:
                c = comment_map[c.parent_id]
            return c.pk

        reply_map = {}
        root_comments = []
        for c in comment_queryset:
            if c.parent_id:
                root_id = get_root_id(c)
                reply_map.setdefault(root_id, []).append(c)
            else:
                root_comments.append(c)
        root_comments.sort(key=lambda x: x.up_num, reverse=True)
        comments_with_replies = [(c, reply_map.get(c.pk, [])) for c in root_comments]
        return render(request, 'article_detail.html', locals())


class UpDown(View):
    @is_login_method
    def post(self, request):
        backend = {
            'code': 400,
            'msg': '',
        }
        user_obj = request.user
        blog_obj = user_obj.blog
        article_id = request.POST.get('article_id')
        is_up = request.POST.get('is_up')
        is_up = True if is_up == 'true' else False

        article_obj = Article.objects.filter(pk=article_id).first()
        if article_obj.blog == blog_obj:
            backend['msg'] = '您不能操作自己的文章'
            return JsonResponse(backend)

        res_is_up = UpAndDown.objects.filter(user=user_obj, article=article_obj).first()
        if res_is_up:
            flag = res_is_up.is_up
            if flag == is_up:
                res_is_up.delete()
                if flag:
                    article_obj.up_num -= 1
                    backend['msg'] = '取消点赞成功'
                else:
                    article_obj.down_num -= 1
                    backend['msg'] = '取消点踩成功'
                article_obj.save()
            else:
                res_is_up.delete()
                if flag:
                    article_obj.up_num -= 1
                    article_obj.down_num += 1
                else:
                    article_obj.down_num -= 1
                    article_obj.up_num += 1
                article_obj.save()
                backend['msg'] = '切换操作成功'

                UpAndDown.objects.create(
                    user=user_obj,
                    article=article_obj,
                    is_up=is_up,
                )
        else:
            UpAndDown.objects.create(
                user=user_obj,
                article=article_obj,
                is_up=is_up,
            )
            if is_up:
                article_obj.up_num += 1
                backend['msg'] = '点赞成功'
            else:
                article_obj.down_num += 1
                backend['msg'] = '点踩成功'

            article_obj.save()

        backend['code'] = 200
        backend['up_num'] = article_obj.up_num
        backend['down_num'] = article_obj.down_num
        clear_cache_patterns('article')
        return JsonResponse(backend)
