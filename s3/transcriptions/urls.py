from django.urls import path
from .views import (
    AudioFileChunkDetailView, AudioFileChunkEvaluateView, AudioFileChunkListCreateView, AudioFileChunkStatisticsView, AudioFileListCreateView, AudioFileDetailView,
    CleanedAudioFileListCreateView, CleanedAudioFileDetailView,
    CaseRecordListCreateView, CaseRecordDetailView, CleanedAudioFileToggleApprovedView, CleanedAudioFileToggleDisapprovedView,
    EvaluationRecordListCreateView, EvaluationRecordDetailView,
    EvaluationResultsListCreateView, EvaluationResultsDetailView, LeaderboardView, process_audio_folder
)

urlpatterns = [
    # ✅ AudioFile URLs
    path('audio-files/', AudioFileListCreateView.as_view(), name='audiofile-list'),
    path('audio-files/<uuid:pk>/', AudioFileDetailView.as_view(), name='audiofile-detail'),

    # ✅ EvaluatedAudioFile URLs
    path('cleaned-audio-files/', CleanedAudioFileListCreateView.as_view(), name='evaluated-audio-list'),
    path('cleaned-audio-files/<uuid:pk>/', CleanedAudioFileDetailView.as_view(), name='evaluated-audio-detail'),
 # Update the is_evaluated status of a specific cleaned audio file
    path('cleaned-audio-files/<uuid:pk>/approve/', CleanedAudioFileToggleApprovedView.as_view(), name='toggle_approved'),
    path('cleaned-audio-files/<uuid:pk>/disapprove/', CleanedAudioFileToggleDisapprovedView.as_view(), name='toggle_disapproved'),


    # ✅ CaseRecord URLs
    path('case-records/', CaseRecordListCreateView.as_view(), name='caserecord-list'),
    path('case-records/<uuid:pk>/', CaseRecordDetailView.as_view(), name='caserecord-detail'),

    # ✅ EvaluationRecord URLs
    path('evaluation-records/', EvaluationRecordListCreateView.as_view(), name='evaluationrecord-list'),
    path('evaluation-records/<uuid:pk>/', EvaluationRecordDetailView.as_view(), name='evaluationrecord-detail'),
      
    # ✅ AudioFileChunk URLs
    path('audio-chunks/', AudioFileChunkListCreateView.as_view(), name='audiofilechunk-list'),
    path('audio-chunks/<uuid:pk>/', AudioFileChunkDetailView.as_view(), name='audiofilechunk-detail'),
    # Custom Action (evaluate)
    path('audio-chunks/<uuid:pk>/evaluate/', AudioFileChunkEvaluateView.as_view(), name='audiofilechunk-evaluate'),
    path('chunk-statistics/', AudioFileChunkStatisticsView.as_view(), name='chunk-statistics'),

    # ✅ EvaluationResults URLs
    path('evaluation-results/', EvaluationResultsListCreateView.as_view(), name='evaluationresults-list'),
    path('evaluation-results/<uuid:pk>/', EvaluationResultsDetailView.as_view(), name='evaluationresults-detail'),


   
    
    
    # Bulk Audio file processing 
    path("process-audio/", process_audio_folder, name="process_audio"),
    
    
    # Leaderboard 
    path('leader-board/', LeaderboardView.as_view(), name='Leader_board'),


]
