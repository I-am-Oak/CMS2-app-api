"""
Tests for policy APIs.
"""

from decimal import Decimal
import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Policy, Tag, Claims

from policy.serializers import (
    PolicySerializer,
    PolicyDetailSerializer,
)


RECIPES_URL = reverse('policy:policy-list')


def detail_url(policy_id):
    """Create and return a policy detail URL."""
    return reverse('policy:policy-detail', args=[policy_id])


def image_upload_url(policy_id):
    """Create and return an image upload URL."""
    return reverse('policy:policy-upload-image', args=[policy_id])


def create_policy(user, **params):
    """Create and return a sample policy."""
    defaults = {
        'title': 'Sample ecepie title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample Description',
        'link': 'http://example.com/policy.pdf',
    }
    defaults.update(params)

    policy = Policy.objects.create(user=user, **defaults)
    return policy


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


class PublicPolicyAPITests(TestCase):
    """Test unauthorized API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePolicyAPITests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='user.example.com',
            password='testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrive_policys(self):
        """Test retrieving a list of policys"""
        create_policy(user=self.user)
        create_policy(user=self.user)

        res = self.client.get(RECIPES_URL)

        policys = Policy.objects.all().order_by('-id')
        serializer = PolicySerializer(policys, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_policy_list_limited_to_user(self):
        """test list of policys islimited to authenticated user."""
        other_user = create_user(
            email='other@example.com',
            password='password123',
        )
        create_policy(user=other_user)
        create_policy(user=self.user)

        res = self.client.get(RECIPES_URL)

        policys = Policy.objects.filter(user=self.user)
        serializer = PolicySerializer(policys, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_policy_detail(self):
        """Test get policy detail."""
        policy = create_policy(user=self.user)

        url = detail_url(policy.id)
        res = self.client.get(url)

        serializer = PolicyDetailSerializer(policy)
        self.assertEqual(res.data, serializer.data)

    def test_create_policy(self):
        """Test creating a policy."""
        payload = {
            'title': 'Sample policy',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        policy = Policy.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(policy, k), v)
        self.assertEqual(policy.user, self.user)

    def test_partial_update(self):
        """Test partial update of a policy."""
        original_link = 'https://example.com/policy.pdf'
        policy = create_policy(
            user=self.user,
            title='Sample policy title',
            link=original_link,
        )

        payload = {'title': 'New policy title'}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        policy.refresh_from_db()
        self.assertEqual(policy.title, payload['title'])
        self.assertEqual(policy.link, original_link)
        self.assertEqual(policy.user, self.user)

    def test_full_update(self):
        """Test full update of policy"""
        policy = create_policy(
            user=self.user,
            title='Sample policy title',
            link='https://example.com/policy.pdf',
            description='Sample policy description.',
        )

        payload = {
            'title': 'New policy title',
            'link': 'https://example.com/new-policy.pdf',
            'description': 'New policy description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        url = detail_url(policy.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        policy.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(policy, k), v)
        self.assertEqual(policy.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the policy user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        policy = create_policy(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(policy.id)
        self.client.patch(url, payload)

        policy.refresh_from_db()
        self.assertEqual(policy.user, self.user)

    def test_delete_policy(self):
        """Test deleting a policy successful."""
        policy = create_policy(user=self.user)
        url = detail_url(policy.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Policy.objects.filter(id=policy.id).exists())

    def test_delete_other_users_policy_error(self):
        """Test trying to delete another users policy gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        policy = create_policy(user=new_user)
        url = detail_url(policy.id)
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Policy.objects.filter(id=policy.id).exists())

    def test_create_policy_with_new_tags(self):
        """Test creating a policy with new tags."""
        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        policys = Policy.objects.filter(user=self.user)
        self.assertEqual(policys.count(), 1)
        policy = policys[0]
        self.assertEqual(policy.tags.count(), 2)
        for tag in payload['tags']:
            exists = policy.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_policy_with_existing_tags(self):
        """Test creating a policy with existing status."""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        policys = Policy.objects.filter(user=self.user)
        self.assertEqual(policys.count(), 1)
        policy = policys[0]
        self.assertEqual(policy.tags.count(), 2)
        self.assertIn(tag_indian, policy.tags.all())
        for tag in payload['tags']:
            exists = policy.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_status_on_update(self):
        """Test creating status when updating a policy."""
        policy = create_policy(user=self.user)
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_status = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_status, policy.tags.all())

    def test_update_policy_assign_tags(self):
        """Test assigning an existing status when updating a policy."""
        status_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        policy = create_policy(user=self.user)
        policy.tags.add(status_breakfast)

        status_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(status_lunch, policy.tags.all())
        self.assertNotIn(status_breakfast, policy.tags.all())

    def test_clear_policy_tags(self):
        """Test clearing a policys tags."""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        policy = create_policy(user=self.user)
        policy.tags.add(tag)

        payload = {'tags': []}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(policy.tags.count(), 0)

    def test_create_policy_with_new_claims(self):
        """Test creating a policy with new claims."""
        payload = {
            'title': 'Cauliflower Tacos',
            'time_minutes': 60,
            'price': Decimal('4.30'),
            'claims': [{'name': 'Cauliflower'}, {'name': 'Salt'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        policys = Policy.objects.filter(user=self.user)
        self.assertEqual(policys.count(), 1)
        policy = policys[0]
        self.assertEqual(policy.claims.count(), 2)
        for claims in payload['claims']:
            exists = policy.claims.filter(
                name=claims['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_policy_with_existing_claim(self):
        """Test creating a new policy with existing claims."""
        claims = Claims.objects.create(user=self.user, name='Lemon')
        payload = {
            'title': 'Vietnamese Soup',
            'time_minutes': 25, 'price': '2.55',
            'claims': [{'name': 'Lemon'}, {'name': 'Fish Sauce'}],
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        policys = Policy.objects.filter(user=self.user)
        self.assertEqual(policys.count(), 1)
        policy = policys[0]
        self.assertEqual(policy.claims.count(), 2)
        self.assertIn(claims, policy. claims.all())
        for claims in payload['claims']:
            exists = policy.claims.filter(
                name=claims['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_claim_on_update(self):
        """Test creating an claims when updating a policy."""
        policy = create_policy(user=self.user)

        payload = {'claims': [{'name': 'Limes'}]}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_claim = Claims.objects.get(
            user=self.user,
            name='Limes')
        self.assertIn(new_claim, policy. claims.all())

    def test_update_policy_assign_claim(self):
        """Test assigning an existing claims when updating a policy."""
        claim1 = Claims.objects.create(
            user=self.user,
            name='Pepper')
        policy = create_policy(user=self.user)
        policy.claims.add(claim1)

        claim2 = Claims.objects.create(
            user=self.user,
            name='Chili')
        payload = {'claims': [{'name': 'Chili'}]}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(claim2, policy.claims.all())
        self.assertNotIn(claim1, policy.claims.all())

    def test_clear_policy_claims(self):
        """Test clearing a policys claims."""
        claims = Claims.objects.create(
            user=self.user,
            name='Garlic'
            )
        policy = create_policy(user=self.user)
        policy.claims.add(claims)

        payload = {'claims': []}
        url = detail_url(policy.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(policy.claims.count(), 0)

    def test_filter_by_tags(self):
        """Test filtering policys by tags."""
        r1 = create_policy(user=self.user, title='Thai Vegetable Curry')
        r2 = create_policy(user=self.user, title='Aubergine with Tahini')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)
        r3 = create_policy(user=self.user, title='Fish and chips')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = PolicySerializer(r1)
        s2 = PolicySerializer(r2)
        s3 = PolicySerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

    def test_filter_by_claims(self):
        """Test filtering policys by claims."""
        r1 = create_policy(user=self.user, title='Posh Beans on Toast')
        r2 = create_policy(user=self.user, title='Chicken Cacciatore')
        in1 = Claims.objects.create(user=self.user, name='Feta Cheese')
        in2 = Claims.objects.create(user=self.user, name='Chicken')
        r1.claims.add(in1)
        r2.claims.add(in2)
        r3 = create_policy(user=self.user, title='Red Lentil Dal')

        params = {'claims': f'{in1.id},{in2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = PolicySerializer(r1)
        s2 = PolicySerializer(r2)
        s3 = PolicySerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


class ImageUploadTests (TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.policy = create_policy(user=self.user)

    def tearDown(self):
        self.policy.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a policy."""
        url = image_upload_url(self.policy.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB', (10, 10))
            img.save(image_file, format='JPEG')
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')

        self.policy.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.policy.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.policy.id)
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
