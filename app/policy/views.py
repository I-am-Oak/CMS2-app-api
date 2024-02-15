"""
Views for the policy APIs
"""

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

from core.models import Policy, Status, Claims
from policy import serializers


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'statuss',
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
class PolicyViewSet(viewsets. ModelViewSet):
    """View for manage policy APIs."""
    serializer_class = serializers. PolicyDetailSerializer
    queryset = Policy.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve policys for authenticated user."""
        statuss = self.request.query_params.get('statuss')
        claims = self.request.query_params.get('claims')
        queryset = self.queryset.all()
        if statuss:
            status_ids = self._params_to_ints(statuss)
            queryset = queryset.filter(statuss__id__in=status_ids)
        if claims:
            claim_ids = self._params_to_ints(claims)
            queryset = queryset.filter(claims__id__in=claim_ids)

        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.PolicySerializer
        elif self.action == 'upload_image':
            return serializers.PolicyImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new policy."""
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """Upload an image to policy."""
        policy = self.get_object()
        serializer = self.get_serializer(policy, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to recepies.',
            )
        ]
    )
)
class BasePolicyAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset.all()
        if assigned_only:
            queryset = queryset.filter(policy__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()


class StatusViewSet(BasePolicyAttrViewSet):
    """Manage statuss in the database."""
    serializer_class = serializers. StatusSerializer
    queryset = Status.objects.all()


class ClaimViewSet(BasePolicyAttrViewSet):
    """Manage claims in the database."""
    serializer_class = serializers. ClaimSerializer
    queryset = Claims.objects.all()
