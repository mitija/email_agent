from django.test import TestCase
from core.models import Contact, EmailAddress

class NameMatchingTests(TestCase):
    def setUp(self):
        """Set up test data with various name formats"""
        # Create email addresses for our contacts
        self.email1 = EmailAddress.objects.create(email="john.smith@example.com")
        self.email2 = EmailAddress.objects.create(email="william.jones@example.com")
        self.email3 = EmailAddress.objects.create(email="robert.brown@example.com")
        
        # Create contacts with different name formats
        self.contact1 = Contact.objects.create(name="John William Smith")
        self.contact1.emails.add(self.email1)
        
        self.contact2 = Contact.objects.create(name="William Jones Jr")
        self.contact2.emails.add(self.email2)
        
        self.contact3 = Contact.objects.create(name="Robert James Brown")
        self.contact3.emails.add(self.email3)

    def test_exact_name_match(self):
        """Test exact name matches"""
        results = Contact.objects.search_similar_names("John William Smith")
        self.assertEqual(results[0], self.contact1)
        self.assertTrue(results[0].rank > 0)

    def test_reversed_name_order(self):
        """Test that names match regardless of order"""
        results = Contact.objects.search_similar_names("Smith John")
        self.assertEqual(results[0], self.contact1)
        
        results = Contact.objects.search_similar_names("Smith John William")
        self.assertEqual(results[0], self.contact1)

    def test_partial_name_match(self):
        """Test matching with only part of the name"""
        # Test with first and last name only
        results = Contact.objects.search_similar_names("John Smith")
        self.assertEqual(results[0], self.contact1)
        
        # Test with just the first name
        results = Contact.objects.search_similar_names("John")
        self.assertTrue(self.contact1 in results)
        
        # Test with just the last name
        results = Contact.objects.search_similar_names("Smith")
        self.assertTrue(self.contact1 in results)

    def test_middle_name_variations(self):
        """Test various middle name formats"""
        # Full middle name
        results = Contact.objects.search_similar_names("John William Smith")
        self.assertEqual(results[0], self.contact1)
        
        # Middle initial
        results = Contact.objects.search_similar_names("John W Smith")
        self.assertTrue(self.contact1 in results)
        
        # No middle name
        results = Contact.objects.search_similar_names("John Smith")
        self.assertTrue(self.contact1 in results)

    def test_multiple_matches_ranking(self):
        """Test that multiple matches are ranked appropriately"""
        # Create another Smith
        other_smith = Contact.objects.create(name="Jane Smith")
        
        results = Contact.objects.search_similar_names("Smith")
        
        # Both Smiths should be in results
        smith_contacts = [c for c in results if "Smith" in c.name]
        self.assertEqual(len(smith_contacts), 2)
        
        # Cleanup
        other_smith.delete()

    def test_no_matches(self):
        """Test behavior when no matches are found"""
        results = Contact.objects.search_similar_names("Nonexistent Name")
        self.assertEqual(len(results), 0)

    def test_empty_query(self):
        """Test behavior with empty query"""
        results = Contact.objects.search_similar_names("")
        self.assertEqual(len(results), 0)
        
        results = Contact.objects.search_similar_names(" ")
        self.assertEqual(len(results), 0)

    def test_special_characters(self):
        """Test handling of special characters and accents"""
        # Create a contact with special characters
        special_contact = Contact.objects.create(name="José María García")
        
        # Should match with or without special characters
        results = Contact.objects.search_similar_names("Jose Maria Garcia")
        self.assertTrue(special_contact in results)
        
        results = Contact.objects.search_similar_names("José María García")
        self.assertTrue(special_contact in results)
        
        # Cleanup
        special_contact.delete()

    def test_case_insensitive(self):
        """Test case insensitive matching"""
        results = Contact.objects.search_similar_names("JOHN WILLIAM SMITH")
        self.assertEqual(results[0], self.contact1)
        
        results = Contact.objects.search_similar_names("john william smith")
        self.assertEqual(results[0], self.contact1) 