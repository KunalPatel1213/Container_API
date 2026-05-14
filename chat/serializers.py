from rest_framework import serializers

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "sender",
            "receiver",
            "booking_id",
            "message_text",
            "timestamp",
            "is_read",
            "attachment",
        ]
        extra_kwargs = {
            "timestamp": {"read_only": True},
        }

    def validate(self, attrs):
        # Common source of 400: empty message_text.
        message_text = attrs.get("message_text")
        if message_text is not None and isinstance(message_text, str):
            if not message_text.strip():
                raise serializers.ValidationError({"message_text": "This field may not be blank."})
        return attrs




