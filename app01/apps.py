from django.apps import AppConfig


class App01Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app01'
    verbose_name = '博客管理'

    def ready(self):
        import app01.signals
