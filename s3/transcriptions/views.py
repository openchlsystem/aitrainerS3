import json
from rest_framework import generics, permissions, viewsets, status
from .models import (
    AudioFile,
    cleaned_audio_file,
    CaseRecord,
    evaluation_record,
    AudioFileChunk,
    evaluation_results,
)
from .serializers import (
    AudioFileSerializer,
    CleanedAudioFileSerializer,
    CaseRecordSerializer,
    EvaluationRecordSerializer,
    AudioFileChunkSerializer,
    EvaluationResultsSerializer,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt


# ✅ AudioFile Views
class AudioFileListCreateView(generics.ListCreateAPIView):
    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AudioFileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AudioFile.objects.all()
    serializer_class = AudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]


# ✅ EvaluatedAudioFile Views
# class CleanedAudioFileListCreateView(generics.ListCreateAPIView):
#     queryset = cleaned_audio_file.objects.all()
#     serializer_class = CleanedAudioFileSerializer
#     # permission_classes = [permissevaluated-audioions.IsAuthenticated]


# class CleanedAudioFileDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = cleaned_audio_file.objects.all()
#     serializer_class = CleanedAudioFileSerializer
    # permission_classes = [permissions.IsAuthenticated]


# ✅ CaseRecord Views
class CaseRecordListCreateView(generics.ListCreateAPIView):
    queryset = CaseRecord.objects.all()
    serializer_class = CaseRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


class CaseRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = CaseRecord.objects.all()
    serializer_class = CaseRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


# ✅ EvaluationRecord Views
class EvaluationRecordListCreateView(generics.ListCreateAPIView):
    queryset = evaluation_record.objects.all()
    serializer_class = EvaluationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


class EvaluationRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = evaluation_record.objects.all()
    serializer_class = EvaluationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


# # ✅ AudioFileChunk Views
# class AudioFileChunkListCreateView(generics.ListCreateAPIView):
#     queryset = AudioFileChunk.objects.all()
#     serializer_class = AudioFileChunkSerializer
#     # permission_classes = [permissions.IsAuthenticated]


# class AudioFileChunkDetailView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = AudioFileChunk.objects.all()
#     serializer_class = AudioFileChunkSerializer
#     permission_classes = [permissions.IsAuthenticated]


# ✅ EvaluationResults Views
class EvaluationResultsListCreateView(generics.ListCreateAPIView):
    queryset = evaluation_results.objects.all()
    serializer_class = EvaluationResultsSerializer
    # permission_classes = [permissions.IsAuthenticated]


class EvaluationResultsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = evaluation_results.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]

# CleanedAudioFile Views
class CleanedAudioFileListCreateView(generics.ListCreateAPIView):
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()  # Start with the default queryset

        pending_filter = self.request.query_params.get('pending', None)
        if pending_filter == 'true':
            queryset = queryset.filter(is_approved=False, is_disapproved=False)

        return queryset

    def perform_create(self, serializer): #add user when creating
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

class CleanedAudioFileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer): #add user when updating
        serializer.save(updated_by=self.request.user)

class CleanedAudioFileToggleApprovedView(generics.UpdateAPIView): #for toggle approve
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']

    def patch(self, request, *args, **kwargs):
        cleaned_audio = self.get_object()
        cleaned_audio.is_approved = not cleaned_audio.is_approved
        cleaned_audio.updated_by = request.user
        cleaned_audio.save()
        return Response(
            {"status": "updated", "is_approved": cleaned_audio.is_approved}, status=status.HTTP_200_OK
        )

class CleanedAudioFileToggleDisapprovedView(generics.UpdateAPIView): #for toggle disapprove
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['patch']

    def patch(self, request, *args, **kwargs):
        cleaned_audio = self.get_object()
        cleaned_audio.is_disapproved = not cleaned_audio.is_disapproved
        cleaned_audio.updated_by = request.user
        cleaned_audio.save()
        return Response(
            {"status": "updated", "is_disapproved": cleaned_audio.is_disapproved}, status=status.HTTP_200_OK
        )


# AudioFileChunk Views
class AudioFileChunkListCreateView(generics.ListCreateAPIView):
    queryset = AudioFileChunk.objects.all()
    serializer_class = AudioFileChunkSerializer
    permission_classes = [permissions.IsAuthenticated]

class AudioFileChunkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AudioFileChunk.objects.all()
    serializer_class = AudioFileChunkSerializer
    permission_classes = [permissions.IsAuthenticated]

