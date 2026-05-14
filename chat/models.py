from django.db import models
from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    booking_id = models.IntegerField(null=True, blank=True)
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    attachment = models.FileField(upload_to="chat_attachments/", null=True, blank=True)

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.message_text[:30]}"

