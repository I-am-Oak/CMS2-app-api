from rest_framework import serializers, viewsets, permissions
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
            'id', 'user',
            'claim_id', 'description', 'image']

    def create(self, validated_data):
        """Create a claim."""
        tags_data = validated_data.pop('tags', [])
        claim = Claim.objects.create(**validated_data)
        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(**tag_data)
            claim.tags.add(tag)
        return claim


class PolicySerializer(serializers.ModelSerializer):
    """Serializer for policies."""
    claims = ClaimSerializer(many=True, required=False)

    class Meta:
        model = Policy
        fields = ['id', 'user', 'title', 'policy_id',
                  'startDate', 'endDate', 'premiumAmt', 'sumAssured',
                  'claimedAmt', 'claims']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a policy."""
        tags_data = validated_data.pop('tags', [])
        claims_data = validated_data.pop('claims', [])
        policy = Policy.objects.create(**validated_data)
        for tag_data in tags_data:
            tag, _ = Tag.objects.get_or_create(**tag_data)
            policy.tags.add(tag)
        for claim_data in claims_data:
            claim = Claim.objects.create(**claim_data, policy=policy)
            policy.claims.add(claim)
        return policy

class PolicyDetailSerializer(PolicySerializer):
    """Serializer for policy detail view."""

    class Meta(PolicySerializer.Meta):
        fields = PolicySerializer.Meta.fields + ['description']