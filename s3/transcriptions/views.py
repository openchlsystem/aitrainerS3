import datetime
import json
import os
import logging
import subprocess
from time import timezone
from rest_framework import generics, permissions, status, serializers
from .models import (
    ChunkTranscription,
    Project,
    AudioFile,
    ProcessedAudioFile,
    DiarizedAudioFile,
    CaseRecord,
    AudioChunk,
    EvaluationResults,
    ReviewQueue,
    TranscriptionRevision,
    TranscriptionStatus,
    UserStats,
    WorkSession,
)
from .serializers import (
    AudioFileSerializer,
    ChunkStatisticsSerializer,
    ChunkTranscriptionSerializer,
    EnhancedUserStatsSerializer,
    ProcessedAudioFileSerializer,
    DiarizedAudioFileSerializer,
    CaseRecordSerializer,
    EvaluationCategoryStatisticsSerializer,
    EvaluationChunkCategorySerializer,
    AudioChunkSerializer,
    EvaluationResultsSerializer,
    EvaluationResultsLeaderBoardSerializer,
    EvaluationResultsSummarySerializer,
    ProjectSerializer,
    ReviewQueueSerializer,
    TranscriptionRevisionSerializer,
    TranscriptionStatusSerializer,
    WorkSessionSerializer
)
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models import (
    Subquery,
    OuterRef,
    Count,
    FloatField,
    ExpressionWrapper,
    IntegerField,
    Sum,
)
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser

from django.db import transaction

from s3.transcriptions import models

logger = logging.getLogger(__name__)

class BaseListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project from request header
        if hasattr(self.request, 'project') and self.request.project:
            queryset = queryset.filter(project=self.request.project)
            
        return queryset
    
    def perform_create(self, serializer):
        # Set project from request header
        if hasattr(self.request, 'project') and self.request.project:
            serializer.save(
                project=self.request.project,
                created_by=self.request.user,
                updated_by=self.request.user
            )
        else:
            raise serializers.ValidationError({"project": "Project ID header (x-project-id) is required"})

class BaseRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project from request header
        if hasattr(self.request, 'project') and self.request.project:
            queryset = queryset.filter(project=self.request.project)
            
        return queryset
    
    def perform_update(self, serializer):
        # Ensure we keep the same project when updating
        serializer.save(updated_by=self.request.user)

