import pytest
from transcriptions.models import AudioFileChunk
from transcriptions.signals import update_chunk_status
from django.db.models.signals import post_save

@pytest.mark.django_db
def test_update_chunk_status_signal(mocker):
    mock_signal = mocker.patch("transcriptions.signals.update_chunk_status")

    chunk = AudioFileChunk.objects.create(unique_id="550e8400-e29b-41d4-a716-446655440006", chunk_file="test.mp3")
    
    post_save.send(sender=AudioFileChunk, instance=chunk)
    
    mock_signal.assert_called_once()
