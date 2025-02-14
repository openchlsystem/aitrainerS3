from rest_framework import generics, permissions, viewsets, status
from .models import (
    AudioFile, cleaned_audio_file, CaseRecord, evaluation_record, 
    AudioFileChunk, evaluation_results
)
from .serializers import (
    AudioFileSerializer, CleanedAudioFileSerializer, CaseRecordSerializer,
    EvaluationRecordSerializer, AudioFileChunkSerializer, EvaluationResultsSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response


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
    permission_classes = [permissions.IsAuthenticated]

class AudioFileChunkDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AudioFileChunk.objects.all()
    serializer_class = AudioFileChunkSerializer
    permission_classes = [permissions.IsAuthenticated]


# ✅ EvaluationResults Views
class EvaluationResultsListCreateView(generics.ListCreateAPIView):
    queryset = evaluation_results.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]

class EvaluationResultsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = evaluation_results.objects.all()
    serializer_class = EvaluationResultsSerializer
    permission_classes = [permissions.IsAuthenticated]


class CleanedAudioFileViewSet(viewsets.ModelViewSet):
    queryset = cleaned_audio_file.objects.all()
    serializer_class = CleanedAudioFileSerializer

    @action(detail=True, methods=['patch'])
    def toggle_evaluated(self, request, pk=None):
        cleaned_audio = self.get_object()
        cleaned_audio.is_evaluated = not cleaned_audio.is_evaluated
        cleaned_audio.save()
        return Response({"status": "updated", "is_evaluated": cleaned_audio.is_evaluated})