class AudioFileChunkEvaluateView(generics.GenericAPIView): #for evaluate
    queryset = AudioFileChunk.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        chunk = self.get_object()
        user = request.user
        data = request.data

        dual_speaker = str(data.get("dual_speaker", "false")).lower() == "true"
        speaker_overlap = str(data.get("speaker_overlap", "false")).lower() == "true"
        background_noise = str(data.get("background_noise", "false")).lower() == "true"
        prolonged_silence = str(data.get("prolonged_silence", "false")).lower() == "true"
        not_normal_speech_rate = str(data.get("not_normal_speech_rate", "false")).lower() == "true"
        echo_noise = str(data.get("echo_noise", "false")).lower() == "true"
        incomplete_sentence = str(data.get("incomplete_sentence", "false")).lower() == "true"
        evaluation_notes = data.get("evaluation_notes", "")
        evaluation_start = data.get("evaluation_start")
        evaluation_end = data.get("evaluation_end")
        evaluation_duration = data.get("evaluation_duration")

        evaluation, created = evaluation_results.objects.update_or_create(
            audiofilechunk=chunk,
            created_by=user,
            defaults={
                "dual_speaker": dual_speaker,
                "speaker_overlap": speaker_overlap,
                "background_noise": background_noise,
                "prolonged_silence": prolonged_silence,
                "not_normal_speech_rate": not_normal_speech_rate,
                "echo_noise": echo_noise,
                "incomplete_sentence": incomplete_sentence,
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

        chunk.is_evaluated = True #to be removed when counting to 3
        chunk.evaluation_count += 1
        chunk.save()

        serializer = EvaluationResultsSerializer(evaluation)

        return Response(
            {
                "message": "Evaluation saved successfully",
                "evaluation": serializer.data,
                "created": created,
            },
            status=status.HTTP_200_OK,
        )

class AudioFileChunkStatisticsView(generics.GenericAPIView): #for statistics
    queryset = AudioFileChunk.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        total_chunks = AudioFileChunk.objects.count()
        total_evaluated_chunks = AudioFileChunk.objects.filter(is_evaluated=True).count()
        total_unevaluated_chunks = total_chunks - total_evaluated_chunks

        statistics = {
            "total_chunks": total_chunks,
            "total_evaluated_chunks": total_evaluated_chunks,
            "total_unevaluated_chunks": total_unevaluated_chunks,
        }
        return Response(statistics, status=status.HTTP_200_OK)

# Batch audio file input 

import os
import logging
import json
import subprocess
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files import File
from .models import AudioFile
from pydub.utils import mediainfo  # Faster metadata extraction
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

@csrf_exempt
def process_audio_folder(request):
    if request.method == "POST":
        try:
            files = request.FILES.getlist("files")  # Handle file uploads

            if not files:
                return JsonResponse({"error": "No files provided."}, status=400)

            processed_files = process_audio_files_from_uploaded(files)  # Process uploaded files
            return JsonResponse({"message": f"Processed {processed_files} audio files."})

        except Exception as e:
            print(f"❌ Error processing files: {e}")
            return JsonResponse({"error": "Failed to process files."}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)

def process_audio_files_from_uploaded(files):
    """Processes uploaded audio files directly."""
    processed_count = 0

    for file in files:
        filename = file.name
        print(f"📂 Processing uploaded file: {filename}")

        if filename.endswith((".ogg", ".wav")):  # Check if file is Ogg or WAV
            try:
                # ✅ Save the file temporarily
                temp_path = default_storage.save(f"temp/{filename}", ContentFile(file.read()))

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
                    defaults={"duration": duration, "file_size": file_size}
                )

                if not created:
                    updated = False
                    if audio_file_instance.duration is None:
                        audio_file_instance.duration = duration
                        updated = True
                    if audio_file_instance.file_size is None:
                        audio_file_instance.file_size = file_size
                        updated = True
                    if updated:
                        audio_file_instance.save()

                # ✅ Save file in Django FileField
                if not audio_file_instance.audio_file:
                    with open(temp_path, "rb") as f:
                        audio_file_instance.audio_file.save(filename, File(f), save=True)

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
            stderr=subprocess.PIPE
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
            ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", 
             "-of", "json", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        metadata = json.loads(result.stdout)
        duration = float(metadata["format"]["duration"])
        file_size = int(metadata["format"]["size"])
        return duration, file_size
    except Exception as e:
        print(f"❌ Error extracting metadata for {filepath}: {e}")
        return None, None



# leader board 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EvaluationResultsSummarySerializer

class LeaderboardView(APIView):
    def get(self, request, *args, **kwargs):
        leaderboard_data = EvaluationResultsSummarySerializer.get_leaderboard()
        serializer = EvaluationResultsSummarySerializer(leaderboard_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

