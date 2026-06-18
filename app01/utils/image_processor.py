import base64
import os
import re
import uuid
from datetime import datetime
from django.conf import settings

_BASE64_RE = re.compile(
    r'<img[^>]+src=[\'"](data:image/([^;]+);base64,([^\'">\s]+))[\'"]',
    re.IGNORECASE,
)


def convert_base64_images(html):
    """将 HTML 中的 base64 图片替换为上传后的文件 URL。"""
    if not html:
        return html

    def replace_match(match):
        full_data_url = match.group(1)
        ext = match.group(2).lower()
        data = match.group(3)

        if ext == 'jpeg':
            ext = 'jpg'
        if ext not in ('jpg', 'png', 'gif', 'webp'):
            ext = 'jpg'

        try:
            raw = base64.b64decode(data)
        except Exception as e:
            print(f'[convert_base64_images] base64 decode failed: {e}')
            return match.group(0)

        now = datetime.now()
        filename = f"{uuid.uuid4().hex}.{ext}"
        rel_dir = f"article_images/{now.year}/{now.month:02d}"
        save_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)

        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            print(f'[convert_base64_images] mkdir failed: {save_dir}, {e}')
            return match.group(0)

        filepath = os.path.join(save_dir, filename)
        try:
            with open(filepath, 'wb') as f:
                f.write(raw)
        except OSError as e:
            print(f'[convert_base64_images] write failed: {filepath}, {e}')
            return match.group(0)

        url = '/' + '/'.join(
            [settings.MEDIA_URL.strip('/'), rel_dir, filename]
        )
        print(f'[convert_base64_images] converted: {len(raw)} bytes -> {url}')
        return match.group(0).replace(full_data_url, url)

    return _BASE64_RE.sub(replace_match, html)
