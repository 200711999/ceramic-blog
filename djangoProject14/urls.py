from django.contrib import admin
from django.urls import path, re_path

from app01 import views
from app01.utils import code
from django.conf.urls.static import static, settings

# 修改后台标题和页眉
admin.site.site_header = "我的后台管理"
admin.site.site_title = "我的后台"
admin.site.index_title = "欢迎来到我的后台"

urlpatterns = [
    # 超级管理员后台
    path('admin/', admin.site.urls),

    # 用户注册
    path('register/', views.Register.as_view(), name='register'),
    # 用户登录
    path('login/', views.Login.as_view(), name='login'),
    # 登录验证码
    path('get_code/', code.get_code),
    # 退出登录
    path('logout/', views.Logout.as_view(), name='logout'),
    # 修改密码
    path('set_password/', views.SetPassword.as_view(), name='set_password'),

    # 修改个人信息(AJAX 弹窗)
    path('edit_profile/', views.EditProfile.as_view(), name='edit_profile'),

    # 主页
    path('index/', views.Index.as_view(), name='index'),

    # 个人站点
    path('index/<str:username>/', views.Site.as_view(), name='site'),

    # 侧边栏路由：分类、标签、日期
    re_path('^index/(?P<username>\w+)/(?P<condition>category|tag|date)/(?P<value>[\d-]+)/$', views.Site.as_view()),

    # 文章详情页
    re_path(r"^index/(?P<username>\w+)/p/(?P<article_id>\d+)/$", views.ArticleDetail.as_view()),

    # 点赞点踩
    path('updown/', views.UpDown.as_view(), name='updown'),

    # 修改头像
    path('set_avatar/', views.SetAvatar.as_view()),

    # 发布评论
    path('comment/', views.CommentView.as_view()),
    path('comment/like/', views.CommentLikeView.as_view(), name='comment_like'),
    path('comment/delete/', views.CommentDeleteView.as_view(), name='comment_delete'),

    # 用户搜索（@补全）
    path('search_users/', views.UserSearchView.as_view(), name='search_users'),

    # 通知
    path('notifications/', views.NotificationView.as_view(), name='notifications'),

    # 后台管理
    path('backend/', views.Backend.as_view()),

    # 文章管理
    path('article/add/', views.AddArticle.as_view(), name='add_article'),
    path('article/edit/<int:article_id>/', views.EditArticle.as_view(), name='edit_article'),
    path('article/delete/', views.DeleteArticle.as_view(), name='delete_article'),

    # 分类管理
    path('category/add/', views.AddCategory.as_view(), name='add_category'),
    path('category/edit/', views.EditCategory.as_view(), name='edit_category'),
    path('category/delete/', views.DeleteCategory.as_view(), name='delete_category'),
    # 标签管理
    path('tag/add/', views.AddTag.as_view(), name='add_tag'),
    path('tag/edit/', views.EditTag.as_view(), name='edit_tag'),
    path('tag/delete/', views.DeleteTag.as_view(), name='delete_tag'),
    # 评论管理
    path('comment/manage/delete/', views.ManageCommentDelete.as_view(), name='manage_comment_delete'),

    # 用户信息完善
    path('edit/user/', views.EditUser.as_view(), name='edit_user'),

    # AI 问答助手
    path('ai_chat/', views.AIChat.as_view(), name='ai_chat'),

    # AI 写作辅助
    path('ai/generate/', views.AIGenerate.as_view(), name='ai_generate'),
    path('ai/summarize/', views.AISummarize.as_view(), name='ai_summarize'),
    path('ai/continue/', views.AIContinue.as_view(), name='ai_continue'),

    # AI 自动分类/打标签
    path('ai/auto_tag/', views.AIAutoTag.as_view(), name='ai_auto_tag'),

    # 编辑器图片上传
    path('upload_image/', views.ImageUpload.as_view(), name='upload_image'),

    # 关注 / 取关
    path('follow/', views.FollowToggleView.as_view(), name='follow_toggle'),

    # 举报文章
    path('report/', views.ReportArticleView.as_view(), name='report_article'),

    # 物品展览
    path('exhibition/', views.Exhibition.as_view(), name='exhibition'),

    # 公告 API
    path('announcement/latest/', views.AnnouncementAPI.as_view(), name='announcement_latest'),
    path('announcement/list/', views.AnnouncementListAPI.as_view(), name='announcement_list'),
    path('announcement/dismiss/', views.AnnouncementDismissAPI.as_view(), name='announcement_dismiss'),
]
# media文件访问路由
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
