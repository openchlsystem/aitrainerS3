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
    ProcessingTask
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
    ProcessingTaskSerializer,
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
        
        # Filter by is_diarized if provided
        is_diarized = self.request.query_params.get('is_diarized')
        if is_diarized is not None:
            is_diarized_bool = is_diarized.lower() == 'true'
            queryset = queryset.filter(is_diarized=is_diarized_bool)
        
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
                    is_diarized=self.request.data.get('is_diarized', False),
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
        # Ensure a project is provided
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({"project": "Project is required"})
        
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

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
        # Ensure a project is provided
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({"project": "Project is required"})
        
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

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
class ProcessingTaskListCreateView(BaseListCreateView):
    queryset = ProcessingTask.objects.all()
    serializer_class = ProcessingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by project
        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project__unique_id=project_id)
            
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # Filter by task type
        task_type = self.request.query_params.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
            
        # Filter by audio ID
        audio_id = self.request.query_params.get('audio_id')
        if audio_id:
            queryset = queryset.filter(audio_id=audio_id)
            
        return queryset.order_by('-created_at')

    def perform_create(self, serializer):
        # Ensure a project is provided
        project_id = self.request.data.get('project')
        if not project_id:
            raise serializers.ValidationError({"project": "Project is required"})
        
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class ProcessingTaskDetailView(BaseRetrieveUpdateDestroyView):
    queryset = ProcessingTask.objects.all()
    serializer_class = ProcessingTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

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
        background_noise = str(data.get("background_noise", "false")).lower() == "true"
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
                "background_noise": background_noise,
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

