"""
Serializers for policy APIs
"""
from rest_framework import serializers

from core.models import Policy, Tag, Claim, Company


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for Company."""

    class Meta:
        model = Company
        fields = ['id', 'email', 'name']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags."""

    class Meta:
        model = Tag
        fields = '__all__'
        read_only_fields = ['id']


class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for Claims."""
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Claim
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'title',
            'startDate', 'endDate', 'premiumAmt', 'sumAssured']

    def _get_or_create_tags(self, tags, policy):
        """Handle getting or creating tags as needed."""
        auth_user = self.context['request'].user
        for tag in tags:
            status_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            policy.tags.add(status_obj)


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for policies."""

    class Meta:
        model = Policy
        fields = ['id', 'user', 'title', 'policy_id',
                  'startDate', 'endDate', 'premiumAmt', 'sumAssured',
                  'claimedAmt']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a policy."""
        tags = validated_data.pop('tags', [])
        claims = validated_data.pop('claims', [])
        policy = Policy.objects.create(**validated_data)
        self._get_or_create_tags(tags, policy)
        self._get_or_create_claims(claims, policy)

        return policy

    def update(self, instance, validated_data):
        """Update policy."""
        tags_data = validated_data.pop('tags', [])
        claims_data = validated_data.pop('claims', [])

        instance.tags.clear()
        instance.claims.clear()  # Clear all existing claims

        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(**tag_data)
            instance.tags.add(tag)

        for claim_data in claims_data:
            claim, _ = Claim.objects.get_or_create(**claim_data)
            instance.claims.add(claim)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class PolicyDetailSerializer(PolicySerializer):
    """Serializer for policy detail view."""

    class Meta(PolicySerializer.Meta):
        fields = PolicySerializer.Meta.fields + ['description']


class ClaimImageSerializer(serializers.ModelSerializer):
    """Serializer for uploading images to policies."""

    class Meta:
        model = Policy
        fields = ['id', 'image']
        read_only_fields = ['id']
