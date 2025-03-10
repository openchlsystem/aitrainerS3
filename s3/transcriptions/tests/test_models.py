import pytest
from transcriptions.models import AudioFileChunk, EvaluationResults
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestAudioFileChunkModel:
    def test_create_audio_file_chunk(self):
        chunk = AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440000", chunk_file="test.mp3")
        assert chunk.unique_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_audio_file_chunk_str(self):
        chunk = AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440001", chunk_file="test.mp3")
        assert str(chunk) == "550e8400-e29b-41d4-a716-446655440001"

@pytest.mark.django_db
class TestEvaluationResultsModel:
    def test_create_evaluation_result(self):
        user = User.objects.create_user(whatsapp_number="1234567890")
        chunk = AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440002", chunk_file="test.mp3")
        evaluation = EvaluationResults.objects.create(
            audiofilechunk=chunk,
            created_by=user,
            dual_speaker=True
        )
        assert evaluation.audiofilechunk == chunk
        assert evaluation.created_by == user
        assert evaluation.dual_speaker is True
