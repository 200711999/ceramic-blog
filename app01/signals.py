from django.db.models.signals import post_save
from django.dispatch import receiver

from app01.models import User, Blog


@receiver(post_save, sender=User)
def ensure_user_has_blog(sender, instance, created, **kwargs):
    if created and instance.blog is None:
        Blog.objects.create(
            site_name=instance.username,
            site_title=f'{instance.username}的个人站点',
        )
