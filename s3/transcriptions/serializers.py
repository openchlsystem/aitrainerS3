from rest_framework import serializers
from .models import (
    AudioFile, cleaned_audio_file, CaseRecord, evaluation_record, AudioFileChunk, evaluation_results
)
from django.db.models import Count, Sum, IntegerField, F, ExpressionWrapper, FloatField


class AudioFileSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')  # Read-only
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')  # Read-only

    class Meta:
        model = AudioFile
        fields = '__all__'

class CleanedAudioFileSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')  # Read-only
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')  # Read-only

    class Meta:
        model = cleaned_audio_file
        fields = '__all__'

class CaseRecordSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')  # Read-only
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')  # Read-only

    class Meta:
        model = CaseRecord
        fields = '__all__'

class EvaluationRecordSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')  # Read-only
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')  # Read-only

    class Meta:
        model = evaluation_record
        fields = '__all__'

class AudioFileChunkSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')  # Read-only
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')  # Read-only

    class Meta:
        model = AudioFileChunk
        fields = '__all__'

class EvaluationResultsSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')  # Read-only
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')  # Read-only

    class Meta:
        model = evaluation_results
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'evaluation_date'] #read only fields.

from django.db.models import Count, Sum, IntegerField
from rest_framework import serializers, generics
from .models import evaluation_results, AudioFileChunk

class EvaluationResultsSummarySerializer(serializers.Serializer):
    audiofilechunk = serializers.UUIDField()
    dual_speaker_count = serializers.IntegerField()
    speaker_overlap_count = serializers.IntegerField()
    background_noise_count = serializers.IntegerField()
    prolonged_silence_count = serializers.IntegerField()
    not_normal_speech_rate_count = serializers.IntegerField()
    echo_noise_count = serializers.IntegerField()
    incomplete_sentence_count = serializers.IntegerField()
    total_boolean_sum = serializers.IntegerField()
    evaluation_count = serializers.IntegerField()
    score = serializers.FloatField()

    @classmethod
    def get_queryset(cls):
        total_choices = 7  # Number of boolean fields
        return evaluation_results.objects.values('audiofilechunk').annotate(
            evaluation_count=Count('unique_id'),
            dual_speaker_count=Sum('dual_speaker', output_field=IntegerField()),
            speaker_overlap_count=Sum('speaker_overlap', output_field=IntegerField()),
            background_noise_count=Sum('background_noise', output_field=IntegerField()),
            prolonged_silence_count=Sum('prolonged_silence', output_field=IntegerField()),
            not_normal_speech_rate_count=Sum('not_normal_speech_rate', output_field=IntegerField()),
            echo_noise_count=Sum('echo_noise', output_field=IntegerField()),
            incomplete_sentence_count=Sum('incomplete_sentence', output_field=IntegerField()),
            total_boolean_sum=ExpressionWrapper(
                Sum('dual_speaker', output_field=IntegerField()) +
                Sum('speaker_overlap', output_field=IntegerField()) +
                Sum('background_noise', output_field=IntegerField()) +
                Sum('prolonged_silence', output_field=IntegerField()) +
                Sum('not_normal_speech_rate', output_field=IntegerField()) +
                Sum('echo_noise', output_field=IntegerField()) +
                Sum('incomplete_sentence', output_field=IntegerField()),
                output_field=IntegerField()
            ),
            score=ExpressionWrapper(
                (
                    Sum('dual_speaker', output_field=IntegerField()) +
                    Sum('speaker_overlap', output_field=IntegerField()) +
                    Sum('background_noise', output_field=IntegerField()) +
                    Sum('prolonged_silence', output_field=IntegerField()) +
                    Sum('not_normal_speech_rate', output_field=IntegerField()) +
                    Sum('echo_noise', output_field=IntegerField()) +
                    Sum('incomplete_sentence', output_field=IntegerField())
                ) / (Count('unique_id') * total_choices),
                output_field=FloatField()
            )
        )
    
# New Serializer to categorize chunks based on evaluation count
class EvaluationChunkCategorySerializer(serializers.Serializer):
    not_evaluated = serializers.ListField(child=serializers.UUIDField())
    one_evaluation = serializers.ListField(child=serializers.UUIDField())
    two_evaluations = serializers.ListField(child=serializers.UUIDField())


class ChunkStatisticsSerializer(serializers.Serializer):
    total_chunks = serializers.IntegerField()
    not_evaluated = serializers.IntegerField()
    one_evaluation = serializers.IntegerField()
    two_evaluations = serializers.IntegerField()
    three_or_more_evaluations = serializers.IntegerField()
    ready_for_transcription = serializers.IntegerField()
    evaluation_completion_rate = serializers.FloatField()
    transcribed_chunks = serializers.IntegerField()  # New statistic


class EvaluationCategoryStatisticsSerializer(serializers.Serializer):
    dual_speaker_count = serializers.IntegerField()
    speaker_overlap_count = serializers.IntegerField()
    background_noise_count = serializers.IntegerField()
    prolonged_silence_count = serializers.IntegerField()
    not_normal_speech_rate_count = serializers.IntegerField()
    echo_noise_count = serializers.IntegerField()
    incomplete_sentence_count = serializers.IntegerField()
    total_evaluated_chunks = serializers.IntegerField()