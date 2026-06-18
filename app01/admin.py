from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from app01.models import User, Blog, Tag, Category, UpAndDown, Article, Announcement, AnnouncementDismissal, Report


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('id', 'avatar_thumb', 'username', 'email', 'phone', 'gender', 'age', 'blog', 'is_staff', 'is_active')
    list_display_links = ('id', 'username')
    list_filter = ('is_staff', 'is_active', 'gender')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-id',)
    list_per_page = 20
    fieldsets = UserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('age', 'gender', 'phone', 'avatar', 'blog')}),
    )

    @admin.display(description='头像')
    def avatar_thumb(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="/media/{}" style="width:32px;height:32px;border-radius:50%;object-fit:cover">',
                obj.avatar
            )
        return '—'


@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('id', 'site_name', 'site_title', 'site_theme', 'create_time')
    list_display_links = ('id', 'site_name')
    search_fields = ('site_name', 'site_title')
    ordering = ('-id',)
    list_per_page = 20


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'blog', 'category', 'up_num', 'down_num', 'comment_num', 'create_time', 'is_delete')
    list_display_links = ('id', 'title')
    list_filter = ('category', 'is_delete', 'create_time')
    search_fields = ('title', 'content', 'blog__site_name')
    filter_horizontal = ('tags',)
    ordering = ('-create_time',)
    date_hierarchy = 'create_time'
    list_per_page = 20
    list_editable = ('is_delete',)
    autocomplete_fields = ('blog', 'category')
    readonly_fields = ('up_num', 'down_num', 'comment_num', 'create_time', 'update_time')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'blog', 'article_count')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'blog__site_name')
    list_filter = ('blog',)
    ordering = ('id',)
    list_per_page = 30

    @admin.display(description='文章数')
    def article_count(self, obj):
        return obj.article_set.count()


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'blog', 'article_count')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'blog__site_name')
    list_filter = ('blog',)
    ordering = ('id',)
    list_per_page = 30

    @admin.display(description='文章数')
    def article_count(self, obj):
        return obj.article_set.count()


@admin.register(UpAndDown)
class UpAndDownAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'article', 'action_label')
    list_display_links = ('id',)
    list_filter = ('is_up',)
    search_fields = ('user__username', 'article__title')
    ordering = ('-id',)
    list_per_page = 30
    autocomplete_fields = ('user', 'article')

    @admin.display(description='操作', boolean=False)
    def action_label(self, obj):
        return '点赞' if obj.is_up else '点踩'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'image_thumb', 'is_active', 'priority', 'create_time')
    list_display_links = ('id', 'title')
    list_editable = ('is_active', 'priority')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')
    ordering = ('-priority', '-create_time')
    list_per_page = 20

    @admin.display(description='配图')
    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="/media/{}" style="max-height:40px;border-radius:4px">',
                obj.image
            )
        return '—'


@admin.register(AnnouncementDismissal)
class AnnouncementDismissalAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'announcement', 'dismissed_at')
    list_filter = ('announcement',)
    search_fields = ('user__username',)
    ordering = ('-dismissed_at',)
    list_per_page = 30


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'article_title', 'article_link', 'reason_preview', 'status', 'status_badge', 'create_time')
    list_display_links = ('id', 'reporter')
    list_filter = ('status', 'create_time')
    search_fields = ('reporter__username', 'article__title', 'reason')
    ordering = ('status', '-create_time')
    list_per_page = 20
    list_editable = ('status',)
    autocomplete_fields = ('reporter', 'article', 'resolved_by')
    readonly_fields = ('create_time',)

    @admin.display(description='文章')
    def article_title(self, obj):
        return obj.article.title

    @admin.display(description='阅读')
    def article_link(self, obj):
        url = f"/index/{obj.article.blog.user.username}/p/{obj.article.pk}/"
        return format_html('<a href="{}" target="_blank">阅读文章</a>', url)

    @admin.display(description='举报原因')
    def reason_preview(self, obj):
        if len(obj.reason) > 40:
            return obj.reason[:40] + '…'
        return obj.reason

    @admin.display(description='状态')
    def status_badge(self, obj):
        status_color = {'pending': 'orange', 'resolved': 'green', 'dismissed': 'gray'}
        color = status_color.get(obj.status, 'gray')
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            color, obj.get_status_display()
        )

    def save_model(self, request, obj, form, change):
        if change:
            old_status = Report.objects.get(pk=obj.pk).status
            if old_status == 'pending' and obj.status != 'pending':
                from django.utils import timezone
                from app01.models import Notification
                obj.resolved_by = request.user
                obj.resolved_time = timezone.now()
                verb = 'report_resolved' if obj.status == 'resolved' else 'report_dismissed'
                Notification.objects.create(
                    recipient=obj.reporter,
                    actor=request.user,
                    verb=verb,
                    article=obj.article,
                )
        super().save_model(request, obj, form, change)
