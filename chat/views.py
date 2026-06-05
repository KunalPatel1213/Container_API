from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import ChatMessage
from .serializers import ChatMessageSerializer


class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = ChatMessage.objects.all()

        booking_id = self.request.query_params.get("booking_id")
        conversation_id = self.request.query_params.get("conversation_id")
        provider_id = self.request.query_params.get("provider_id")
        user_email = self.request.query_params.get("user_email")

        if booking_id:
            queryset = queryset.filter(booking_id=booking_id)
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)
        if provider_id:
            queryset = queryset.filter(provider_id=provider_id)
        if user_email:
            queryset = queryset.filter(user_email__iexact=user_email)

        return queryset.order_by("timestamp")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(is_read=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"messages": serializer.data})
