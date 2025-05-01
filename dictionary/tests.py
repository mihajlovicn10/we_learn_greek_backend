from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from dictionary.models import Dictionary

User = get_user_model()

class DictionaryAPITestCase(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # Generate token for the user
        self.token = Token.objects.create(user=self.user)
        
        # Set up the client to include token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        # Sample data for dictionary entries
        self.dictionary_data = {
            "greek_word": "λόγος",
            "pronounciation": "logos",
            "translation": "word",
            "user": self.user
        }

        # Create an initial dictionary entry
        self.dictionary_entry = Dictionary.objects.create(**self.dictionary_data)

        # API URLs
        self.list_url = reverse("dictionary_list_create")
        self.detail_url = reverse("dictionary_detail", kwargs={"pk": self.dictionary_entry.pk})

    def test_list_dictionary_entries(self):
        """Test retrieving the list of dictionary entries."""
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["greek_word"], "λόγος")

    def test_retrieve_dictionary_entry(self):
        """Test retrieving a single dictionary entry by ID."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["greek_word"], "λόγος")

    def test_create_dictionary_entry(self):
        """Test creating a new dictionary entry."""
        new_entry = {
            "greek_word": "φωνή",
            "pronounciation": "phone",
            "translation": "voice",
            "user": self.user.id
        }
        response = self.client.post(self.list_url, new_entry)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dictionary.objects.count(), 2)
        self.assertEqual(response.data["greek_word"], "φωνή")

    def test_update_dictionary_entry(self):
        """Test updating an existing dictionary entry."""
        updated_data = {
            "greek_word": "φωνή",
            "pronounciation": "phone",
            "translation": "updated voice",
            "user": self.user.id
        }
        response = self.client.put(self.detail_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.dictionary_entry.refresh_from_db()
        self.assertEqual(self.dictionary_entry.translation, "updated voice")

    def test_delete_dictionary_entry(self):
        """Test deleting a dictionary entry."""
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Dictionary.objects.count(), 0)

    def test_create_entry_unauthenticated(self):
        """Test creating a dictionary entry without authentication."""
        self.client.credentials()  # Remove token
        new_entry = {
            "greek_word": "φωνή",
            "pronounciation": "phone",
            "translation": "voice",
            "user": self.user.id
        }
        response = self.client.post(self.list_url, new_entry)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
