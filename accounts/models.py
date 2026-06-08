from django.conf import settings
from django.db import models


class Register(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    fullname = models.CharField(max_length=50)
    company = models.CharField(max_length=100, default="Unknown")
    email = models.EmailField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["fullname"]
        verbose_name = "User Account"
        verbose_name_plural = "User Accounts"

    def __str__(self):
        return f"{self.fullname} ({self.company})"
