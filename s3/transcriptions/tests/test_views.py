import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from transcriptions.models import AudioFileChunk, EvaluationResults
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestEvaluationChunkCategoryView:
    def test_get_evaluation_chunk_categories(self):
        client = APIClient()
        user = User.objects.create_user(whatsapp_number="1234567890")
        client.force_authenticate(user=user)

        AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440005", chunk_file="test.mp3")

        url = reverse("evaluation-chunk-category")
        response = client.get(url)
        assert response.status_code == 200

@pytest.mark.django_db
class TestChunksForTranscriptionView:
    def test_get_chunks_for_transcription(self):
        client = APIClient()
        user = User.objects.create_user(whatsapp_number="1234567890")
        client.force_authenticate(user=user)

        url = reverse("chunks-for-transcription")
        response = client.get(url)
        assert response.status_code == 200

@pytest.mark.django_db
class TestLeaderboardView:
    def test_get_leaderboard(self):
        client = APIClient()
        url = reverse("leaderboard")
        response = client.get(url)
        assert response.status_code == 200
