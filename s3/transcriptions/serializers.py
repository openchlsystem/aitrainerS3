from rest_framework import serializers
from .models import (
    AudioFile, cleaned_audio_file, CaseRecord, evaluation_record, AudioFileChunk, evaluation_results
)

class AudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFile
        fields = '__all__'

class CleanedAudioFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = cleaned_audio_file
        fields = '__all__'

class CaseRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseRecord
        fields = '__all__'

class EvaluationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = evaluation_record
        fields = '__all__'

class AudioFileChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AudioFileChunk
        fields = '__all__'

class EvaluationResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = evaluation_results
        fields = '__all__'
