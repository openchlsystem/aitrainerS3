from django.urls import path
from .views import (
    # Project views
    ProjectListCreateView, ProjectDetailView,
    
    # Audio file views
    AudioFileListCreateView, AudioFileDetailView,
    
    # Processed audio file views
    ProcessedAudioFileListCreateView, ProcessedAudioFileDetailView,
    
    # Diarized audio file views
    DiarizedAudioFileListCreateView, DiarizedAudioFileDetailView,
    
    # Case record views
    CaseRecordListCreateView, CaseRecordDetailView,
    
    # Audio chunk views (renamed from AudioFileChunk)
    AudioChunkListCreateView, AudioChunkDetailView, AudioChunkEvaluateView,
    
    # Evaluation views
    EvaluationResultsListCreateView, EvaluationResultsDetailView, 
    EvaluationResultsSummaryView, EvaluationChunkCategoryView,
    
    # Statistics views
    ChunkStatisticsView, EvaluationCategoryStatisticsView,
    
    # Processing tasks
    ProcessingTaskListCreateView, ProcessingTaskDetailView,
    
    # Specialized views
    ChunksForTranscriptionView, LeaderboardView,
    
    # File upload view
    AudioFilesBulkUploadView
)

urlpatterns = [
    # Project URLs
    path('projects/', ProjectListCreateView.as_view(), name='project-list'),
    path('projects/<uuid:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    
    # AudioFile URLs
    path('audio-files/', AudioFileListCreateView.as_view(), name='audiofile-list'),
    path('audio-files/<uuid:pk>/', AudioFileDetailView.as_view(), name='audiofile-detail'),

    # ProcessedAudioFile URLs (replacing CleanedAudioFile)
    path('processed-audio-files/', ProcessedAudioFileListCreateView.as_view(), name='processed-audio-list'),
    path('processed-audio-files/<uuid:pk>/', ProcessedAudioFileDetailView.as_view(), name='processed-audio-detail'),

    # DiarizedAudioFile URLs
    path('diarized-audio-files/', DiarizedAudioFileListCreateView.as_view(), name='diarized-audio-list'),
    path('diarized-audio-files/<uuid:pk>/', DiarizedAudioFileDetailView.as_view(), name='diarized-audio-detail'),

    # CaseRecord URLs
    path('case-records/', CaseRecordListCreateView.as_view(), name='caserecord-list'),
    path('case-records/<uuid:pk>/', CaseRecordDetailView.as_view(), name='caserecord-detail'),

    # AudioChunk URLs (renamed from AudioFileChunk)
    path('audio-chunks/', AudioChunkListCreateView.as_view(), name='audiochunk-list'),
    path('audio-chunks/<uuid:pk>/', AudioChunkDetailView.as_view(), name='audiochunk-detail'),
    path('audio-chunks/<uuid:pk>/evaluate/', AudioChunkEvaluateView.as_view(), name='audiochunk-evaluate'),

    # ProcessingTask URLs
    path('processing-tasks/', ProcessingTaskListCreateView.as_view(), name='processing-task-list'),
    path('processing-tasks/<uuid:pk>/', ProcessingTaskDetailView.as_view(), name='processing-task-detail'),

    # Statistics URLs
    path('chunk-statistics/', ChunkStatisticsView.as_view(), name='chunk-statistics'),
    path('evaluation-statistics/', EvaluationCategoryStatisticsView.as_view(), name='evaluation-statistics'),

    # EvaluationResults URLs
    path('evaluation-results/', EvaluationResultsListCreateView.as_view(), name='evaluationresults-list'),
    path('evaluation-results/<uuid:pk>/', EvaluationResultsDetailView.as_view(), name='evaluationresults-detail'),
    path('evaluation-summary/', EvaluationResultsSummaryView.as_view(), name='evaluation-summary'),
    path('evaluation-categories/', EvaluationChunkCategoryView.as_view(), name='evaluation-categories'),

    # Specialized views
    path('transcribable/', ChunksForTranscriptionView.as_view(), name='transcribable'),
    path('leader-board/', LeaderboardView.as_view(), name='leader-board'),
    
    # File upload
    path('upload/audio/', AudioFilesBulkUploadView.as_view(), name='audio-bulk-upload'),
]