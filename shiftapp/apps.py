from django.apps import AppConfig



class ShiftappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shiftapp'


class MembersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shiftapp'

    def ready(self):
        import shiftapp.signals