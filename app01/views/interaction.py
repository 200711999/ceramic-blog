from django.http import JsonResponse
from django.views import View

from app01.models import User, Article, Comment, CommentLike, Notification, Follow, Report
from app01.utils.dors import is_login_method


class CommentView(View):
    @is_login_method
    def post(self, request):
        backend = {
            'code': 400,
            'msg': '',
        }
        user_obj = request.user
        comment = request.POST.get('comment')
        article_id = request.POST.get('article_id')
        parent_id = request.POST.get('parent_id')

        article_obj = Article.objects.filter(pk=article_id).first()
        if not comment:
            backend['msg'] = '请输入评论内容'
            return JsonResponse(backend)

        new_comment = Comment.objects.create(
            user=user_obj,
            article=article_obj,
            content=comment,
            parent_id=parent_id,
        )
        article_obj.comment_num += 1
        article_obj.save()

        # 通知
        if parent_id:
            parent_comment = Comment.objects.filter(pk=parent_id).first()
            if parent_comment and parent_comment.user != user_obj:
                Notification.objects.create(
                    recipient=parent_comment.user, actor=user_obj,
                    verb='replied', article=article_obj, comment=new_comment,
                )
        else:
            if article_obj.blog.user != user_obj:
                Notification.objects.create(
                    recipient=article_obj.blog.user, actor=user_obj,
                    verb='commented', article=article_obj, comment=new_comment,
                )

        backend['code'] = 200
        backend['msg'] = '评论成功'
        backend['comment_num'] = article_obj.comment_num
        return JsonResponse(backend)


class CommentLikeView(View):
    @is_login_method
    def post(self, request):
        comment_id = request.POST.get('comment_id')
        comment = Comment.objects.filter(pk=comment_id).first()
        if not comment:
            return JsonResponse({'code': 400, 'msg': '评论不存在'})
        like_obj = CommentLike.objects.filter(user=request.user, comment=comment).first()
        if like_obj:
            like_obj.delete()
            comment.up_num -= 1
            comment.save()
            return JsonResponse({'code': 200, 'msg': '取消点赞', 'up_num': comment.up_num, 'liked': False})
        else:
            CommentLike.objects.create(user=request.user, comment=comment)
            comment.up_num += 1
            comment.save()
            if comment.user != request.user:
                Notification.objects.create(
                    recipient=comment.user, actor=request.user,
                    verb='liked', article=comment.article, comment=comment,
                )
            return JsonResponse({'code': 200, 'msg': '点赞成功', 'up_num': comment.up_num, 'liked': True})


class CommentDeleteView(View):
    @is_login_method
    def post(self, request):
        comment_id = request.POST.get('comment_id')
        comment = Comment.objects.filter(pk=comment_id).first()
        if not comment:
            return JsonResponse({'code': 400, 'msg': '评论不存在'})
        if comment.user != request.user:
            return JsonResponse({'code': 403, 'msg': '只能删除自己的评论'})
        article = comment.article
        comment.delete()
        article.comment_num = Comment.objects.filter(article=article).count()
        article.save()
        return JsonResponse({'code': 200, 'msg': '删除成功', 'comment_num': article.comment_num})


class NotificationView(View):
    @is_login_method
    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user).select_related('actor', 'article__blog__user')[:20]
        data = [{
            'id': n.pk,
            'actor_name': n.actor.username,
            'actor_avatar': str(n.actor.avatar),
            'verb': n.verb,
            'verb_display': n.get_verb_display(),
            'article_id': n.article_id,
            'article_title': n.article.title if n.article else None,
            'article_author': n.article.blog.user.username if n.article else None,
            'comment_id': n.comment_id,
            'is_read': n.is_read,
            'time': n.create_time.strftime('%m-%d %H:%M'),
        } for n in notifications]
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'code': 200, 'notifications': data, 'unread_count': unread_count})

    @is_login_method
    def post(self, request):
        nid = request.POST.get('id')
        if nid == 'all':
            Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        elif nid:
            Notification.objects.filter(pk=nid, recipient=request.user).update(is_read=True)
        return JsonResponse({'code': 200})


class UserSearchView(View):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q or len(q) > 20:
            return JsonResponse({'code': 400, 'users': []})
        users = User.objects.filter(username__icontains=q)[:8]
        return JsonResponse({'code': 200, 'users': [{'id': u.pk, 'username': u.username, 'avatar': str(u.avatar)} for u in users]})


class FollowToggleView(View):
    @is_login_method
    def post(self, request):
        target_id = request.POST.get('user_id')
        target = User.objects.filter(pk=target_id).first()
        if not target or target == request.user:
            return JsonResponse({'code': 400, 'msg': '操作无效'})

        follow_obj = Follow.objects.filter(follower=request.user, followed=target).first()
        if follow_obj:
            follow_obj.delete()
            following = False
        else:
            Follow.objects.create(follower=request.user, followed=target)
            following = True
            Notification.objects.create(
                recipient=target, actor=request.user,
                verb='followed', article=None,
            )

        follower_count = Follow.objects.filter(followed=target).count()
        return JsonResponse({
            'code': 200,
            'following': following,
            'follower_count': follower_count,
        })


class ReportArticleView(View):
    @is_login_method
    def post(self, request):
        article_id = request.POST.get('article_id')
        reason = (request.POST.get('reason') or '').strip()

        if not reason:
            return JsonResponse({'code': 400, 'msg': '请填写举报原因'})
        if len(reason) > 256:
            return JsonResponse({'code': 400, 'msg': '举报原因不能超过256个字符'})

        article_obj = Article.objects.filter(pk=article_id, is_delete=False).first()
        if not article_obj:
            return JsonResponse({'code': 400, 'msg': '文章不存在'})
        if article_obj.blog.user == request.user:
            return JsonResponse({'code': 400, 'msg': '不能举报自己的文章'})

        if Report.objects.filter(reporter=request.user, article=article_obj).exists():
            return JsonResponse({'code': 400, 'msg': '您已举报过该文章，请等待处理'})

        Report.objects.create(
            reporter=request.user,
            article=article_obj,
            reason=reason,
        )
        return JsonResponse({'code': 200, 'msg': '举报提交成功，管理员将尽快处理'})
