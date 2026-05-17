from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Container
from .serializers import ContainerSerializer

class ContainerViewSet(viewsets.ModelViewSet):
    queryset = Container.objects.all().order_by('-last_updated')
    serializer_class = ContainerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    # Optional filtering
    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        transport_mode = self.request.query_params.get('transport_mode')

        if status:
            queryset = queryset.filter(status=status)
        if transport_mode:
            queryset = queryset.filter(transport_mode=transport_mode)

        return queryset
