import json
import os
import logging
import subprocess
from rest_framework import generics, permissions, status, serializers
from .models import (
    Project,
    AudioFile,
    ProcessedAudioFile,
    DiarizedAudioFile,
    CaseRecord,
    AudioChunk,
    EvaluationResults,
)
from .serializers import (
    AudioFileSerializer,
    ChunkStatisticsSerializer,
    ProcessedAudioFileSerializer,
    DiarizedAudioFileSerializer,
    CaseRecordSerializer,
    EvaluationCategoryStatisticsSerializer,
    EvaluationChunkCategorySerializer,
    AudioChunkSerializer,
    EvaluationResultsSerializer,
    EvaluationResultsLeaderBoardSerializer,
    EvaluationResultsSummarySerializer,
    ProjectSerializer
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

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
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
        two_evaluations_chunks = list(chunks.filter(evaluation_count=2).values())

        # Helper function to build full URL
        def get_full_url(chunk):
            chunk_obj = AudioChunk.objects.get(unique_id=chunk['unique_id'])
            return request.build_absolute_uri(f"/shared/{chunk_obj.chunk_file}")

        # Collect unique_ids for categorized chunks (excluding not_evaluated)
        evaluated_chunk_ids = [chunk["unique_id"] for chunk in one_evaluation_chunks + two_evaluations_chunks]

        # Fetch evaluations done by the current user for those chunks
        user_evaluations = EvaluationResults.objects.filter(
            audiofilechunk__in=evaluated_chunk_ids, created_by=user
        ).values_list("audiofilechunk", flat=True)

        # Convert to a set for fast lookup
        user_evaluated_set = set(user_evaluations)

        # Append evaluated_by_user boolean to the required categories
        for chunk in one_evaluation_chunks + two_evaluations_chunks:
            chunk["evaluated_by_user"] = chunk["unique_id"] in user_evaluated_set
        
        # Append full URL for chunk_file
        for chunk in not_evaluated_chunks:
            chunk['file_url'] = get_full_url(chunk)

        for chunk in one_evaluation_chunks:
            chunk['file_url'] = get_full_url(chunk)

        for chunk in two_evaluations_chunks:
            chunk['file_url'] = get_full_url(chunk)

        return Response({
            "not_evaluated": not_evaluated_chunks,
            "one_evaluation": one_evaluation_chunks,
            "two_evaluations": two_evaluations_chunks,
        })

# Chunks for Transcription View
class ChunksForTranscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Get project_id from request if provided
        project_id = request.query_params.get('project_id')
        base_queryset = AudioChunk.objects.all()
        
        if project_id:
            try:
                project = Project.objects.get(unique_id=project_id)
                base_queryset = base_queryset.filter(project=project)
            except Project.DoesNotExist:
                return Response({"error": f"Project with ID {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        total_choices = 6  # Updated to match new evaluation fields count

        # Subquery to count evaluations and calculate score
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
                score=ExpressionWrapper(
                    (
                        Sum("not_clear", output_field=IntegerField())
                        + Sum("speaker_overlap", output_field=IntegerField())
                        + Sum("dual_speaker", output_field=IntegerField())
                        + Sum("interruptive_background_noise", output_field=IntegerField())
                        + Sum("silence", output_field=IntegerField())
                        + Sum("incomplete_word", output_field=IntegerField())
                    )
                    / (Count("unique_id") * total_choices),
                    output_field=FloatField(),
                ),
            )
            .values("evaluation_count", "score")
        )

        # Query chunks and annotate with evaluation count & score
        chunks = base_queryset.annotate(
            evaluation_count=Subquery(evaluation_summary.values("evaluation_count")),
            score=Subquery(evaluation_summary.values("score")),
        )

        # Filter: Chunks with evaluation_count ≥ 3 and score < 0.3
        chunks_for_transcription = chunks.filter(evaluation_count__gte=3, score__lt=0.3)
        
        # Helper function to get full URL
        def get_full_url(chunk):
            return request.build_absolute_uri(f"/media/{chunk.chunk_file}")
        
        # Serialize chunks
        resultingChunks = AudioChunkSerializer(
            chunks_for_transcription, many=True
        ).data
        
        # Append full URL for chunk_file
        for chunk in resultingChunks:
            chunk['file_url'] = get_full_url(AudioChunk.objects.get(unique_id=chunk['unique_id']))

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
        
        total_choices = 6  # Updated to match new evaluation fields count
        
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
                score=ExpressionWrapper(
                    (
                        Sum("not_clear", output_field=IntegerField())
                        + Sum("speaker_overlap", output_field=IntegerField())
                        + Sum("dual_speaker", output_field=IntegerField())
                        + Sum("interruptive_background_noise", output_field=IntegerField())
                        + Sum("silence", output_field=IntegerField())
                        + Sum("incomplete_word", output_field=IntegerField())
                    )
                    / (Count("unique_id") * total_choices),
                    output_field=FloatField(),
                ),
            )
            .values("evaluation_count", "score")
        )
        
        chunks = base_queryset.annotate(
            evaluation_count=Subquery(evaluation_summary.values("evaluation_count")),
            score=Subquery(evaluation_summary.values("score")),
        )
        
        total_chunks = chunks.count()
        not_evaluated = chunks.filter(evaluation_count__isnull=True).count()
        one_evaluation = chunks.filter(evaluation_count=1).count()
        two_evaluations = chunks.filter(evaluation_count=2).count()
        three_or_more_evaluations = chunks.filter(evaluation_count__gte=3).count()
        ready_for_transcription = chunks.filter(
            evaluation_count__gte=3, score__lt=0.3
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