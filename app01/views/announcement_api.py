from django.http import JsonResponse
from django.views import View

from app01.models import Announcement, AnnouncementDismissal
from app01.utils.dors import is_login_method


class AnnouncementAPI(View):
    def get(self, request):
        ann = Announcement.objects.filter(is_active=True).first()
        if not ann:
            return JsonResponse({'code': 200, 'announcement': None})

        dismissed = False
        if request.user.is_authenticated:
            dismissed = AnnouncementDismissal.objects.filter(
                user=request.user, announcement=ann,
            ).exists()

        return JsonResponse({
            'code': 200,
            'announcement': {
                'id': ann.pk,
                'title': ann.title,
                'content': ann.content,
                'image': str(ann.image) if ann.image else None,
            },
            'dismissed': dismissed,
        })


class AnnouncementListAPI(View):
    def get(self, request):
        announcements = Announcement.objects.filter(is_active=True).order_by('-priority', '-create_time')
        data = [{
            'id': a.pk,
            'title': a.title,
            'content': a.content,
            'create_time': a.create_time.strftime('%Y-%m-%d'),
        } for a in announcements]
        return JsonResponse({'code': 200, 'announcements': data})


class AnnouncementDismissAPI(View):
    @is_login_method
    def post(self, request):
        announcement_id = request.POST.get('announcement_id')
        ann = Announcement.objects.filter(pk=announcement_id, is_active=True).first()
        if not ann:
            return JsonResponse({'code': 400, 'msg': '公告不存在'})
        AnnouncementDismissal.objects.get_or_create(
            user=request.user, announcement=ann,
        )
        return JsonResponse({'code': 200})
