"""
Tests for statuss Api.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Status, Policy
from policy.serializers import StatusSerializer

TAGS_URL = reverse('policy:status-list')


def detail_url(status_id):
    """Create and return a status detail url."""
    return reverse('policy:status-detail', args=[status_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicStatussApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving statuss."""
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateStatussApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_statuss(self):
        """Test retrieving a list of statuss."""
        Status.objects.create(user=self.user, name='Vegan')
        Status.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        statuss = Status.objects.all().order_by('name')
        serializer = StatusSerializer(statuss, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_statuss_limited_to_user(self):
        """Test list of statuss is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Status.objects.create(user=user2, name='Fruity')
        status = Status.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], status.name)
        self.assertEqual(res.data[0]['id'], status.id)

    def test_update_status(self):
        """Test updating a status."""
        status = Status.objects.create(user=self.user, name='After Dinner')

        payload = {'name': 'Dessert'}
        url = detail_url(status.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_0K)
        status.refresh_from_db()
        self.assertEqual(status.name, payload['name'])

    def test_delete_status(self):
        """Test deleting a status."""
        status = Status.objects.create(user=self.user, name='Breakfast')

        url = detail_url(status.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        statuss = Status.objects.filter(user=self.user)
        self.assertFalse(statuss.exists())

    def test_filter_statuss_assigned_to_policys(self):
        """Test listing statuss to those assigned to policys."""
        status1 = Status.objects.create(user=self.user, name='Breakfast')
        status2 = Status.objects.create(user=self.user, name='Lunch')

        policy = Policy.objects.create(
            title='Green Eggs on Toast',
            time_minutes=10,
            price=Decimal('2.50'),
            user=self.user,
        )
        policy.statuss.add(status1)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        s1 = StatusSerializer(status1)
        s2 = StatusSerializer(status2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_statuss_unique(self):
        """Test filtered statuss returns a unique list."""
        status = Status.objects.create(user=self.user, name='Breakfast')
        Status.objects.create(user=self.user, name='Dinner')

        policy1 = Policy.objects.create(
            title='Pancakes',
            time_minutes=5,
            price=Decimal('5.00'),
            user=self.user,
        )
        policy2 = Policy.objects.create(
            title='Porridge',
            time_minutes=3,
            price=Decimal('2.00'),
            user=self.user,
        )
        policy1.statuss.add(status)
        policy2.statuss.add(status)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
