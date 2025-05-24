from django.test import TestCase, Client
from django.urls import reverse
from core.models import Contact, EmailAddress
import json

class ContactSearchTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test contacts
        self.contact1 = Contact.objects.create(name="Raphael Smith")
        self.contact2 = Contact.objects.create(name="John Doe")
        self.contact3 = Contact.objects.create(name="Raphael Johnson")
        
        # Create test client
        self.client = Client()

    def test_search_contacts(self):
        """Test the contact search API endpoint"""
        # Test searching for "raph"
        response = self.client.get('/api/contacts/search/?query=raph')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)  # Should find Raphael Smith and Raphael Johnson
        
        # Verify the results contain the expected contacts
        contact_names = {result['name'] for result in data['results']}
        self.assertEqual(contact_names, {'Raphael Smith', 'Raphael Johnson'})

    def test_search_contacts_empty_query(self):
        """Test the contact search API with empty query"""
        response = self.client.get('/api/contacts/search/?query=')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 0)

    def test_search_contacts_no_matches(self):
        """Test the contact search API with no matching results"""
        response = self.client.get('/api/contacts/search/?query=xyz')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 0) 