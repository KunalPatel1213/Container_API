from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import BookingValidation
from .serializers import BookingValidationSerializer

class BookingValidationViewSet(viewsets.ModelViewSet):
    queryset = BookingValidation.objects.all()
    serializer_class = BookingValidationSerializer

    # CREATE (POST)
    def create(self, request, *args, **kwargs):
        serializer = BookingValidationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # READ (GET all + GET single)
    def list(self, request, *args, **kwargs):
        queryset = BookingValidation.objects.all()
        serializer = BookingValidationSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        try:
            booking = BookingValidation.objects.get(pk=pk)
        except BookingValidation.DoesNotExist:
            return Response({"error": "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookingValidationSerializer(booking)
        return Response(serializer.data)

    # UPDATE (PUT/PATCH)
    def update(self, request, pk=None, *args, **kwargs):
        try:
            booking = BookingValidation.objects.get(pk=pk)
        except BookingValidation.DoesNotExist:
            return Response({"error": "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookingValidationSerializer(booking, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None, *args, **kwargs):
        try:
            booking = BookingValidation.objects.get(pk=pk)
        except BookingValidation.DoesNotExist:
            return Response({"error": "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookingValidationSerializer(booking, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    def destroy(self, request, pk=None, *args, **kwargs):
        try:
            booking = BookingValidation.objects.get(pk=pk)
        except BookingValidation.DoesNotExist:
            return Response({"error": "Not Found"}, status=status.HTTP_404_NOT_FOUND)
        booking.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
