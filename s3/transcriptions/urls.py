from django.urls import path
from .views import (
    AudioFileListCreateView, AudioFileDetailView,
    CleanedAudioFileListCreateView, CleanedAudioFileDetailView,
    CaseRecordListCreateView, CaseRecordDetailView, CleanedAudioFileViewSet,
    EvaluationRecordListCreateView, EvaluationRecordDetailView,
    AudioFileChunkListCreateView, AudioFileChunkDetailView,
    EvaluationResultsListCreateView, EvaluationResultsDetailView, chunk_statistics, evaluate_chunk
)

urlpatterns = [
    # ✅ AudioFile URLs
    path('audio-files/', AudioFileListCreateView.as_view(), name='audiofile-list'),
    path('audio-files/<uuid:pk>/', AudioFileDetailView.as_view(), name='audiofile-detail'),

    # ✅ EvaluatedAudioFile URLs
    path('evaluated-audio/', CleanedAudioFileListCreateView.as_view(), name='evaluated-audio-list'),
    path('evaluated-audio/<uuid:pk>/', CleanedAudioFileDetailView.as_view(), name='evaluated-audio-detail'),

    # ✅ CaseRecord URLs
    path('case-records/', CaseRecordListCreateView.as_view(), name='caserecord-list'),
    path('case-records/<uuid:pk>/', CaseRecordDetailView.as_view(), name='caserecord-detail'),

    # ✅ EvaluationRecord URLs
    path('evaluation-records/', EvaluationRecordListCreateView.as_view(), name='evaluationrecord-list'),
    path('evaluation-records/<uuid:pk>/', EvaluationRecordDetailView.as_view(), name='evaluationrecord-detail'),

    # ✅ AudioFileChunk URLs
    path('audio-chunks/', AudioFileChunkListCreateView.as_view(), name='audiofilechunk-list'),
    path('audio-chunks/<uuid:pk>/', AudioFileChunkDetailView.as_view(), name='audiofilechunk-detail'),

    # ✅ EvaluationResults URLs
    path('evaluation-results/', EvaluationResultsListCreateView.as_view(), name='evaluationresults-list'),
    path('evaluation-results/<uuid:pk>/', EvaluationResultsDetailView.as_view(), name='evaluationresults-detail'),

      # List all cleaned audio files
    path('cleaned-audio-files/', CleanedAudioFileViewSet.as_view({'get': 'list'}), name='cleaned_audio_file_list'),
    
    # Update the is_evaluated status of a specific cleaned audio file
    path('cleaned-audio-files/<int:pk>/approve/', CleanedAudioFileViewSet.as_view({'patch': 'toggle_approved'}), name='toggle_approved'),
    path('cleaned-audio-files/<int:pk>/disapprove/', CleanedAudioFileViewSet.as_view({'patch': 'toggle_disapproved'}), name='toggle_disapproved'),

    path('evaluate-chunk/<int:chunk_id>/', evaluate_chunk, name='evaluate_chunk'),
    path('chunk-statistics/', chunk_statistics, name='chunk-statistics'),


]
