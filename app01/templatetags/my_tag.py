import re

from django import template
from django.utils.safestring import mark_safe
from datetime import datetime, timedelta

from django.db.models import Count
from django.utils.timezone import is_naive, make_naive, now as django_now
from app01.models import User

import bleach
import warnings
warnings.filterwarnings('ignore', category=bleach.sanitizer.NoCssSanitizerWarning)

# 注册模版标签
register = template.Library()

# rich_content 允许的 HTML 标签和属性
ALLOWED_TAGS = [
    'p', 'div', 'span', 'br', 'hr',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'strong', 'em', 'u', 's', 'b', 'i', 'del',
    'blockquote', 'pre', 'code',
    'ul', 'ol', 'li',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'sub', 'sup',
]
ALLOWED_ATTRS = {
    '*': ['class', 'style'],
    'a': ['href', 'title', 'target'],
    'img': ['src', 'alt', 'width', 'height'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


@register.filter
def get_desc(content):
    return content[:50] + "······"


# 匹配 <img src="data:image/..."> — 在 bleach 处理前保护 base64 图片
_DATA_IMG_RE = re.compile(
    r'(<img[^>]*\s)src=([\'"])(data:image/[^\'"]+)\2',
    re.IGNORECASE,
)

# 匹配 <img style="...">，把 style 里的 width/height 提前转成属性
# bleach 没有 css_sanitizer 时会清空 style 属性，导致编辑器里设置的图片尺寸丢失
_IMG_STYLE_RE = re.compile(
    r'<img\b([^>]*?)\s*style\s*=\s*([\'"])(.*?)\2([^>]*)>',
    re.IGNORECASE | re.DOTALL,
)
_IMG_STYLE_WIDTH_RE = re.compile(r'width\s*:\s*([^;]+)', re.IGNORECASE)
_IMG_STYLE_HEIGHT_RE = re.compile(r'height\s*:\s*([^;]+)', re.IGNORECASE)


def _migrate_img_style_dimensions(value):
    """把 img style 里的 width/height 提取为 width/height 属性，避免被 bleach 清空。"""
    def _replace(m):
        prefix = m.group(1)
        style = m.group(3)
        suffix = m.group(4)

        width = _IMG_STYLE_WIDTH_RE.search(style)
        height = _IMG_STYLE_HEIGHT_RE.search(style)

        # 只处理 px 单位的值，HTML width/height 属性只接受整数
        def _px_value(v):
            v = v.strip()
            if v.endswith('px'):
                return v[:-2].strip()
            # 纯数字也当成 px
            if v.replace('.', '', 1).isdigit():
                return v
            return None

        attrs = ''
        if width:
            w = _px_value(width.group(1))
            if w and 'width=' not in prefix.lower() and 'width=' not in suffix.lower():
                attrs += ' width="{}"'.format(w)
        if height:
            h = _px_value(height.group(1))
            if h and 'height=' not in prefix.lower() and 'height=' not in suffix.lower():
                attrs += ' height="{}"'.format(h)

        return '<img{}{}{}>'.format(prefix, attrs, suffix)

    return _IMG_STYLE_RE.sub(_replace, value)


@register.filter
def rich_content(value):
    if not value:
        return ''

    # 把 base64 图片 src 替换为临时 token，避免 bleach 因 data: 协议而删掉 src
    saved = {}
    def _protect_base64(m):
        token = '__IMG_B64_{}__'.format(len(saved))
        saved[token] = m.group(3)
        return '{}src={}{}{}'.format(m.group(1), m.group(2), token, m.group(2))
    value = _DATA_IMG_RE.sub(_protect_base64, value)

    # 把 style 里的 width/height 提前转成属性，否则 bleach 会清空 style
    value = _migrate_img_style_dimensions(value)

    has_tags = re.search(r'<[^>]+>', value)
    if has_tags:
        value = bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=ALLOWED_PROTOCOLS)
    else:
        value = bleach.linkify(bleach.clean(
            value.replace('\n', '<br>'), tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS, protocols=ALLOWED_PROTOCOLS,
        ))

    # 恢复 base64 图片
    for token, data_uri in saved.items():
        value = value.replace(token, data_uri)

    # 修复因 MEDIA_URL 配置不当产生的协议相对 URL (//media/...)
    value = value.replace('src="//media/', 'src="/media/')
    value = value.replace("src='//media/", "src='/media/")

    return mark_safe(value)


@register.filter
def blog_age(create_time):
    time_item = datetime.now() - create_time
    return time_item.days


@register.filter
def friendly_time(value):
    """
    将 datetime 格式化为友好时间：
    今天 14:24 / 昨天 14:24 / 3天前 / 5月5日 / 2025年5月5日
    """
    if not value:
        return ''
    # 统一转为本地 naive datetime
    if hasattr(value, 'astimezone'):
        dt = make_naive(value) if not is_naive(value) else value
    else:
        dt = value
    n = datetime.now()
    delta = n - dt
    today = n.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    if dt >= today:
        return '今天 {:02d}:{:02d}'.format(dt.hour, dt.minute)
    elif dt >= yesterday:
        return '昨天 {:02d}:{:02d}'.format(dt.hour, dt.minute)
    elif delta.days < 7:
        return '{}天前'.format(delta.days)
    elif dt.year == n.year:
        return '{}月{}日'.format(dt.month, dt.day)
    else:
        return '{}年{}月{}日'.format(dt.year, dt.month, dt.day)


# 模版中可以通过
# {% sidebar %} 直接渲染成 sidebar.html 中内容
# 存储：侧边栏，导航条，底部。。。局部组件的内容
@register.inclusion_tag('sidebar.html')
def sidebar(username):
    user_obj = User.objects.filter(username=username).first()
    blog = user_obj.blog
    article_queryset = blog.articles.all()

    # 基于该站点的所有文章，和该站点的所有分类，统计每个分类的文章数量

    # category_info 内部数据格式
    # [(1,'后端',2) , (2,'前端',1) , (3,'杂事',0)]
    category_queryset = blog.categorys.all()
    category_info = []
    for category in category_queryset:
        category_id = category.pk
        category_name = category.name
        category_count = article_queryset.filter(category=category).count()
        category_info.append((category_id, category_name, category_count))

    # 查询出该站点的所有标签
    tag_queryset = blog.tags.all()
    tag_info = []
    for tag in tag_queryset:
        tag_id = tag.pk
        tag_name = tag.name
        tag_count = article_queryset.filter(tags=tag).count()
        tag_info.append((tag_id, tag_name, tag_count))

    group_info = article_queryset.values("create_time__year", "create_time__month").annotate(
        count=Count("create_time"))
    date_info = []
    # [("2026","01",2),("2026","12",1),...]  (year,month,count)
    for group in group_info:
        year = group.get('create_time__year')
        month = group.get('create_time__month')
        count = group.get('count')
        date_info.append((year, month, count))

    return locals()