"""
tests.py - Test Suite for Lilian AI
======================================
Tests the intent classification, entity extraction, and API endpoints.
Run with: python manage.py test inventory_ai
"""

from django.test import TestCase, Client
from django.urls import reverse
from datetime import date, timedelta
from .models import InventoryItem
from .ai_service import IntentClassifier, EntityExtractor, LilianAI
import json


class IntentClassifierTest(TestCase):
    """Tests that the AI correctly identifies user intent."""

    def test_expired_products(self):
        self.assertEqual(
            IntentClassifier.classify("What products are expired?"),
            'expired_products'
        )
        self.assertEqual(
            IntentClassifier.classify("Show me already expired items"),
            'expired_products'
        )

    def test_near_expiry(self):
        self.assertEqual(
            IntentClassifier.classify("Which products are expiring soon?"),
            'near_expiry'
        )
        self.assertEqual(
            IntentClassifier.classify("Items near expiry"),
            'near_expiry'
        )

    def test_healthy_products(self):
        self.assertEqual(
            IntentClassifier.classify("Show healthy products"),
            'healthy_products'
        )

    def test_expiry_on_date(self):
        self.assertEqual(
            IntentClassifier.classify("What expires on 2025-06-01?"),
            'expiry_on_date'
        )
        self.assertEqual(
            IntentClassifier.classify("Products expiring in June"),
            'expiry_on_date'
        )

    def test_expiry_before_date(self):
        self.assertEqual(
            IntentClassifier.classify("What expires before March 2025?"),
            'expiry_before_date'
        )

    def test_expiry_after_date(self):
        self.assertEqual(
            IntentClassifier.classify("Products expiring after July 2025"),
            'expiry_after_date'
        )

    def test_between_dates(self):
        self.assertEqual(
            IntentClassifier.classify("Products between January and June"),
            'expiry_between_dates'
        )

    def test_status_count(self):
        self.assertEqual(
            IntentClassifier.classify("How many expired products?"),
            'status_count'
        )

    def test_help(self):
        self.assertEqual(
            IntentClassifier.classify("What can you do?"),
            'help'
        )

    def test_inventory_summary(self):
        self.assertEqual(
            IntentClassifier.classify("Give me an inventory overview"),
            'inventory_summary'
        )


class EntityExtractorTest(TestCase):
    """Tests date and keyword extraction from queries."""

    def test_iso_date_extraction(self):
        dates = EntityExtractor.extract_dates("expires on 2025-05-20")
        self.assertEqual(dates['single_date'], date(2025, 5, 20))

    def test_month_extraction(self):
        dates = EntityExtractor.extract_dates("products expiring in June")
        self.assertEqual(dates['month'], 6)

    def test_month_year_extraction(self):
        dates = EntityExtractor.extract_dates("before March 2025")
        self.assertEqual(dates['month'], 3)
        self.assertEqual(dates['year'], 2025)

    def test_date_range_extraction(self):
        dates = EntityExtractor.extract_dates(
            "between January 2025 and June 2025"
        )
        self.assertIn('start_date', dates)
        self.assertIn('end_date', dates)

    def test_relative_days(self):
        dates = EntityExtractor.extract_dates("within 30 days")
        self.assertEqual(dates['start_date'], date.today())
        self.assertEqual(dates['end_date'], date.today() + timedelta(days=30))

    def test_keyword_extraction(self):
        keywords = EntityExtractor.extract_keywords("Show expired petroleum products")
        self.assertEqual(keywords.get('status'), 'expired')
        self.assertEqual(keywords.get('type'), 'petroleum')


class SampleDataMixin:
    """Mixin to create sample inventory data for tests."""

    def create_sample_data(self):
        today = date.today()

        # Expired product
        InventoryItem.objects.create(
            brand="High-Grade Diesel",
            part_number="PD-100",
            type="petroleum",
            usage_rate="500Liters",
            batch_number="B-001",
            shelf_life="5 years",
            expiry_date=today - timedelta(days=30),
            company="Global Fuels Ltd",
            status="expired",
        )

        # Near expiry product
        InventoryItem.objects.create(
            brand="Premium Lubricant",
            part_number="PL-200",
            type="lubricant",
            usage_rate="100Liters",
            batch_number="B-002",
            shelf_life="3 years",
            expiry_date=today + timedelta(days=15),
            company="Lubes Corp",
            status="near_expiry",
        )

        # Healthy product
        InventoryItem.objects.create(
            brand="Industrial Chemical",
            part_number="IC-300",
            type="chemical",
            usage_rate="200Liters",
            batch_number="B-003",
            shelf_life="10 years",
            expiry_date=today + timedelta(days=365),
            company="ChemWorks Inc",
            status="healthy",
        )


class LilianAITest(SampleDataMixin, TestCase):
    """Integration tests for the full AI pipeline."""

    def setUp(self):
        self.create_sample_data()

    def test_expired_query(self):
        response = LilianAI.ask("What products are expired?")
        self.assertEqual(response['intent'], 'expired_products')
        self.assertGreaterEqual(response['count'], 1)

    def test_healthy_query(self):
        response = LilianAI.ask("Show healthy products")
        self.assertEqual(response['intent'], 'healthy_products')
        self.assertGreaterEqual(response['count'], 1)

    def test_near_expiry_query(self):
        response = LilianAI.ask("What's expiring soon?")
        self.assertEqual(response['intent'], 'near_expiry')

    def test_help_query(self):
        response = LilianAI.ask("help")
        self.assertEqual(response['intent'], 'help')
        self.assertIn('Lilian', response['message'])

    def test_summary_query(self):
        response = LilianAI.ask("Give me an inventory overview")
        self.assertEqual(response['intent'], 'inventory_summary')
        self.assertIn('total_products', response['data'])

    def test_status_refresh(self):
        result = LilianAI.refresh_statuses()
        self.assertIn('updated_to_expired', result)
        self.assertIn('timestamp', result)


class APIChatEndpointTest(SampleDataMixin, TestCase):
    """Tests the REST API endpoints."""

    def setUp(self):
        self.client = Client()
        self.create_sample_data()

    def test_chat_endpoint_success(self):
        response = self.client.post(
            '/api/ai/chat/',
            data=json.dumps({'query': 'What products are expired?'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['intent'], 'expired_products')

    def test_chat_endpoint_empty_query(self):
        response = self.client.post(
            '/api/ai/chat/',
            data=json.dumps({'query': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_chat_endpoint_no_query(self):
        response = self.client.post(
            '/api/ai/chat/',
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_status_endpoint(self):
        response = self.client.get('/api/ai/status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('total', data)
        self.assertIn('healthy', data)
        self.assertIn('expired', data)

    def test_health_endpoint(self):
        response = self.client.get('/api/ai/health/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['service'], 'Lilian AI')
        self.assertEqual(data['status'], 'operational')

    def test_refresh_status_endpoint(self):
        response = self.client.post('/api/ai/refresh-status/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
