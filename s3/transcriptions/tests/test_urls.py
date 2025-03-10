import pytest
from django.urls import reverse, resolve
from transcriptions.views import (
    EvaluationChunkCategoryView,
    ChunksForTranscriptionView,
    ChunkStatisticsSerializerView,
    LeaderboardView,
)

@pytest.mark.django_db
class TestTranscriptionsURLs:
    def test_evaluation_chunk_category_url(self):
        path = reverse("evaluation-categories")  # ✅ Updated name
        assert resolve(path).func.view_class == EvaluationChunkCategoryView

    def test_chunks_for_transcription_url(self):
        path = reverse("transcribable")  # ✅ Updated name
        assert resolve(path).func.view_class == ChunksForTranscriptionView

    def test_chunk_statistics_url(self):
        path = reverse("chunk-statistics")  
        assert resolve(path).func.view_class == ChunkStatisticsSerializerView

    def test_leaderboard_url(self):
        path = reverse("Leader_board")  # ✅ Updated name (case-sensitive)
        assert resolve(path).func.view_class == LeaderboardView
