from django.contrib.auth.models import User
from django.db import models


class ChatMessage(models.Model):
    sender = models.ForeignKey(
        User,
        related_name="sent_messages",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    receiver = models.ForeignKey(
        User,
        related_name="received_messages",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    booking_id = models.CharField(max_length=100, null=True, blank=True)
    conversation_id = models.CharField(max_length=100, null=True, blank=True)
    provider_id = models.CharField(max_length=100, null=True, blank=True)
    provider_name = models.CharField(max_length=150, blank=True)
    provider_email = models.EmailField(blank=True)
    provider_mobile = models.CharField(max_length=30, blank=True)
    user_name = models.CharField(max_length=150, blank=True)
    user_email = models.EmailField(blank=True)
    user_mobile = models.CharField(max_length=30, blank=True)
    user_location = models.TextField(blank=True)
    total_payment = models.CharField(max_length=100, blank=True)
    sender_role = models.CharField(max_length=30, blank=True)
    sender_name = models.CharField(max_length=150, blank=True)
    message_text = models.TextField(blank=True)
    booking_details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="chat_attachments/", null=True, blank=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["sender", "receiver", "timestamp"]),
            models.Index(fields=["receiver", "is_read"]),
            models.Index(fields=["booking_id", "timestamp"]),
            models.Index(fields=["conversation_id", "timestamp"]),
            models.Index(fields=["provider_id", "user_email", "timestamp"]),
        ]

    def __str__(self):
        sender = self.sender_name or self.sender or self.sender_role or "unknown"
        return f"{sender}: {self.message_text[:30]}"
