from django.db import models
from django.contrib.auth.hashers import make_password
class Register(models.Model):
    fullname = models.CharField(max_length=50, blank=False, null=False)
    email = models.EmailField(max_length=100, blank=False, null=False, unique=True)
    password = models.CharField(max_length=128, blank=False, null=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def __str__(self):
        return self.fullname


class Login(models.Model):
    username = models.CharField(max_length=50, blank=False , null=False)
    password = models.CharField(max_length=50, blank=False , null=False)