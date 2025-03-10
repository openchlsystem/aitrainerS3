import pytest
from transcriptions.serializers import AudioFileChunkSerializer, EvaluationResultsSerializer
from transcriptions.models import AudioFileChunk, EvaluationResults
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestAudioFileChunkSerializer:
    def test_valid_audio_file_chunk_serialization(self):
        chunk = AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440003", chunk_file="test.mp3")
        serializer = AudioFileChunkSerializer(chunk)
        assert serializer.data["unique_id"] == str(chunk.unique_id)

    def test_invalid_audio_file_chunk_serialization(self):
        data = {"chunk_file": "test.mp3"}  # Missing unique_id
        serializer = AudioFileChunkSerializer(data=data)
        assert not serializer.is_valid()

@pytest.mark.django_db
class TestEvaluationResultsSerializer:
    def test_valid_evaluation_results_serialization(self):
        user = User.objects.create_user(whatsapp_number="1234567890")
        chunk = AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440004", chunk_file="test.mp3")
        evaluation = EvaluationResults.objects.create(
            audiofilechunk=chunk, created_by=user, dual_speaker=True
        )
        serializer = EvaluationResultsSerializer(evaluation)
        assert serializer.data["audiofilechunk"] == str(chunk.unique_id)
