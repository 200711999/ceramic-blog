from django.db import models
from django.contrib.auth.models import AbstractUser


# 抽象模型类
# 抽象类不会被迁移生成表的，唯一的作用是被继承，可以让其他模型表直接拿到字段
class BaseModel(models.Model):
    class Meta:
        abstract = True  # 设置为抽象类

    # auto_now_add 创建模型对象的时候，会自动记录创建时间，类型是DateTimeField
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    # 更新时间
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    # 逻辑删除
    is_delete = models.BooleanField(default=False, verbose_name='逻辑删除')


# 用户表（需要用到auth相关功能，需要继承AbstractUser）
class User(AbstractUser, BaseModel):
    # 年龄
    age = models.IntegerField(null=True, blank=True, verbose_name='年龄')
    # 性别
    gender = models.CharField(max_length=10, null=True, blank=True, verbose_name='性别')
    # 手机号码
    phone = models.CharField(max_length=11, null=True, blank=True, verbose_name='手机号码')
    # 头像 FileField()文件字段，  数据中本质也是varchar
    avatar = models.FileField(  # upload_to 指向服务端文件夹，保存模型对象的时候，会自动将文件保存到下面
        upload_to='avatar/',
        null=True, blank=True, verbose_name='头像'
    )

    # 外键： 用户和个人站点 一对一关系
    blog = models.OneToOneField(related_name='user',to='Blog', on_delete=models.CASCADE, verbose_name='个人站点', null=True, blank=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'

# 个人站点表
class Blog(BaseModel):
    # 站点名称
    site_name = models.CharField(max_length=32, verbose_name='站点名称')
    # 站点标题
    site_title = models.CharField(max_length=32, verbose_name='站点标题')
    # 站点样式
    site_theme = models.FileField(upload_to='css/', verbose_name='站点样式',null=True, blank=True)

    def __str__(self):
        return self.site_title

    class Meta:
        verbose_name = '个人站点'
        verbose_name_plural = '个人站点'

# 标签表
class Tag(models.Model):
    # 标签名称
    name = models.CharField(max_length=10, verbose_name='标签名称')

    # 外键字段 一对多 个人站点
    blog = models.ForeignKey(related_name='tags',to="Blog", on_delete=models.CASCADE, verbose_name="个人站点")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = '标签'

# 分类表
class Category(models.Model):
    # 分类名称
    name = models.CharField(max_length=10, verbose_name='分类名称')

    # 外键字段 一对多个人站点
    blog = models.ForeignKey(related_name='categorys',to="Blog", on_delete=models.CASCADE, verbose_name="个人站点")
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'

# 文章表
class Article(BaseModel):
    # 文章标题
    title = models.CharField(max_length=128, verbose_name='文章标题')
    # 文章内容
    content = models.TextField(verbose_name='文章内容')
    # desc 从content中截取
    # 点赞点踩评论数
    # 点赞数
    up_num = models.IntegerField(default=0, verbose_name='点赞数')
    # 点踩数
    down_num = models.IntegerField(default=0, verbose_name='点踩数')
    # 评论数
    comment_num = models.IntegerField(default=0, verbose_name='评论数')
    # 浏览量
    view_count = models.IntegerField(default=0, verbose_name='浏览量')
    # 发布状态
    STATUS_CHOICES = (('draft', '草稿'), ('published', '已发布'))
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='published', verbose_name='发布状态')

    # 外键字段
    blog = models.ForeignKey(related_name='articles',to='Blog', on_delete=models.CASCADE, verbose_name='个人站点')
    # 分类
    category = models.ForeignKey(to='Category', on_delete=models.CASCADE, verbose_name='文章分类')
    # 标签 (生成关系表）（多对多不需要on_delete) (虚拟字段，不生成表中)
    tags = models.ManyToManyField(to='Tag', verbose_name='文章标签')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'

# 点赞点踩
class UpAndDown(models.Model):
    # 用户
    user = models.ForeignKey(to='User', on_delete=models.CASCADE, verbose_name='用户')
    # 文章
    article = models.ForeignKey(to='Article', on_delete=models.CASCADE, verbose_name='文章')
    # 是什么操作 1点赞 0点踩
    is_up = models.BooleanField(verbose_name='点赞点踩状态')  # 1 点赞 0 点踩

    class Meta:
        verbose_name = '点赞点踩'
        verbose_name_plural = '点赞点踩'
        unique_together = ('user', 'article')


