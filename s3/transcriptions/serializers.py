from rest_framework import serializers
from .models import (
    AudioFile, ProcessedAudioFile, CaseRecord, DiarizedAudioFile, 
    AudioChunk, EvaluationResults, ProcessingTask, Project
)
from django.db.models import Count, Sum, IntegerField, ExpressionWrapper, FloatField

class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = '__all__'

class AudioFileSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AudioFile
        fields = '__all__'


class FilePathField(serializers.FileField):
    """
    Custom field that accepts either a file upload or a file path as a string.
    """
    def to_internal_value(self, data):
        if isinstance(data, str):
            # It's a path string - return as is
            return data
        # Otherwise use normal file field validation
        return super().to_internal_value(data)


class ProcessedAudioFileSerializer(serializers.ModelSerializer):
    """Serializer for ProcessedAudioFile model"""
    processed_file = FilePathField()
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = ProcessedAudioFile
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DiarizedAudioFileSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DiarizedAudioFile
        fields = '__all__'


class CaseRecordSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CaseRecord
        fields = '__all__'


class AudioChunkSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AudioChunk
        fields = '__all__'
        read_only_fields = ['file_path']  # read only fields


class EvaluationResultsSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = EvaluationResults
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'evaluation_date']


class ProcessingTaskSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.whatsapp_number')
    updated_by = serializers.ReadOnlyField(source='updated_by.whatsapp_number')
    project = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ProcessingTask
        fields = '__all__'


    
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


class EvaluationResultsLeaderBoardSerializer(serializers.Serializer):
    created_by_username = serializers.CharField(source='created_by__first_name')
    evaluations_done = serializers.IntegerField()

    @staticmethod
    def get_leaderboard():
        # Aggregate the number of evaluations done by each user (grouped by 'created_by')
        result = EvaluationResults.objects.select_related('created_by').values('created_by__first_name').annotate(evaluations_done=Count('unique_id'))
        return result
    

class EvaluationResultsSummarySerializer(serializers.Serializer):
    audiofilechunk = serializers.UUIDField()
    not_clear_count = serializers.IntegerField()
    speaker_overlap_count = serializers.IntegerField()
    background_noise_count = serializers.IntegerField()
    silence_count = serializers.IntegerField()
    incomplete_word_count = serializers.IntegerField()
    total_boolean_sum = serializers.IntegerField()
    evaluation_count = serializers.IntegerField()
    score = serializers.FloatField()

    @classmethod
    def get_queryset(cls, project=None):
        total_choices = 5  # Number of boolean fields
        queryset = EvaluationResults.objects.values('audiofilechunk')
    
        # Filter by project if provided
        if project:
            queryset = queryset.filter(project=project)
        
        return queryset.annotate(
            evaluation_count=Count('unique_id'),
            not_clear_count=Sum('not_clear', output_field=IntegerField()),
            speaker_overlap_count=Sum('speaker_overlap', output_field=IntegerField()),
            background_noise_count=Sum('background_noise', output_field=IntegerField()),
            silence_count=Sum('silence', output_field=IntegerField()),
            incomplete_word_count=Sum('incomplete_word', output_field=IntegerField()),
            total_boolean_sum=ExpressionWrapper(
                Sum('not_clear', output_field=IntegerField()) +
                Sum('speaker_overlap', output_field=IntegerField()) +
                Sum('background_noise', output_field=IntegerField()) +
                Sum('silence', output_field=IntegerField()) +
                Sum('incomplete_word', output_field=IntegerField()),
                output_field=IntegerField()
            ),
            score=ExpressionWrapper(
                (
                    Sum('not_clear', output_field=IntegerField()) +
                    Sum('speaker_overlap', output_field=IntegerField()) +
                    Sum('background_noise', output_field=IntegerField()) +
                    Sum('silence', output_field=IntegerField()) +
                    Sum('incomplete_word', output_field=IntegerField())
                ) / (Count('unique_id') * total_choices),
                output_field=FloatField()
            )
        )


class EvaluationCategoryStatisticsSerializer(serializers.Serializer):
    not_clear_count = serializers.IntegerField()
    speaker_overlap_count = serializers.IntegerField()
    background_noise_count = serializers.IntegerField()
    silence_count = serializers.IntegerField()
    incomplete_word_count = serializers.IntegerField()
    total_evaluated_chunks = serializers.IntegerField()