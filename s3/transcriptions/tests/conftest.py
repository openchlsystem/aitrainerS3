import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from transcriptions.models import AudioFile, CleanedAudioFile, CaseRecord, AudioFileChunk, EvaluationResults


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(
        whatsapp_number="+1234567890",  # Required field
        password="testpass"
    )


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def audio_file(user):
    return AudioFile.objects.create(
        audio_id="AUDIO123",
        file_size=12345,
        duration=10.0,
        created_by=user
    )


@pytest.fixture
def cleaned_audio_file(user, audio_file):
    return CleanedAudioFile.objects.create(
        audio_file=audio_file,
        is_approved=True,
        created_by=user
    )


@pytest.fixture
def case_record(user, audio_file):
    return CaseRecord.objects.create(
        case_id="CASE123",
        main_category="Category1",
        audio_id=audio_file,
        created_by=user
    )


@pytest.fixture
def audio_chunk(user):
    return AudioFileChunk.objects.create(
        duration=5.2,
        created_by=user
    )


@pytest.fixture
def evaluation_result(user, audio_chunk):
    return EvaluationResults.objects.create(
        audiofilechunk=audio_chunk,
        dual_speaker=False,
        created_by=user
    )
