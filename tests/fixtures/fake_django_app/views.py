from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.response import Response


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = None  # Would be User model
        fields = ['id', 'name', 'email', 'age']


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users."""
    serializer_class = UserSerializer

    def list(self, request):
        """List all users."""
        return Response([])

    def create(self, request):
        """Create a new user."""
        return Response({})

    def retrieve(self, request, pk=None):
        """Get a single user."""
        return Response({})

    def update(self, request, pk=None):
        """Update a user."""
        return Response({})

    def destroy(self, request, pk=None):
        """Delete a user."""
        return Response({})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user account."""
        return Response({})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """List active users."""
        return Response([])
