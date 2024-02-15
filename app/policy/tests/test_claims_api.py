"""
Test for claims API
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Claims, Policy
from policy.serializers import ClaimSerializer

INGREDIENTS_URL = reverse('policy:claims-list')


def detail_url(claim_id):
    """Create and return an claims detail URL."""
    return reverse('policy:claims-detail', args=[claim_id])


def create_user(email="user@example.com", password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicClaimsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving claims."""
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateClaimsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_claims(self):
        """Test retrieving a list of claims."""
        Claims.objects.create(user=self.user, name='Kale')
        Claims.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(INGREDIENTS_URL)

        claims = Claims.objects.all().order_by('name')
        serializer = ClaimSerializer(claims, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertCountEqual(res.data, serializer.data)

    def test_claims_limited_to_user(self):
        """Test list of claims is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Claims.objects.create(user=user2, name='Salt')
        claims = Claims.objects.create(
            user=self.user,
            name='Pepper')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], claims.name)
        self.assertEqual(res.data[0]['id'], claims.id)

    def test_update_claim(self):
        """Test updating an claims."""
        claims = Claims.objects.create(
            user=self.user,
            name='Cilantro')

        payload = {'name': 'Coriander'}
        url = detail_url(claims.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        claims.refresh_from_db()
        self.assertEqual(claims.name, payload['name'])

    def test_delete_claim(self):
        """Test deleting an claims."""
        claims = Claims.objects.create(
            user=self.user,
            name='Lettuce')

        url = detail_url(claims.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        claims = Claims.objects.filter(user=self.user)
        self.assertFalse(claims.exists())

    def test_filter_claims_assigned_to_policys(self):
        """Test listing claims by those assigned to policys."""
        in1 = Claims.objects.create(user=self.user, name='Apples')
        in2 = Claims.objects.create(user=self.user, name='Turkey')
        policy = Policy.objects.create(
            title='Apple Crumble',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user,
        )
        policy.claims.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = ClaimSerializer(in1)
        s2 = ClaimSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_claims_unique(self):
        """Test filtered claims returns a unique list."""
        ing = Claims.objects.create(user=self.user, name='Eggs')
        Claims.objects.create(user=self.user, name='Lentils')

        policy1 = Policy.objects.create(
            title='Eggs Benedict',
            time_minutes=60,
            price=Decimal('7.00'),
            user=self.user,
        )
        policy2 = Policy.objects.create(
            title='Herb Eggs',
            time_minutes=20,
            price=Decimal('4.00'),
            user=self.user,
        )
        policy1.claims.add(ing)
        policy2.claims.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
