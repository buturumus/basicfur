from django.db import models
from django.contrib.auth.models import AbstractUser
import logging

# Create your models here.
DFLT_NO_NANE='nobody'
DFLT_ADM_NAME='b3admin'
DFLT_ADM_PW='b3adminb3admin'
DFLT_NORM_NAME='test'
DFLT_NORM_PW='test'

class CustomUser(AbstractUser):

    @staticmethod
    def get_default_set():
        return (
            DFLT_NO_NANE, DFLT_ADM_NAME,
        )

    @classmethod
    def default_init(cls):
        # ignore in in pre-migration state
        try:
            # nobody
            nobody_user = CustomUser()
            nobody_user.username = DFLT_NO_NANE
            nobody_user.save()
            # admin
            admin_user = CustomUser()
            admin_user.username = DFLT_ADM_NAME
            admin_user.set_password(DFLT_ADM_PW)
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            # normal
            admin_user = CustomUser()
            admin_user.username = DFLT_NORM_NAME
            admin_user.set_password(DFLT_NORM_PW)
            admin_user.is_staff = True
            admin_user.is_superuser = False
            admin_user.save()
        except:
            return

    @classmethod
    def check_defaults(cls):
        try:
            for name in cls.get_default_set():
                obj = cls.objects.get(username=name)
        except:
            cls.objects.all().delete()
            cls.default_init()