class BaseGenericAPIView(generics.GenericAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project from request header
        if hasattr(self.request, 'project') and self.request.project:
            queryset = queryset.filter(project=self.request.project)
            
        return queryset

class BaseListAPIView(generics.ListAPIView):
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project from request header
        if hasattr(self.request, 'project') and self.request.project:
            queryset = queryset.filter(project=self.request.project)
            
        return queryset

# ✅ Project Views
class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """
        Optionally filter projects by workflow_type
        """
        queryset = Project.objects.all()
        workflow_type = self.request.query_params.get('workflow_type')
        if workflow_type:
            queryset = queryset.filter(workflow_type=workflow_type)
        return queryset

    def perform_create(self, serializer):
        # For ASR workflow, ensure the asr_chunk_duration is set if not provided
        if serializer.validated_data.get('workflow_type') == 'ASR_CORRECTION' and 'asr_chunk_duration' not in serializer.validated_data:
            serializer.save(
                created_by=self.request.user, 
                updated_by=self.request.user,
                asr_chunk_duration=30  # Default value
            )
        else:
            serializer.save(created_by=self.request.user, updated_by=self.request.user)

class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        """
        When updating a project, handle potential workflow type changes
        """
        original_instance = self.get_object()
        original_workflow = original_instance.workflow_type
        new_workflow = serializer.validated_data.get('workflow_type', original_workflow)
        
        # If switching to ASR workflow, ensure asr_chunk_duration is set
        if new_workflow == 'ASR_CORRECTION' and original_workflow != 'ASR_CORRECTION' and 'asr_chunk_duration' not in serializer.validated_data:
            serializer.save(updated_by=self.request.user, asr_chunk_duration=30)
        else:
            serializer.save(updated_by=self.request.user)

# ✅ AudioFile Views
class AudioFileListCreateView(BaseListCreateView):
    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure a project is provided
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({"project": "Project is required"})
        
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class AudioFileDetailView(BaseRetrieveUpdateDestroyView):
    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

# ✅ ProcessedAudioFile Views
class ProcessedAudioFileListCreateView(BaseListCreateView):
    queryset = ProcessedAudioFile.objects.all()
    serializer_class = ProcessedAudioFileSerializer

    def get_queryset(self):
        queryset = super().get_queryset()  # This will apply project filtering from BaseListCreateView
        
        pending_filter = self.request.query_params.get('pending', None)
        if pending_filter == 'true':
            queryset = queryset.filter(is_approved=False, is_disapproved=False)
        
        return queryset

    def perform_create(self, serializer):
        # Check if the processed_file is a string (path)
        processed_file = self.request.data.get('processed_file')
        
        if isinstance(processed_file, str):
            # Make sure the path uses the right prefix
            if not processed_file.startswith('processed/'):
                processed_file = f"processed/{processed_file.split('/')[-1]}"
            
            if hasattr(self.request, 'project') and self.request.project:
                # Create the object directly
                from django.utils import timezone
                
                # Build the instance manually to avoid issues with FileField
                audio_file = ProcessedAudioFile(
                    project=self.request.project,
                    file_size=self.request.data.get('file_size'),
                    duration=self.request.data.get('duration'),
                    created_by=self.request.user,
                    updated_by=self.request.user,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Bypass normal FileField handling and set path directly
                audio_file.processed_file.name = processed_file
                
                # Save without validating the file
                audio_file.save()
                serializer.instance = audio_file
            else:
                raise serializers.ValidationError({"project": "Project ID header (x-project-id) is required"})
        else:
            # Use the parent class implementation for normal file uploads
            super().perform_create(serializer)

class ProcessedAudioFileDetailView(BaseRetrieveUpdateDestroyView):
    queryset = ProcessedAudioFile.objects.all()
    serializer_class = ProcessedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

class ProcessedAudioFileToggleApprovedView(generics.UpdateAPIView):
    queryset = ProcessedAudioFile.objects.all()
    serializer_class = ProcessedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["patch"]
    
    def patch(self, request, *args, **kwargs):
        processed_audio = self.get_object()
        processed_audio.is_approved = not processed_audio.is_approved
        processed_audio.updated_by = request.user
        processed_audio.save()
        return Response(
            {"status": "updated", "is_approved": processed_audio.is_approved},
            status=status.HTTP_200_OK,
        )


class ProcessedAudioFileToggleDisapprovedView(generics.UpdateAPIView):
    queryset = ProcessedAudioFile.objects.all()
    serializer_class = ProcessedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["patch"]
    
    def patch(self, request, *args, **kwargs):
        processed_audio = self.get_object()
        processed_audio.is_disapproved = not processed_audio.is_disapproved
        processed_audio.updated_by = request.user
        processed_audio.save()
        return Response(
            {"status": "updated", "is_disapproved": processed_audio.is_disapproved},
            status=status.HTTP_200_OK,
        )

# ✅ DiarizedAudioFile Views
class DiarizedAudioFileListCreateView(BaseListCreateView):
    queryset = DiarizedAudioFile.objects.all()
    serializer_class = DiarizedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()  # Start with the default queryset
        
        # Filter by project if provided
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project__unique_id=project_id)
        
        return queryset

    def perform_create(self, serializer):
        # Check if the diarized_file is a string (path)
        diarized_file = self.request.data.get('diarized_file')
        
        if isinstance(diarized_file, str):
            # Make sure the path uses the right prefix
            if not diarized_file.startswith('diarized/'):
                diarized_file = f"diarized/{diarized_file.split('/')[-1]}"
            
            if hasattr(self.request, 'project') and self.request.project:
                # Create the object directly
                from django.utils import timezone
                
                # Build the instance manually to avoid issues with FileField
                audio_file = DiarizedAudioFile(
                    project=self.request.project,
                    diarization_result_json_path=self.request.data.get('diarization_result_json_path'),
                    file_size=self.request.data.get('file_size'),
                    duration=self.request.data.get('duration'),
                    created_by=self.request.user,
                    updated_by=self.request.user,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Bypass normal FileField handling and set path directly
                audio_file.diarized_file.name = diarized_file
                
                # Save without validating the file
                audio_file.save()
                serializer.instance = audio_file
            else:
                raise serializers.ValidationError({"project": "Project ID header (x-project-id) is required"})
        else:
            # Use the parent class implementation for normal file uploads
            super().perform_create(serializer)

class DiarizedAudioFileDetailView(BaseRetrieveUpdateDestroyView):
    queryset = DiarizedAudioFile.objects.all()
    serializer_class = DiarizedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

# ✅ CaseRecord Views
class CaseRecordListCreateView(BaseListCreateView):
    queryset = CaseRecord.objects.all()
    serializer_class = CaseRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure a project is provided
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({"project": "Project is required"})
        
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class CaseRecordDetailView(BaseRetrieveUpdateDestroyView):
    queryset = CaseRecord.objects.all()
    serializer_class = CaseRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

# ✅ AudioChunk Views
class AudioChunkListCreateView(BaseListCreateView):
    queryset = AudioChunk.objects.all()
    serializer_class = AudioChunkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()  # Start with the default queryset
        
        # Filter by project if provided
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project__unique_id=project_id)
        
        return queryset

    def perform_create(self, serializer):
        # Check if the chunk_file is a string (path)
        chunk_file = self.request.data.get('chunk_file')
        
        if isinstance(chunk_file, str):
            # Make sure the path uses the right prefix
            if not chunk_file.startswith('chunks/'):
                chunk_file = f"chunks/{chunk_file.split('/')[-1]}"
            
            if hasattr(self.request, 'project') and self.request.project:
                # Create the object directly
                from django.utils import timezone
                
                # Build the instance manually to avoid issues with FileField
                audio_chunk = AudioChunk(
                    project=self.request.project,
                    duration=self.request.data.get('duration'),
                    feature_text=self.request.data.get('feature_text'),
                    locale=str(self.request.data.get('detected_language')).upper() if self.request.data.get('detected_language') else None,
                    created_by=self.request.user,
                    updated_by=self.request.user,
                    created_at=timezone.now(),
                    updated_at=timezone.now()
                )
                
                # Bypass normal FileField handling and set path directly
                audio_chunk.chunk_file.name = chunk_file
                
                # Save without validating the file
                audio_chunk.save()
                serializer.instance = audio_chunk
            else:
                raise serializers.ValidationError({"project": "Project ID header (x-project-id) is required"})
        else:
            # Use the parent class implementation for normal file uploads
            super().perform_create(serializer)

class AudioChunkDetailView(BaseRetrieveUpdateDestroyView):
    queryset = AudioChunk.objects.all()
    serializer_class = AudioChunkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

# ✅ EvaluationResults Views
class EvaluationResultsListCreateView(BaseListCreateView):
    queryset = EvaluationResults.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()  # Start with the default queryset
        
        # Filter by project if provided
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project__unique_id=project_id)
        
        return queryset

    def perform_create(self, serializer):
        # Ensure a project is provided
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({"project": "Project is required"})
        
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class EvaluationResultsDetailView(BaseRetrieveUpdateDestroyView):
    queryset = EvaluationResults.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

