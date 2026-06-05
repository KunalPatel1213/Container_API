from rest_framework import serializers

from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    message = serializers.CharField(source="message_text", allow_blank=False)
    created_at = serializers.DateTimeField(source="timestamp", read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            "booking_id",
            "conversation_id",
            "provider_id",
            "provider_name",
            "provider_email",
            "provider_mobile",
            "user_name",
            "user_email",
            "user_mobile",
            "user_location",
            "total_payment",
            "sender_role",
            "sender_name",
            "message",
            "created_at",
            "booking_details",
        ]
        extra_kwargs = {
            "booking_id": {"required": False, "allow_blank": True, "allow_null": True},
            "conversation_id": {"required": False, "allow_blank": True, "allow_null": True},
            "sender_role": {"required": False, "allow_blank": True},
            "sender_name": {"required": False, "allow_blank": True},
            "booking_details": {"required": False},
            "provider_id": {"required": False, "allow_blank": True, "allow_null": True, "write_only": True},
            "provider_name": {"required": False, "allow_blank": True, "write_only": True},
            "provider_email": {"required": False, "allow_blank": True, "write_only": True},
            "provider_mobile": {"required": False, "allow_blank": True, "write_only": True},
            "user_name": {"required": False, "allow_blank": True, "write_only": True},
            "user_email": {"required": False, "allow_blank": True, "write_only": True},
            "user_mobile": {"required": False, "allow_blank": True, "write_only": True},
            "user_location": {"required": False, "allow_blank": True, "write_only": True},
            "total_payment": {"required": False, "allow_blank": True, "write_only": True},
        }

    def validate(self, attrs):
        message = attrs.get("message_text", "")
        if isinstance(message, str):
            attrs["message_text"] = message.strip()

        if not attrs.get("message_text"):
            raise serializers.ValidationError({"message": "This field may not be blank."})

        booking_id = attrs.get("booking_id")
        conversation_id = attrs.get("conversation_id")
        if not booking_id and not conversation_id:
            raise serializers.ValidationError(
                {"booking_id": "booking_id or conversation_id is required."}
            )

        if not conversation_id and booking_id:
            attrs["conversation_id"] = booking_id
        if not booking_id and conversation_id:
            attrs["booking_id"] = conversation_id

        return attrs
