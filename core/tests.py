from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase as DRFAPITestCase
from rest_framework import status

from .models import Organization

User = get_user_model()


# ============================
# MODEL TESTS
# ============================
class OrganizationModelTest(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Test Org',
            domain='testorg.com',
            contact_email='test@testorg.com'
        )

    def test_organization_creation(self):
        self.assertEqual(self.organization.name, 'Test Org')
        self.assertEqual(self.organization.domain, 'testorg.com')
        self.assertTrue(self.organization.is_active)

    def test_organization_str(self):
        self.assertEqual(str(self.organization), 'Test Org (starter)')


class UserModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Org',
            domain='testorg.com',
            contact_email='test@testorg.com'
        )
        self.user = User.objects.create_user(
            email='test@test.com',
            password='StrongPass123!',
            organization=self.org,
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'test@test.com')
        self.assertEqual(self.user.organization, self.org)
        self.assertTrue(self.user.check_password('StrongPass123!'))

    def test_user_full_name(self):
        self.assertEqual(self.user.full_name, 'Test User')


# ============================
# API TESTS
# ============================
class CoreAPITestCase(DRFAPITestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Org',
            domain='testorg.com',
            contact_email='test@testorg.com'
        )
        self.user = User.objects.create_user(
            email='admin@test.com',
            password='StrongAdmin123!',
            organization=self.org,
            role='org_admin',
            is_staff=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_organizations(self):
        response = self.client.get('/api/core/organizations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_users(self):
        response = self.client.get('/api/core/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