# ✅ ProcessingTask Views
# class ProcessingTaskListCreateView(BaseListCreateView):
#     queryset = ProcessingTask.objects.all()
#     serializer_class = ProcessingTaskSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         queryset = super().get_queryset()
        
#         # Filter by project
#         project_id = self.request.query_params.get('project_id')
#         if project_id:
#             queryset = queryset.filter(project__unique_id=project_id)
            
#         # Filter by status
#         status_filter = self.request.query_params.get('status')
#         if status_filter:
#             queryset = queryset.filter(status=status_filter)
            
#         # Filter by task type
#         task_type = self.request.query_params.get('task_type')
#         if task_type:
#             queryset = queryset.filter(task_type=task_type)
            
#         # Filter by audio ID
#         audio_id = self.request.query_params.get('audio_id')
#         if audio_id:
#             queryset = queryset.filter(audio_id=audio_id)
            
#         return queryset.order_by('-created_at')

#     def perform_create(self, serializer):
#         # Ensure a project is provided
#         project_id = self.request.data.get('project')
#         if not project_id:
#             raise serializers.ValidationError({"project": "Project is required"})
        
#         serializer.save(created_by=self.request.user, updated_by=self.request.user)

# class ProcessingTaskDetailView(BaseRetrieveUpdateDestroyView):
#     queryset = ProcessingTask.objects.all()
#     serializer_class = ProcessingTaskSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def perform_update(self, serializer):
#         serializer.save(updated_by=self.request.user)

