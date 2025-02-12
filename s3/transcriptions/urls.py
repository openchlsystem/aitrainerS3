from django.urls import path
from .views import (
    AudioFileListCreateView, AudioFileDetailView,
    EvaluatedAudioFileListCreateView, EvaluatedAudioFileDetailView,
    CaseRecordListCreateView, CaseRecordDetailView,
    EvaluationRecordListCreateView, EvaluationRecordDetailView,
    AudioFileChunkListCreateView, AudioFileChunkDetailView,
    EvaluationResultsListCreateView, EvaluationResultsDetailView
)

urlpatterns = [
    # ✅ AudioFile URLs
    path('audio-files/', AudioFileListCreateView.as_view(), name='audiofile-list'),
    path('audio-files/<uuid:pk>/', AudioFileDetailView.as_view(), name='audiofile-detail'),

    # ✅ EvaluatedAudioFile URLs
    path('evaluated-audio/', EvaluatedAudioFileListCreateView.as_view(), name='evaluated-audio-list'),
    path('evaluated-audio/<uuid:pk>/', EvaluatedAudioFileDetailView.as_view(), name='evaluated-audio-detail'),

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
]