# Audio File Processing
@csrf_exempt
def process_audio_folder(request):
    if request.method == "POST":
        try:
            files = request.FILES.getlist("files")  # Handle file uploads
            project_id = request.POST.get("project_id")  # Get project ID

            if not files:
                return JsonResponse({"error": "No files provided."}, status=400)

            if not project_id:
                return JsonResponse({"error": "Project ID is required."}, status=400)

            try:
                project = Project.objects.get(unique_id=project_id)
            except Project.DoesNotExist:
                return JsonResponse({"error": f"Project with ID {project_id} not found."}, status=404)

            # Pass project to processing function
            processed_files = process_audio_files_from_uploaded(files, project, request.user)
            return JsonResponse(
                {"message": f"Processed {processed_files} audio files."}
            )

        except Exception as e:
            print(f"❌ Error processing files: {e}")
            return JsonResponse({"error": f"Failed to process files: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


def process_audio_files_from_uploaded(files, project, user):
    """Processes uploaded audio files directly."""
    processed_count = 0

    for file in files:
        filename = file.name
        print(f"📂 Processing uploaded file: {filename}")

        if filename.endswith((".ogg", ".wav")):  # Check if file is Ogg or WAV
            try:
                # ✅ Save the file temporarily
                temp_path = default_storage.save(
                    f"temp/{filename}", ContentFile(file.read())
                )

                # Convert Ogg to WAV if the file is Ogg Vorbis
                if filename.endswith(".ogg"):
                    wav_filename = filename.replace(".ogg", ".wav")
                    wav_temp_path = convert_ogg_to_wav(temp_path, wav_filename)
                    if not wav_temp_path:
                        print(f"⚠️ Skipping {filename} due to conversion failure.")
                        continue
                    temp_path = wav_temp_path  # Use the new WAV file for further processing
                    filename = wav_filename  # Update the filename to .wav

                # ✅ Extract metadata
                duration, file_size = get_audio_metadata(temp_path)

                if duration is None or file_size is None:
                    print(f"⚠️ Skipping {filename} due to metadata extraction failure.")
                    continue

                # ✅ Save file to database
                audio_id = os.path.splitext(filename)[0]
                audio_file_instance, created = AudioFile.objects.get_or_create(
                    audio_id=audio_id,
                    defaults={
                        "project": project,  # Set the project
                        "file_path": f"raw/{filename}",  # Store relative path
                        "duration": duration, 
                        "file_size": file_size,
                        "created_by": user,
                        "updated_by": user
                    },
                )

                if not created:
                    updated = False
                    if audio_file_instance.duration is None:
                        audio_file_instance.duration = duration
                        updated = True
                    if audio_file_instance.file_size is None:
                        audio_file_instance.file_size = file_size
                        updated = True
                    if audio_file_instance.project is None:
                        audio_file_instance.project = project
                        updated = True
                    if updated:
                        audio_file_instance.updated_by = user
                        audio_file_instance.save()

                # ✅ Copy file to the shared folder
                destination_path = os.path.join("shared/raw", filename)
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                
                with open(temp_path, "rb") as src_file:
                    with open(destination_path, "wb") as dst_file:
                        dst_file.write(src_file.read())

                processed_count += 1

                # ✅ Delete temp file after processing
                default_storage.delete(temp_path)

            except Exception as e:
                print(f"❌ Error processing file {filename}: {e}")

    return processed_count


def convert_ogg_to_wav(input_path, output_filename):
    """Convert Ogg Vorbis audio to WAV format using ffmpeg."""
    output_path = os.path.join(os.path.dirname(input_path), output_filename)
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_path, output_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print(f"✅ Converted {input_path} to {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        print(f"❌ Error converting {input_path} to WAV: {e}")
        return None


def get_audio_metadata(filepath):
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
        print(f"❌ Error extracting metadata for {filepath}: {e}")
        return None, None


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


class EvaluationChunkCategoryView(APIView):
    serializer_class = EvaluationChunkCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        
        # Filter by project if provided
        project_id = request.query_params.get('project_id')
        base_queryset = AudioChunk.objects.all()
        
        if project_id:
            try:
                project = Project.objects.get(unique_id=project_id)
                base_queryset = base_queryset.filter(project=project)
            except Project.DoesNotExist:
                return Response({"error": f"Project with ID {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)

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
        def get_full_url(chunk):
            chunk_obj = AudioChunk.objects.get(unique_id=chunk['unique_id'])
            return request.build_absolute_uri(f"/media/{chunk_obj.file_path}")
        
        # Append full URL for file_path
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
        
        total_choices = 5  # Updated to match new evaluation fields count

        # Subquery to count evaluations and calculate score
        evaluation_summary = (
            EvaluationResults.objects.filter(audiofilechunk=OuterRef("unique_id"))
            .values("audiofilechunk")
            .annotate(
                evaluation_count=Count("unique_id"),
                total_boolean_sum=Sum("not_clear", output_field=IntegerField())
                + Sum("speaker_overlap", output_field=IntegerField())
                + Sum("background_noise", output_field=IntegerField())
                + Sum("silence", output_field=IntegerField())
                + Sum("incomplete_word", output_field=IntegerField()),
                score=ExpressionWrapper(
                    (
                        Sum("not_clear", output_field=IntegerField())
                        + Sum("speaker_overlap", output_field=IntegerField())
                        + Sum("background_noise", output_field=IntegerField())
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
            return request.build_absolute_uri(f"/media/{chunk.file_path}")
        
        # Serialize chunks
        resultingChunks = AudioChunkSerializer(
            chunks_for_transcription, many=True
        ).data
        
        # Append full URL for file_path
        for chunk in resultingChunks:
            chunk['file_url'] = get_full_url(AudioChunk.objects.get(unique_id=chunk['unique_id']))

        return Response({
            "chunks_for_transcription": resultingChunks
        })


# Chunk Statistics View
class ChunkStatisticsView(APIView):
    serializer_class = ChunkStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Filter by project if provided
        project_id = request.query_params.get('project_id')
        base_queryset = AudioChunk.objects.all()
        
        if project_id:
            try:
                project = Project.objects.get(unique_id=project_id)
                base_queryset = base_queryset.filter(project=project)
            except Project.DoesNotExist:
                return Response({"error": f"Project with ID {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        total_choices = 5  # Updated to match new evaluation fields count

        evaluation_summary = (
            EvaluationResults.objects.filter(audiofilechunk=OuterRef("unique_id"))
            .values("audiofilechunk")
            .annotate(
                evaluation_count=Count("unique_id"),
                total_boolean_sum=Sum("not_clear", output_field=IntegerField())
                + Sum("speaker_overlap", output_field=IntegerField())
                + Sum("background_noise", output_field=IntegerField())
                + Sum("silence", output_field=IntegerField())
                + Sum("incomplete_word", output_field=IntegerField()),
                score=ExpressionWrapper(
                    (
                        Sum("not_clear", output_field=IntegerField())
                        + Sum("speaker_overlap", output_field=IntegerField())
                        + Sum("background_noise", output_field=IntegerField())
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
class EvaluationCategoryStatisticsView(APIView):
    serializer_class = EvaluationCategoryStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Filter by project if provided
        project_id = request.query_params.get('project_id')
        queryset = EvaluationResults.objects.all()
        
        if project_id:
            try:
                project = Project.objects.get(unique_id=project_id)
                queryset = queryset.filter(project=project)
            except Project.DoesNotExist:
                return Response({"error": f"Project with ID {project_id} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        total_evaluations = queryset.count()

        stats = EvaluationResults.objects.aggregate(
            dual_speaker_count=Sum("dual_speaker", output_field=IntegerField()),
            speaker_overlap_count=Sum("speaker_overlap", output_field=IntegerField()),
            background_noise_count=Sum("background_noise", output_field=IntegerField()),
            prolonged_silence_count=Sum(
                "prolonged_silence", output_field=IntegerField()
            ),
            not_normal_speech_rate_count=Sum(
                "not_normal_speech_rate", output_field=IntegerField()
            ),
            echo_noise_count=Sum("echo_noise", output_field=IntegerField()),
            incomplete_sentence_count=Sum(
                "incomplete_sentence", output_field=IntegerField()
            ),
        )

        stats["total_evaluations"] = total_evaluations

        return Response(stats)

class LeaderboardView(APIView):
    def get(self, request, *args, **kwargs):
        leaderboard_data = EvaluationResultsLeaderBoardSerializer.get_leaderboard()
        serializer = EvaluationResultsLeaderBoardSerializer(leaderboard_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AudioFilesBulkUploadView(APIView):
    """
    View to handle bulk audio file uploads from the Vue3 frontend
    Supports folder upload where users select a folder containing audio files
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
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
                        defaults={
                            'project': project,
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