# Audio Chunk Evaluation View
class AudioChunkEvaluateView(BaseGenericAPIView):
    queryset = AudioChunk.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        chunk = self.get_object()
        user = request.user
        data = request.data

        # Get the project from the chunk
        project = chunk.project
        if not project:
            return Response(
                {"error": "This chunk is not associated with a project."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get evaluation fields from request data
        not_clear = str(data.get("not_clear", "false")).lower() == "true"
        speaker_overlap = str(data.get("speaker_overlap", "false")).lower() == "true"
        dual_speaker = str(data.get("dual_speaker", "false")).lower() == "true"
        interruptive_background_noise = str(data.get("interruptive_background_noise", "false")).lower() == "true"
        silence = str(data.get("silence", "false")).lower() == "true"
        incomplete_word = str(data.get("incomplete_word", "false")).lower() == "true"
        evaluation_notes = data.get("evaluation_notes", "")
        evaluation_start = data.get("evaluation_start")
        evaluation_end = data.get("evaluation_end")
        evaluation_duration = data.get("evaluation_duration")

        # Create or update evaluation
        evaluation, created = EvaluationResults.objects.update_or_create(
            audiofilechunk=chunk,
            created_by=user,
            defaults={
                "project": project,  # Ensure project is set
                "not_clear": not_clear,
                "speaker_overlap": speaker_overlap,
                "dual_speaker": dual_speaker,
                "interruptive_background_noise": interruptive_background_noise,
                "silence": silence,
                "incomplete_word": incomplete_word,
                "evaluation_notes": evaluation_notes,
                "evaluation_start": evaluation_start,
                "evaluation_end": evaluation_end,
                "evaluation_duration": evaluation_duration,
                "updated_by": user,
            },
        )

        if created:
            evaluation.created_by = user
        evaluation.updated_by = user
        evaluation.save()

        serializer = EvaluationResultsSerializer(evaluation)

        return Response(
            {
                "message": "Evaluation saved successfully",
                "evaluation": serializer.data,
                "created": created,
            },
            status=status.HTTP_200_OK,
        )
    
# Evaluation Results Summary View
class EvaluationResultsSummaryView(BaseListAPIView):
    serializer_class = EvaluationResultsSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = EvaluationResultsSummarySerializer.get_queryset(project=getattr(self.request, 'project', None))
        
        # Filter by project if provided
        # project_id = self.request.query_params.get('project_id')
        # if project_id:
        #     queryset = queryset.filter(
        #         audiofilechunk__in=AudioChunk.objects.filter(project__unique_id=project_id).values_list('unique_id', flat=True)
        #     )
            
        return queryset

class EvaluationChunkCategoryView(BaseGenericAPIView):
    serializer_class = EvaluationChunkCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AudioChunk.objects.all()  # Define the base queryset

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Get the filtered queryset from the base class
        # This already handles the project filtering from request.project
        base_queryset = self.get_queryset()

        # Subquery to count evaluations per chunk
        evaluation_counts = EvaluationResults.objects.filter(
            audiofilechunk=OuterRef('unique_id')
        ).values('audiofilechunk').annotate(count=Count('unique_id')).values('count')

        # Query chunks and annotate with evaluation count
        chunks = base_queryset.annotate(
            evaluation_count=Subquery(evaluation_counts, output_field=IntegerField())
        )

        # Categorize and fetch full chunk details
        not_evaluated_chunks = list(chunks.filter(evaluation_count__isnull=True).values())
        one_evaluation_chunks = list(chunks.filter(evaluation_count=1).values())
        # Modified to focus on chunks with exactly 1 evaluation (not 2)
        # since we now need only 2 evaluations total for transcription

        # Helper function to build full URL
        def get_full_url(chunk):
            chunk_obj = AudioChunk.objects.get(unique_id=chunk['unique_id'])
            return request.build_absolute_uri(f"/shared/{chunk_obj.chunk_file}")

        # Collect unique_ids for categorized chunks (excluding not_evaluated)
        evaluated_chunk_ids = [chunk["unique_id"] for chunk in one_evaluation_chunks]

        # Fetch evaluations done by the current user for those chunks
        user_evaluations = EvaluationResults.objects.filter(
            audiofilechunk__in=evaluated_chunk_ids, created_by=user
        ).values_list("audiofilechunk", flat=True)

        # Convert to a set for fast lookup
        user_evaluated_set = set(user_evaluations)

        # Append evaluated_by_user boolean to the required categories
        for chunk in one_evaluation_chunks:
            chunk["evaluated_by_user"] = chunk["unique_id"] in user_evaluated_set
        
        # Append full URL for chunk_file
        for chunk in not_evaluated_chunks:
            chunk['file_url'] = get_full_url(chunk)

        for chunk in one_evaluation_chunks:
            chunk['file_url'] = get_full_url(chunk)

        return Response({
            "not_evaluated": not_evaluated_chunks,
            "one_evaluation": one_evaluation_chunks,
            # Removed "two_evaluations" category since we now only need 2 total evaluations
            # for transcription eligibility, so we don't need a separate "two evaluations" bucket
        })

# Chunks for Transcription View
class ChunksForTranscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get project_id from request if provided
        project_id = request.query_params.get('project_id')
        
        # Get project either from query param or request
        project = None
        if project_id:
            try:
                project = Project.objects.get(unique_id=project_id)
            except Project.DoesNotExist:
                return Response({"error": f"Project with ID {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        elif hasattr(request, 'project') and request.project:
            project = request.project
        
        if not project:
            return Response({"error": "Project is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check workflow type and handle accordingly
        if project.workflow_type == 'ASR_CORRECTION':
            # ASR workflow
            return self._handle_asr_workflow(request, project)
        else:
            # Default manual transcription workflow
            return self._handle_manual_workflow(request, project)
    
    def _handle_manual_workflow(self, request, project):
        # Updated logic for manual transcription with new workflow
        base_queryset = AudioChunk.objects.filter(project=project)
        
        # Filter out chunks that already have transcriptions in progress or completed
        available_chunks = base_queryset.filter(
            # Not assigned to anyone
            is_assigned=False
        ).exclude(
            # Exclude chunks that have transcriptions with status other than REJECTED
            # (This means DRAFT, PENDING_REVIEW, APPROVED are all excluded)
            models.Q(current_transcription__isnull=False) & 
            ~models.Q(current_transcription__status__name='REJECTED')
        )
        
        total_choices = 6  # Total number of boolean fields

        # Subquery to count evaluations and calculate total boolean flags (true values)
        evaluation_summary = (
            EvaluationResults.objects.filter(audiofilechunk=OuterRef("unique_id"))
            .values("audiofilechunk")
            .annotate(
                evaluation_count=Count("unique_id"),
                # Sum of all boolean fields - used to determine if ANY issue was flagged
                total_boolean_sum=Sum("not_clear", output_field=IntegerField())
                + Sum("speaker_overlap", output_field=IntegerField())
                + Sum("dual_speaker", output_field=IntegerField())
                + Sum("interruptive_background_noise", output_field=IntegerField())
                + Sum("silence", output_field=IntegerField())
                + Sum("incomplete_word", output_field=IntegerField()),
            )
            .values("evaluation_count", "total_boolean_sum")
        )

        # Query chunks and annotate with evaluation count & total boolean sum
        chunks = available_chunks.annotate(
            evaluation_count=Subquery(evaluation_summary.values("evaluation_count")),
            total_boolean_sum=Subquery(evaluation_summary.values("total_boolean_sum")),
        )

        # Chunks with evaluation_count ≥ 2 and no issues flagged
        chunks_for_transcription = chunks.filter(
            evaluation_count__gte=2,
            total_boolean_sum=0
        )
        
        # Helper function to get full URL
        def get_full_url(chunk):
            return request.build_absolute_uri(f"/shared/{chunk.chunk_file}")
        
        # Serialize chunks - include both regular data and transcription data
        resultingChunks = []
        
        for chunk in chunks_for_transcription:
            # Serialize the chunk
            chunk_data = AudioChunkSerializer(chunk).data
            
            # Add the file URL
            chunk_data['file_url'] = get_full_url(chunk)
            
            # Check if there's a rejected transcription to include
            try:
                transcription = ChunkTranscription.objects.filter(
                    audio_chunk=chunk,
                    status__name='REJECTED'
                ).first()
                
                if transcription:
                    chunk_data['transcription'] = ChunkTranscriptionSerializer(transcription).data
                    chunk_data['previous_text'] = transcription.text
            except:
                pass
                
            resultingChunks.append(chunk_data)

        return Response({
            "chunks_for_transcription": resultingChunks
        })
    
    def _handle_asr_workflow(self, request, project):
        # Updated logic for ASR correction workflow
        
        # Get chunks that have ASR-generated transcriptions in DRAFT status
        chunks = AudioChunk.objects.filter(
            project=project,
            is_assigned=False,
            current_transcription__is_asr_generated=True,
            current_transcription__status__name='DRAFT'
        )
        
        # Helper function to get full URL
        def get_full_url(chunk):
            return request.build_absolute_uri(f"/shared/{chunk.chunk_file}")
        
        # Serialize chunks including transcription data
        resultingChunks = []
        
        for chunk in chunks:
            # Serialize the chunk
            chunk_data = AudioChunkSerializer(chunk).data
            
            # Add the file URL
            chunk_data['file_url'] = get_full_url(chunk)
            
            # Include the ASR transcription
            try:
                transcription = chunk.current_transcription
                chunk_data['transcription'] = ChunkTranscriptionSerializer(transcription).data
                chunk_data['asr_text'] = transcription.text
            except:
                pass
                
            resultingChunks.append(chunk_data)
        
        return Response({
            "chunks_for_transcription": resultingChunks
        })

# Chunk Statistics View
class ChunkStatisticsView(BaseGenericAPIView):
    serializer_class = ChunkStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AudioChunk.objects.all()  # Define the base queryset
    
    def get(self, request, *args, **kwargs):
        # Get the filtered queryset from the base class
        # This already handles the project filtering from request.project
        base_queryset = self.get_queryset()
        
        total_choices = 6  # Total number of boolean fields
        
        evaluation_summary = (
            EvaluationResults.objects.filter(audiofilechunk=OuterRef("unique_id"))
            .values("audiofilechunk")
            .annotate(
                evaluation_count=Count("unique_id"),
                total_boolean_sum=Sum("not_clear", output_field=IntegerField())
                + Sum("speaker_overlap", output_field=IntegerField())
                + Sum("dual_speaker", output_field=IntegerField())
                + Sum("interruptive_background_noise", output_field=IntegerField())
                + Sum("silence", output_field=IntegerField())
                + Sum("incomplete_word", output_field=IntegerField()),
            )
            .values("evaluation_count", "total_boolean_sum")
        )
        
        chunks = base_queryset.annotate(
            evaluation_count=Subquery(evaluation_summary.values("evaluation_count")),
            total_boolean_sum=Subquery(evaluation_summary.values("total_boolean_sum")),
        )
        
        total_chunks = chunks.count()
        not_evaluated = chunks.filter(evaluation_count__isnull=True).count()
        one_evaluation = chunks.filter(evaluation_count=1).count()
        two_evaluations = chunks.filter(evaluation_count=2).count()
        three_or_more_evaluations = chunks.filter(evaluation_count__gte=3).count()
        
        # New logic: chunks need 2+ evaluations AND no issues flagged (total_boolean_sum=0)
        ready_for_transcription = chunks.filter(
            evaluation_count__gte=2,     # Changed from 3 to 2
            total_boolean_sum=0          # No issues flagged
        ).count()
        
        transcribed_chunks = (
            chunks.exclude(feature_text__isnull=True).exclude(feature_text="").count()
        )
        
        evaluation_completion_rate = (
            ((total_chunks - not_evaluated) / total_chunks) * 100
            if total_chunks > 0
            else 0
        )
        
        stats = {
            "total_chunks": total_chunks,
            "not_evaluated": not_evaluated,
            "one_evaluation": one_evaluation,
            "two_evaluations": two_evaluations,
            "three_or_more_evaluations": three_or_more_evaluations,
            "ready_for_transcription": ready_for_transcription,
            "evaluation_completion_rate": round(evaluation_completion_rate, 2),
            "transcribed_chunks": transcribed_chunks,
        }
        return Response(stats)
# Evaluation Category Statistics View
class EvaluationCategoryStatisticsView(BaseGenericAPIView):
    serializer_class = EvaluationCategoryStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = EvaluationResults.objects.all()  # Define the base queryset

    def get(self, request, *args, **kwargs):
        # Get the filtered queryset from the base class
        # This already handles the project filtering from request.project
        queryset = self.get_queryset()
        
        total_evaluations = queryset.count()

        # Using the filtered queryset for aggregations
        stats = queryset.aggregate(
            not_clear_count=Sum("not_clear", output_field=IntegerField()),
            speaker_overlap_count=Sum("speaker_overlap", output_field=IntegerField()),
            dual_speaker_count=Sum("dual_speaker", output_field=IntegerField()),
            interruptive_background_noise_count=Sum(
                "interruptive_background_noise", output_field=IntegerField()
            ),
            silence_count=Sum("silence", output_field=IntegerField()),
            incomplete_word_count=Sum("incomplete_word", output_field=IntegerField()),
        )

        # Replace None values with 0
        for key in stats:
            if stats[key] is None:
                stats[key] = 0

        stats["total_evaluated_chunks"] = total_evaluations

        return Response(stats)
    

class LeaderboardView(BaseGenericAPIView):
    queryset = EvaluationResults.objects.all()  # Define the base queryset
    
    def get(self, request, *args, **kwargs):
        # Get the filtered queryset from the base class
        filtered_queryset = self.get_queryset()
        
        # Get leaderboard data using the filtered queryset
        leaderboard_data = EvaluationResultsLeaderBoardSerializer.get_leaderboard(
            queryset=filtered_queryset
        )
        
        serializer = EvaluationResultsLeaderBoardSerializer(leaderboard_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AudioFilesBulkUploadView(BaseGenericAPIView):
    """
    View to handle bulk audio file uploads from the Vue3 frontend
    Supports folder upload where users select a folder containing audio files
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    queryset = AudioFile.objects.all()  # Adding a queryset attribute
    
    def post(self, request):
        try:
            # Get project from request (set by middleware)
            if not hasattr(request, 'project') or not request.project:
                return JsonResponse({"error": "Project ID header (x-project-id) is required"}, status=400)
            
            project = request.project
            
            # Get the files
            files = request.FILES.getlist('files')
            if not files:
                return JsonResponse({"error": "No files provided"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create directory if it doesn't exist
            raw_dir = os.path.join('shared', 'raw')
            os.makedirs(raw_dir, exist_ok=True)
            
            # Process all files
            results = []
            for audio_file in files:
                filename = audio_file.name
                
                # Validate file type
                if not filename.lower().endswith(('.wav', '.mp3', '.ogg', '.flac')):
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Unsupported file format"
                    })
                    continue
                
                # Save file to the shared directory
                file_path = os.path.join('raw', filename)
                full_path = os.path.join('shared', file_path)
                
                with open(full_path, 'wb+') as destination:
                    for chunk in audio_file.chunks():
                        destination.write(chunk)
                
                # Get audio metadata
                duration, file_size = self.get_audio_metadata(full_path)
                
                if duration is None or file_size is None:
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": "Failed to extract audio metadata"
                    })
                    continue
                
                # Generate a unique audio_id
                audio_id = os.path.splitext(filename)[0]
                
                # Create or update AudioFile record
                try:
                    audio_file_obj, created = AudioFile.objects.get_or_create(
                        audio_id=audio_id,
                        project=project,  # Add project to filter criteria for get_or_create
                        defaults={
                            'audio_file': file_path,
                            'file_size': file_size,
                            'duration': duration,
                            'is_processed': False,
                            'created_by': request.user,
                            'updated_by': request.user
                        }
                    )
                    
                    if not created:
                        # Update existing record
                        audio_file_obj.audio_file = file_path
                        audio_file_obj.file_size = file_size
                        audio_file_obj.duration = duration
                        audio_file_obj.updated_by = request.user
                        audio_file_obj.save()
                    
                    results.append({
                        "filename": filename,
                        "status": "success",
                        "audio_id": audio_file_obj.audio_id,
                        "id": str(audio_file_obj.unique_id),
                        "duration": duration,
                        "file_size": file_size,
                        "file_path": audio_file_obj.full_path,
                        "created": created
                    })
                    
                except Exception as e:
                    results.append({
                        "filename": filename,
                        "status": "error",
                        "message": str(e)
                    })
            
            # Return summary
            successful = len([r for r in results if r["status"] == "success"])
            failed = len([r for r in results if r["status"] == "error"])
            
            return JsonResponse({
                "status": "completed",
                "summary": {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed
                },
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Error in bulk upload: {str(e)}")
            return JsonResponse(
                {"error": f"Failed to process files: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_audio_metadata(self, filepath):
        """Extract metadata using ffprobe"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration,size",
                    "-of",
                    "json",
                    filepath,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            metadata = json.loads(result.stdout)
            duration = float(metadata["format"]["duration"])
            file_size = int(metadata["format"]["size"])
            return duration, file_size
        except Exception as e:
            logger.error(f"Error extracting metadata for {filepath}: {e}")
            return None, None
        
# TranscriptionStatus views
class TranscriptionStatusListView(BaseListCreateView):
    queryset = TranscriptionStatus.objects.all()
    serializer_class = TranscriptionStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

class TranscriptionStatusDetailView(BaseRetrieveUpdateDestroyView):
    queryset = TranscriptionStatus.objects.all()
    serializer_class = TranscriptionStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

# ChunkTranscription views
class ChunkTranscriptionListCreateView(BaseListCreateView):
    queryset = ChunkTranscription.objects.all()
    serializer_class = ChunkTranscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status_name = self.request.query_params.get('status')
        if status_name:
            queryset = queryset.filter(status__name=status_name)
            
        # Filter by transcriber
        transcriber_id = self.request.query_params.get('transcriber')
        if transcriber_id:
            queryset = queryset.filter(transcriber__unique_id=transcriber_id)
            
        # Filter by reviewer
        reviewer_id = self.request.query_params.get('reviewer')
        if reviewer_id:
            queryset = queryset.filter(reviewer__unique_id=reviewer_id)
            
        # Filter by ASR generation
        is_asr = self.request.query_params.get('is_asr_generated')
        if is_asr is not None:
            is_asr_bool = is_asr.lower() == 'true'
            queryset = queryset.filter(is_asr_generated=is_asr_bool)
            
        return queryset

class ChunkTranscriptionDetailView(BaseRetrieveUpdateDestroyView):
    queryset = ChunkTranscription.objects.all()
    serializer_class = ChunkTranscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

# WorkSession views
class WorkSessionListCreateView(BaseListCreateView):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by user
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user__unique_id=user_id)
            
        # Filter by session type
        session_type = self.request.query_params.get('session_type')
        if session_type:
            queryset = queryset.filter(session_type=session_type)
            
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(start_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_time__lte=end_date)
            
        return queryset

class WorkSessionDetailView(BaseRetrieveUpdateDestroyView):
    queryset = WorkSession.objects.all()
    serializer_class = WorkSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        """Special method to close a work session"""
        session = self.get_object()
        
        if 'close_session' in request.data and request.data['close_session']:
            session.close_session()
            
        return super().patch(request, *args, **kwargs)

# Review Queue views
class ReviewQueueListView(BaseListAPIView):
    queryset = ReviewQueue.objects.all()
    serializer_class = ReviewQueueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by assigned status
        is_assigned = self.request.query_params.get('is_assigned')
        if is_assigned is not None:
            is_assigned_bool = is_assigned.lower() == 'true'
            queryset = queryset.filter(is_assigned=is_assigned_bool)
            
        # Filter by priority
        min_priority = self.request.query_params.get('min_priority')
        if min_priority:
            queryset = queryset.filter(priority__gte=int(min_priority))
            
        return queryset

class ReviewQueueDetailView(BaseRetrieveUpdateDestroyView):
    queryset = ReviewQueue.objects.all()
    serializer_class = ReviewQueueSerializer
    permission_classes = [permissions.IsAuthenticated]

# Enhanced User Stats views
class UserStatsListView(BaseListAPIView):
    queryset = UserStats.objects.all()
    serializer_class = EnhancedUserStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Sort by field
        sort_by = self.request.query_params.get('sort_by', 'transcriptions_created')
        direction = self.request.query_params.get('direction', 'desc')
        
        if direction == 'desc':
            sort_by = f'-{sort_by}'
            
        return queryset.order_by(sort_by)

class UserStatsDetailView(BaseRetrieveUpdateDestroyView):
    queryset = UserStats.objects.all()
    serializer_class = EnhancedUserStatsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def patch(self, request, *args, **kwargs):
        """Special method to update counts and metrics"""
        user_stats = self.get_object()
        
        if 'update_counts' in request.data and request.data['update_counts']:
            user_stats.update_counts()
            
        if 'update_metrics' in request.data and request.data['update_metrics']:
            user_stats.update_quality_metrics()
            
        return super().patch(request, *args, **kwargs)



# Get next chunk for transcription
class GetChunkForTranscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Assign a chunk to the current user for transcription"""
        # Get project from request
        if not hasattr(request, 'project') or not request.project:
            return Response({"error": "Project ID header (x-project-id) is required"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        project = request.project
        user = request.user
        
        with transaction.atomic():
            # Check workflow type and handle differently based on that
            if project.workflow_type == 'ASR_CORRECTION':
                # For ASR workflow, find chunks with ASR-generated transcriptions
                chunks = AudioChunk.objects.filter(
                    project=project,
                    is_assigned=False,
                    current_transcription__is_asr_generated=True,
                    current_transcription__status__name='DRAFT'
                ).order_by('?')[:1]
            else:
                # For manual workflow, find chunks ready for transcription based on evaluations
                # and without any existing transcription
                chunks = AudioChunk.objects.filter(
                    project=project,
                    is_assigned=False
                ).exclude(
                    current_transcription__isnull=False
                ).annotate(
                    evaluation_count=Count('evaluation_results')
                ).filter(
                    evaluation_count__gte=2
                ).order_by('?')[:1]
            
            if not chunks.exists():
                return Response({"message": "No chunks available for transcription"},
                               status=status.HTTP_404_NOT_FOUND)
            
            chunk = chunks.first()
            
            # Assign the chunk to the user
            chunk.assign_to_user(user)
            
            # Start a work session
            session = WorkSession.objects.create(
                user=user,
                session_type='TRANSCRIPTION',
                start_time=timezone.now(),
                created_by=user,
                updated_by=user
            )
            
            # Create a transcription if it doesn't exist
            draft_status = TranscriptionStatus.objects.get(name='DRAFT')
            
            # Check if the chunk already has a transcription (e.g., ASR generated)
            try:
                transcription = ChunkTranscription.objects.get(audio_chunk=chunk)
                # Update transcriber if needed
                if not transcription.transcriber:
                    transcription.transcriber = user
                    transcription.save(update_fields=['transcriber', 'updated_by'])
            except ChunkTranscription.DoesNotExist:
                # Create a new transcription record
                transcription = ChunkTranscription.objects.create(
                    audio_chunk=chunk,
                    text=chunk.feature_text or '',  # Use existing feature_text if any
                    status=draft_status,
                    transcriber=user,
                    is_asr_generated=False,
                    created_by=user,
                    updated_by=user
                )
            
            # Return the chunk, transcription, and session in response
            return Response({
                "chunk": AudioChunkSerializer(chunk).data,
                "transcription": ChunkTranscriptionSerializer(transcription).data,
                "session": WorkSessionSerializer(session).data,
                "file_url": request.build_absolute_uri(f"/shared/{chunk.chunk_file}")
            }, status=status.HTTP_200_OK)

# Update transcription
class UpdateTranscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, chunk_id):
        """Update a transcription for a specific chunk"""
        # Get user and project
        user = request.user
        
        # Get chunk and verify assignment
        try:
            chunk = AudioChunk.objects.get(unique_id=chunk_id)
        except AudioChunk.DoesNotExist:
            return Response({"error": "Chunk not found"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        if chunk.assigned_to != user:
            return Response({"error": "This chunk is not assigned to you"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Get the transcription
        try:
            transcription = ChunkTranscription.objects.get(audio_chunk=chunk)
        except ChunkTranscription.DoesNotExist:
            return Response({"error": "Transcription not found"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Get request data
        new_text = request.data.get('text', '')
        submit_for_review = request.data.get('submit_for_review', False)
        session_id = request.data.get('session_id')
        
        # Track previous state for revision history
        previous_text = transcription.text
        previous_status = transcription.status
        
        with transaction.atomic():
            # Update text
            transcription.text = new_text
            transcription.updated_by = user
            
            # Also update feature_text for compatibility during transition
            chunk.feature_text = new_text
            chunk.updated_by = user
            chunk.save(update_fields=['feature_text', 'updated_by'])
            
            # Create revision entry
            revision = None
            
            # If submitting for review, change status
            if submit_for_review:
                pending_status = TranscriptionStatus.objects.get(name='PENDING_REVIEW')
                transcription.status = pending_status
                transcription.save(update_fields=['text', 'status', 'updated_by'])
                
                # Add to review queue
                ReviewQueue.objects.create(
                    transcription=transcription,
                    priority=5,  # Default priority
                    created_by=user,
                    updated_by=user
                )
                
                # Create revision with status change
                revision = TranscriptionRevision.objects.create(
                    transcription=transcription,
                    previous_text=previous_text,
                    new_text=new_text,
                    previous_status=previous_status,
                    new_status=pending_status,
                    created_by=user,
                    updated_by=user
                )
                
                # Release the chunk assignment
                chunk.release_assignment()
                
                # Close the work session if provided
                if session_id:
                    try:
                        session = WorkSession.objects.get(unique_id=session_id)
                        session.close_session()
                        session.chunks_processed += 1
                        session.save(update_fields=['end_time', 'duration', 'chunks_processed'])
                    except WorkSession.DoesNotExist:
                        pass
            else:
                # Just saving without status change
                transcription.save(update_fields=['text', 'updated_by'])
                
                # Create revision for text change only if text changed
                if previous_text != new_text:
                    revision = TranscriptionRevision.objects.create(
                        transcription=transcription,
                        previous_text=previous_text,
                        new_text=new_text,
                        previous_status=previous_status,
                        new_status=previous_status,  # Same status, just text change
                        created_by=user,
                        updated_by=user
                    )
            
            return Response({
                "transcription": ChunkTranscriptionSerializer(transcription).data,
                "revision": TranscriptionRevisionSerializer(revision).data if revision else None,
                "submitted_for_review": submit_for_review
            }, status=status.HTTP_200_OK)

# Get next item for review
class GetItemForReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Assign a transcription to the current user for review"""
        # Get project from request
        if not hasattr(request, 'project') or not request.project:
            return Response({"error": "Project ID header (x-project-id) is required"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        project = request.project
        user = request.user
        
        with transaction.atomic():
            # Find an unassigned item in the review queue for this project
            # that wasn't transcribed by this user
            pending_status = TranscriptionStatus.objects.get(name='PENDING_REVIEW')
            
            review_items = ReviewQueue.objects.filter(
                is_assigned=False,
                transcription__audio_chunk__project=project,
                transcription__status=pending_status
            ).exclude(
                transcription__transcriber=user  # Exclude items transcribed by this user
            ).order_by('-priority', 'created_at')[:1]
            
            if not review_items.exists():
                return Response({"message": "No items available for review"},
                               status=status.HTTP_404_NOT_FOUND)
            
            review_item = review_items.first()
            
            # Assign to this reviewer
            review_item.is_assigned = True
            review_item.assigned_to = user
            review_item.assignment_expires_at = timezone.now() + datetime.timedelta(minutes=30)
            review_item.updated_by = user
            review_item.save()
            
            # Start a work session
            session = WorkSession.objects.create(
                user=user,
                session_type='REVIEW',
                start_time=timezone.now(),
                created_by=user,
                updated_by=user
            )
            
            # Get the transcription and chunk
            transcription = review_item.transcription
            chunk = transcription.audio_chunk
            
            # Return the review item, transcription, chunk, and session
            return Response({
                "review_item": ReviewQueueSerializer(review_item).data,
                "transcription": ChunkTranscriptionSerializer(transcription).data,
                "chunk": AudioChunkSerializer(chunk).data,
                "session": WorkSessionSerializer(session).data,
                "file_url": request.build_absolute_uri(f"/shared/{chunk.chunk_file}")
            }, status=status.HTTP_200_OK)

# Complete a review
class CompleteReviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, review_id):
        """Complete a review with approve/reject decision"""
        # Get user
        user = request.user
        
        # Get review item
        try:
            review_item = ReviewQueue.objects.get(unique_id=review_id)
        except ReviewQueue.DoesNotExist:
            return Response({"error": "Review item not found"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Verify assignment
        if review_item.assigned_to != user:
            return Response({"error": "This review is not assigned to you"}, 
                           status=status.HTTP_403_FORBIDDEN)
        
        # Get request data
        action = request.data.get('action')  # 'APPROVED', 'REJECTED', or 'NEEDS_CORRECTION'
        text = request.data.get('text', '')  # Possibly edited text
        feedback = request.data.get('feedback', '')
        session_id = request.data.get('session_id')
        
        if action not in ['APPROVED', 'REJECTED', 'NEEDS_CORRECTION']:
            return Response({"error": "Invalid action. Must be APPROVED, REJECTED, or NEEDS_CORRECTION"}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Get transcription
        transcription = review_item.transcription
        previous_text = transcription.text
        previous_status = transcription.status
        
        with transaction.atomic():
            # Get the new status
            new_status = TranscriptionStatus.objects.get(name=action)
            
            # Update transcription
            transcription.text = text
            transcription.status = new_status
            transcription.reviewer = user
            transcription.updated_by = user
            transcription.save()
            
            # Also update feature_text for compatibility during transition
            chunk = transcription.audio_chunk
            chunk.feature_text = text
            chunk.updated_by = user
            chunk.save(update_fields=['feature_text', 'updated_by'])
            
            # Create revision
            revision = TranscriptionRevision.objects.create(
                transcription=transcription,
                previous_text=previous_text,
                new_text=text,
                previous_status=previous_status,
                new_status=new_status,
                change_reason=feedback,
                created_by=user,
                updated_by=user
            )
            
            # Remove from review queue
            review_item.delete()
            
            # If needs correction, reassign to original transcriber
            if action == 'NEEDS_CORRECTION':
                chunk.assign_to_user(transcription.transcriber)
            
            # Close the work session if provided
            if session_id:
                try:
                    session = WorkSession.objects.get(unique_id=session_id)
                    session.close_session()
                    session.chunks_processed += 1
                    session.save(update_fields=['end_time', 'duration', 'chunks_processed'])
                except WorkSession.DoesNotExist:
                    pass
            
            # Update user stats
            try:
                user_stats = UserStats.objects.get(user=user)
                user_stats.update_counts()
                user_stats.update_quality_metrics()
            except UserStats.DoesNotExist:
                pass
            
            try:
                transcriber_stats = UserStats.objects.get(user=transcription.transcriber)
                transcriber_stats.update_counts()
                transcriber_stats.update_quality_metrics()
            except UserStats.DoesNotExist:
                pass
            
            return Response({
                "transcription": ChunkTranscriptionSerializer(transcription).data,
                "revision": TranscriptionRevisionSerializer(revision).data,
                "action": action
            }, status=status.HTTP_200_OK)