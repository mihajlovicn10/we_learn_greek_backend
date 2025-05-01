# transparent_words/tests.py
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import TransparentWord

class TransparentWordAPITestCase(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create a test entry
        self.transparent_word = TransparentWord.objects.create(
            target_language="Greek",
            word="πρόβλημα",
            root_word="βλήμα",
            area="Science"
        )

        # Define URLs
        self.list_url = reverse('transparent_word_list_create')
        self.detail_url = reverse('transparent_word_detail', kwargs={'pk': self.transparent_word.pk})

    def test_create_transparent_word(self):
        data = {"target_language": "Latin", "word": "problem", "root_word": "problema", "area": "Philosophy"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TransparentWord.objects.count(), 2)

    def test_list_transparent_words(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_transparent_word(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['word'], "πρόβλημα")

    def test_update_transparent_word(self):
        updated_data = {"target_language": "Greek", "word": "πρόβλημα", "root_word": "λύση", "area": "Education"}
        response = self.client.put(self.detail_url, updated_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.transparent_word.refresh_from_db()
        self.assertEqual(self.transparent_word.root_word, "λύση")

    def test_delete_transparent_word(self):
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TransparentWord.objects.count(), 0)
