from rest_framework import serializers
from .models import (
    AudioFile, cleaned_audio_file, CaseRecord, evaluation_record, AudioFileChunk, evaluation_results
)

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



from django.db.models import Count

from rest_framework import serializers
from .models import evaluation_results  # Adjust based on your actual import

class EvaluationResultsSummarySerializer(serializers.Serializer):
    created_by_username = serializers.CharField(source='created_by__first_name')
    evaluations_done = serializers.IntegerField()

    @staticmethod
    def get_leaderboard():
        # Aggregate the number of evaluations done by each user (grouped by 'created_by')
        result = evaluation_results.objects.select_related('created_by').values('created_by__first_name').annotate(evaluations_done=Count('unique_id'))
        
        return result


