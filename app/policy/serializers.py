"""
Serializers for policy APIs
"""
from rest_framework import serializers

from core.models import Policy, Status, Claims


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claims."""

    class Meta:
        model = Claims
        fields = ['id', 'name']
        read_only_fields = ['id']


class StatusSerializer(serializers.ModelSerializer):
    """Serializer for statuss."""

    class Meta:
        model = Status
        fields = ['id', 'name']
        read_only_fields = ['id']


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for policys."""
    statuss = StatusSerializer(many=True, required=False)
    claims = ClaimSerializer(many=True, required=False)

    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link',
            'statuss', 'claims',
            ]
        read_only_fields = ['id']

    def _get_or_create_statuss(self, statuss, policy):
        """Handle getting or creating statuss as needed."""
        auth_user = self.context['request'].user
        for status in statuss:
            status_obj, created = Status.objects.get_or_create(
                user=auth_user,
                **status,
            )
            policy.statuss.add(status_obj)

    def _get_or_create_claims(self, claims, policy):
        """Handle getting or creating claims as needed."""
        auth_user = self.context['request'].user
        for claims in claims:
            claim_obj, created = Claims.objects.get_or_create(
                user=auth_user,
                **claims,
            )
            policy.claims.add(claim_obj)

    def create(self, validate_data):
        """Create a policy."""
        statuss = validate_data.pop('statuss', [])
        claims = validate_data.pop('claims', [])
        policy = Policy.objects.create(**validate_data)
        self._get_or_create_statuss(statuss, policy)
        self._get_or_create_claims(claims, policy)

        return policy

    def update(self, instance, validated_data):
        """Update policy."""
        statuss = validated_data.pop('statuss', None)
        claims = validated_data.pop('claims', None)

        if statuss is not None:
            instance.statuss.clear()
            self._get_or_create_statuss(statuss, instance)

        if claims is not None:
            instance.claims.clear()  # Corrected line
            self._get_or_create_claims(claims, instance)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PolicyDetailSerializer(PolicySerializer):
    """Serializer for policy detail view. """

    class Meta(PolicySerializer.Meta):
        fields = PolicySerializer.Meta.fields + ['description', 'image']


class PolicyImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to policys."""

    class Meta:
        model = Policy
        fields = ['id', 'image']
        read_only_fields = ['id']
        extra_kwargs = {'image': {'required': 'True'}}
