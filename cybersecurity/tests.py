from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from core.models import Organization
from assets.models import Asset, AssetType
from cybersecurity.models import SecurityDigitalTwin, ZeroTrustPolicy

User = get_user_model()


class SecurityDigitalTwinModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Org',
            domain='testorg.com',
            slug='testorg',
            contact_email='test@testorg.com',
        )

        self.user = User.objects.create_user(
            email='admin@test.com',
            password='Test@12345',
            organization=self.org,
            is_staff=True,
        )

        self.asset_type = AssetType.objects.create(
            name='Test Type',
            category='electronic',
        )

        self.asset = Asset.objects.create(
            asset_id='ASSET001',
            name='Test Asset',
            asset_type=self.asset_type,
            organization=self.org,
            created_by=self.user,
        )

    def test_security_twin_creation(self):
        twin = SecurityDigitalTwin.objects.create(
            asset=self.asset,
            twin_type='behavioral',
            security_score=85.5,
            risk_level='medium',
        )

        self.assertEqual(twin.asset, self.asset)
        self.assertEqual(twin.twin_type, 'behavioral')
        self.assertEqual(twin.security_score, 85.5)
        self.assertEqual(twin.risk_level, 'medium')

    def test_security_twin_str(self):
        twin = SecurityDigitalTwin.objects.create(asset=self.asset)
        self.assertIn('Security Twin', str(twin))


class ZeroTrustPolicyModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Org',
            domain='testorg.com',
            slug='testorg',
            contact_email='test@testorg.com',
        )

        self.user = User.objects.create_user(
            email='policyadmin@test.com',
            password='Test@12345',
            organization=self.org,
        )

    def test_zero_trust_policy_creation(self):
        policy = ZeroTrustPolicy.objects.create(
            name='Test Policy',
            organization=self.org,
            framework='nist_800_207',
            mfa_required=True,
            microsegmentation=True,
            created_by=self.user,
        )

        self.assertEqual(policy.name, 'Test Policy')
        self.assertEqual(policy.organization, self.org)
        self.assertEqual(policy.framework, 'nist_800_207')
        self.assertTrue(policy.mfa_required)
        self.assertTrue(policy.microsegmentation)

    def test_zero_trust_policy_str(self):
        policy = ZeroTrustPolicy.objects.create(
            name='ZT Policy',
            organization=self.org,
        )
        self.assertIn('ZT Policy', str(policy))
