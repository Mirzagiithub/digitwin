from django.test import TestCase
from django.utils import timezone
from apps.core.models import Organization
from apps.assets.models import Asset, AssetType
from .models import SimulationScenario, DigitalTwin

class SimulationModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Test Org',
            domain='testorg',
            contact_email='test@testorg.com'
        )
        asset_type = AssetType.objects.create(
            name='Test Type',
            category='electronic'
        )
        self.asset = Asset.objects.create(
            asset_id='ASSET001',
            name='Test Asset',
            asset_type=asset_type,
            organization=self.org
        )
    
    def test_simulation_scenario_creation(self):
        scenario = SimulationScenario.objects.create(
            name='Test Simulation',
            organization=self.org,
            scenario_type='what_if',
            status='draft'
        )
        scenario.target_assets.add(self.asset)
        
        self.assertEqual(scenario.name, 'Test Simulation')
        self.assertEqual(scenario.scenario_type, 'what_if')
        self.assertEqual(scenario.target_assets.count(), 1)
    
    def test_digital_twin_creation(self):
        twin = DigitalTwin.objects.create(
            asset=self.asset,
            twin_type='physics_based',
            model_version='1.0.0'
        )
        
        self.assertEqual(twin.asset, self.asset)
        self.assertEqual(twin.twin_type, 'physics_based')
        self.assertTrue(twin.is_active)