# 评论表
class Comment(models.Model):
    # 用户
    user = models.ForeignKey(to='User', on_delete=models.CASCADE, verbose_name='用户')
    # 文章
    article = models.ForeignKey(related_name='comments',to='Article', on_delete=models.CASCADE, verbose_name='文章')

    # 评论内容
    content = models.TextField(verbose_name='评论内容')
    # 评论时间
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='评论时间')

    # 回复评论id
    parent = models.ForeignKey(to='self', on_delete=models.CASCADE, verbose_name='回复评论', null=True, blank=True)
    # 点赞数
    up_num = models.IntegerField(default=0, verbose_name='点赞数')

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'


# 评论点赞
class CommentLike(models.Model):
    user = models.ForeignKey(to='User', on_delete=models.CASCADE, verbose_name='用户')
    comment = models.ForeignKey(to='Comment', on_delete=models.CASCADE, verbose_name='评论')

    class Meta:
        verbose_name = '评论点赞'
        verbose_name_plural = '评论点赞'
        unique_together = ('user', 'comment')


# 通知
class Notification(models.Model):
    VERB_CHOICES = (
        ('commented', '评论了'),
        ('replied', '回复了'),
        ('liked', '赞了'),
        ('followed', '关注了你'),
        ('published', '发布了新文章'),
        ('report_resolved', '举报已处理'),
        ('report_dismissed', '举报已驳回'),
    )
    recipient = models.ForeignKey(to='User', on_delete=models.CASCADE, related_name='notifications', verbose_name='接收者')
    actor = models.ForeignKey(to='User', on_delete=models.CASCADE, related_name='sent_notifications', verbose_name='触发者')
    verb = models.CharField(max_length=16, choices=VERB_CHOICES, verbose_name='动作')
    article = models.ForeignKey(to='Article', on_delete=models.CASCADE, verbose_name='相关文章', null=True, blank=True)
    comment = models.ForeignKey(to='Comment', on_delete=models.CASCADE, null=True, blank=True, verbose_name='相关评论')
    is_read = models.BooleanField(default=False, verbose_name='已读')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='时间')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-create_time']


# 公告
class Announcement(models.Model):
    title = models.CharField(max_length=64, verbose_name='标题')
    content = models.TextField(verbose_name='正文')
    image = models.FileField(upload_to='announcement/', null=True, blank=True, verbose_name='配图')
    is_active = models.BooleanField(default=True, verbose_name='启用')
    priority = models.IntegerField(default=0, verbose_name='优先级')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '公告'
        verbose_name_plural = '公告'
        ordering = ['-priority', '-create_time']


# 公告关闭记录
class AnnouncementDismissal(models.Model):
    user = models.ForeignKey(to='User', on_delete=models.CASCADE, verbose_name='用户')
    announcement = models.ForeignKey(to='Announcement', on_delete=models.CASCADE, verbose_name='公告')
    dismissed_at = models.DateTimeField(auto_now_add=True, verbose_name='关闭时间')

    class Meta:
        verbose_name = '公告关闭记录'
        verbose_name_plural = '公告关闭记录'
        unique_together = ('user', 'announcement')


# 举报
class Report(models.Model):
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('resolved', '已处理'),
        ('dismissed', '已驳回'),
    )
    reporter = models.ForeignKey(to='User', on_delete=models.CASCADE, related_name='reports', verbose_name='举报者')
    article = models.ForeignKey(to='Article', on_delete=models.CASCADE, related_name='reports', verbose_name='被举报文章')
    reason = models.CharField(max_length=256, verbose_name='举报原因')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    resolved_by = models.ForeignKey(to='User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_reports', verbose_name='处理人')
    resolved_time = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    admin_note = models.TextField(null=True, blank=True, verbose_name='处理备注')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='举报时间')

    class Meta:
        verbose_name = '举报'
        verbose_name_plural = '举报'
        unique_together = ('reporter', 'article')
        ordering = ['-create_time']


# 关注
class Follow(models.Model):
    follower = models.ForeignKey(to='User', on_delete=models.CASCADE, related_name='following_relations', verbose_name='关注者')
    followed = models.ForeignKey(to='User', on_delete=models.CASCADE, related_name='follower_relations', verbose_name='被关注者')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='关注时间')

    class Meta:
        verbose_name = '关注'
        verbose_name_plural = '关注'
        unique_together = ('follower', 'followed')
        ordering = ['-create_time']
