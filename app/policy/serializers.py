"""
Serializers for policy APIs
"""
from rest_framework import serializers

from core.models import Policy, Tag, Claims


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claims."""

    class Meta:
        model = Claims
        fields = ['id', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for policys."""
    tags = TagSerializer(many=True, required=False)
    claims = ClaimSerializer(many=True, required=False)

    class Meta:
        model = Policy
        fields = [
            'id', 'title', 'time_minutes', 'price', 'link',
            'tags', 'claims',
            ]
        read_only_fields = ['id']

    def _get_or_create_tags(self, tags, policy):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            status_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            policy.tags.add(status_obj)

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
        tags = validate_data.pop('tags', [])
        claims = validate_data.pop('claims', [])
        policy = Policy.objects.create(**validate_data)
        self._get_or_create_tags(tags, policy)
        self._get_or_create_claims(claims, policy)

        return policy

    def update(self, instance, validated_data):
        """Update policy."""
        tags = validated_data.pop('tags', None)
        claims = validated_data.pop('claims', None)

        if tags is not None:
            instance.tags.clear()
            self._get_or_create_tags(tags, instance)

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
