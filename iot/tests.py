from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal

from core.models import Organization
from assets.models import Asset, AssetType
from iot.models import TelemetryData, Alert, Device

User = get_user_model()


class TelemetryModelTest(TestCase):
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

    def test_telemetry_creation(self):
        telemetry = TelemetryData.objects.create(
            asset=self.asset,
            metric='temperature',
            value=Decimal('25.50'),
            unit='°C',
        )

        self.assertEqual(telemetry.metric, 'temperature')
        self.assertEqual(telemetry.value, Decimal('25.50'))
        self.assertEqual(telemetry.asset, self.asset)


class AlertModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Org',
            domain='testorg.com',
            slug='testorg',
            contact_email='test@testorg.com',
        )

        self.user = User.objects.create_user(
            email='operator@test.com',
            password='Test@12345',
            organization=self.org,
        )

        self.asset_type = AssetType.objects.create(
            name='Test Type',
            category='electronic',
        )

        self.asset = Asset.objects.create(
            asset_id='ASSET002',
            name='Test Asset',
            asset_type=self.asset_type,
            organization=self.org,
            created_by=self.user,
        )

    def test_alert_creation(self):
        alert = Alert.objects.create(
            asset=self.asset,
            title='Test Alert',
            message='This is a test alert',
            severity='warning',
            source='test_system',
        )

        self.assertEqual(alert.title, 'Test Alert')
        self.assertEqual(alert.severity, 'warning')
        self.assertFalse(alert.acknowledged)
        self.assertFalse(alert.resolved)
        self.assertEqual(alert.asset, self.asset)
