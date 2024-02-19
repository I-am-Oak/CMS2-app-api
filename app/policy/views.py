from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Policy, Tag, Claim
from policy import serializers


# Define a decorator to extend schema view for API documentation
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of IDs to filter',
            ),
            OpenApiParameter(
                'claims',
                OpenApiTypes.STR,
                description='Comma separated list of IDs to filter',
            )
        ]
    )
)
class PolicyViewSet(viewsets.ModelViewSet):
    """View for managing policy APIs."""
    serializer_class = serializers.PolicyDetailSerializer
    queryset = Policy.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Helper method to convert string IDs to integers
    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    # Override get_queryset to filter policies based on tags and claims
    def get_queryset(self):
        """Retrieve policies for authenticated user."""
        tags = self.request.query_params.get('tags')
        claims = self.request.query_params.get('claims')

        user = self.request.user
        if user.is_staff:
            # If user is staff, return all policies
            queryset = Policy.objects.all()
        else:
            # If user is not staff, return policies associated with the user
            queryset = self.queryset.filter(user=user)

        # Apply tag and claim filters
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if claims:
            claim_ids = self._params_to_ints(claims)
            queryset = queryset.filter(claims__id__in=claim_ids)

        return queryset.order_by('-id').distinct()

    # Override perform_create to associate policy with authenticated user
    def perform_create(self, serializer):
        """Create a new policy."""
        serializer.save(user=self.request.user)

    # Define custom action for uploading images to policies
    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to policy."""
        policy = self.get_object()
        serializer = self.get_serializer(policy, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Define a base viewset class for managing policy attributes
@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recipes.',
            )
        ]
    )
)
class BasePolicyAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset class for managing policy attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Override get_queryset to filter by authenticated user and assigned status
    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(int(
            self.request.query_params.get('assigned_only', 0)))
        queryset = self.queryset.all()
        if assigned_only:
            queryset = queryset.filter(policy__isnull=False)

        return queryset.filter(
            user=self.request.user).order_by('-id').distinct()


# Define viewset classes for managing tags and claims
class ClaimViewSet(BasePolicyAttrViewSet):
    """Manage claims in the database."""
    serializer_class = serializers.ClaimSerializer
    queryset = Claim.objects.all()

    def perform_create(self, serializer):
        """Create a new claim."""
        serializer.save(user=self.request.user)

    # Override get_serializer_class to dynamically select serializer
    def get_serializer_class(self):
        """Return the serializer class based on the action."""
        if self.action == 'list':
            return serializers.ClaimSerializer
        elif self.action == 'upload_image':
            return serializers.ClaimImageSerializer

        return self.serializer_class


class TagViewSet(ClaimViewSet):
    """Manage tags in the database."""
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
