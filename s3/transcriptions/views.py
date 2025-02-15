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
class CleanedAudioFileListCreateView(generics.ListCreateAPIView):
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer
    # permission_classes = [permissevaluated-audioions.IsAuthenticated]


class CleanedAudioFileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer
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


# ✅ AudioFileChunk Views
class AudioFileChunkListCreateView(generics.ListCreateAPIView):
    queryset = AudioFileChunk.objects.all()
    serializer_class = AudioFileChunkSerializer
    # permission_classes = [permissions.IsAuthenticated]


class AudioFileChunkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AudioFileChunk.objects.all()
    serializer_class = AudioFileChunkSerializer
    permission_classes = [permissions.IsAuthenticated]


# ✅ EvaluationResults Views
class EvaluationResultsListCreateView(generics.ListCreateAPIView):
    queryset = evaluation_results.objects.all()
    serializer_class = EvaluationResultsSerializer
    # permission_classes = [permissions.IsAuthenticated]


class EvaluationResultsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = evaluation_results.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]


class CleanedAudioFileViewSet(viewsets.ModelViewSet):
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer

    @action(detail=True, methods=["patch"])
    def toggle_evaluated(self, request, pk=None):
        cleaned_audio = self.get_object()
        cleaned_audio.is_evaluated = not cleaned_audio.is_evaluated
        cleaned_audio.save()
        return Response(
            {"status": "updated", "is_evaluated": cleaned_audio.is_evaluated}
        )


@csrf_exempt
def evaluate_chunk(request, chunk_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    chunk = get_object_or_404(AudioFileChunk, id=chunk_id)
    # user = request.user  # Get current logged-in user
    user = "Unknown"  # Get current logged-in user

    # Parse the request data depending on the content type
    if request.content_type == "application/json":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        data = request.POST

    # Convert values to booleans (assuming values are strings in JSON)
    single_speaker = str(data.get("single_speaker", "false")).lower() == "true"
    speaker_overlap = str(data.get("speaker_overlap", "false")).lower() == "true"
    background_noise = str(data.get("background_noise", "false")).lower() == "true"
    prolonged_silence = str(data.get("prolonged_silence", "false")).lower() == "true"
    not_speech_rate = str(data.get("not_speech_rate", "false")).lower() == "true"
    echo_noise = str(data.get("echo_noise", "false")).lower() == "true"
    # is_evaluated = str(data.get('is_evaluated', 'false')).lower() == 'true'
    evaluation_notes = data.get("evaluation_notes", "")

    evaluation, created = evaluation_results.objects.update_or_create(
        audiofilechunk=chunk,
        is_evaluated_by=user,
        is_evaluated=True,
        defaults={
            "single_speaker": single_speaker,
            "speaker_overlap": speaker_overlap,
            "background_noise": background_noise,
            "prolonged_silence": prolonged_silence,
            "not_speech_rate": not_speech_rate,
            "echo_noise": echo_noise,
            # 'is_evaluated': is_evaluated,
            "evaluation_notes": evaluation_notes,
            "evaluation_date": now(),
        },
    )

    # To be removed when checking for score by users
    chunk.is_evaluated = True
    chunk.save()

    if created:
        chunk.evaluation_count += 1  # ✅ Increment evaluation count
        chunk.save()

    return JsonResponse(
        {
            "message": "Evaluation saved successfully",
            "evaluation_id": evaluation.id,
            "created": created,
        }
    )


@csrf_exempt
def chunk_statistics(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Total number of chunks
    total_chunks = AudioFileChunk.objects.count()

    # Total number of evaluated chunks
    total_evaluated_chunks = AudioFileChunk.objects.filter(is_evaluated=True).count()
    total_unevaluated_chunks = total_chunks - total_evaluated_chunks

    # Return the statistics as JSON
    statistics = {
        "total_chunks": total_chunks,
        "total_evaluated_chunks": total_evaluated_chunks,
        "total_unevaluated_chunks": total_unevaluated_chunks,
    }
    return JsonResponse(statistics)
