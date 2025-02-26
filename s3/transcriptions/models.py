from django.db import models
import uuid
from django.conf import settings

class BaseModel(models.Model):
    unique_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Correctly reference the user model
        related_name="created_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Correctly reference the user model
        related_name="updated_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=False
    )    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Project(BaseModel):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

# Audio file must be downloaded prior
class AudioFile(BaseModel):
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="audio_files")
    audio_id = models.CharField(max_length=50, unique=True)
    audio_file = models.FileField(upload_to="audios/")
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)
    is_cleaned = models.BooleanField(default=False)
    
    def __str__(self):
        return self.audio_id

# confirm audio files are usable example long silence , volume , within selected specttogram
class CleanedAudioFile(BaseModel):
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="cleaned_audio_files")
    audio_file = models.FileField(upload_to="cleaned-audio/")
    is_approved = models.BooleanField(default=False)
    is_disapproved = models.BooleanField(default=False)
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)

class CaseRecord(BaseModel):
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="case_records")
    audio_id = models.OneToOneField(AudioFile, on_delete=models.CASCADE, related_name="case_record", null=True, unique=True)
    date = models.DateTimeField()
    talk_time = models.TimeField()
    case_id = models.CharField(max_length=20)
    narrative = models.TextField()
    plan = models.TextField()
    main_category = models.CharField(max_length=100)
    sub_category = models.CharField(max_length=100)
    gbv = models.BooleanField()
    
    def __str__(self):
        return f"Case {self.case_id} - {self.main_category}"

# class EvaluationRecord(BaseModel):
#     project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="evaluation_records")
#     audio_id = models.OneToOneField(AudioFile, on_delete=models.CASCADE, related_name="evaluation_record", null=True, unique=True)
#     date = models.DateTimeField()
#     talk_time = models.TimeField()
#     case_id = models.CharField(max_length=20)
#     narrative = models.TextField()
#     plan = models.TextField()
#     main_category = models.CharField(max_length=100)
#     sub_category = models.CharField(max_length=100)
#     gbv = models.BooleanField()
#     true_transcription = models.TextField()
#     true_transcription_locale = models.CharField(max_length=50)

class AudioFileChunk(BaseModel):
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="audio_chunks")
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("not_sure", "Not Sure"),
    ]
    LOCALE_CHOICES = [
        ("en", "English"),
        ("sw", "Swahili"),
        ("both", "Both"),
    ]
    chunk_file = models.FileField(upload_to="audio-chunks/")
    duration = models.FloatField(null=True)
    feature_text = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="not_sure")
    locale = models.CharField(max_length=5, choices=LOCALE_CHOICES, default="sw")

class EvaluationResults(BaseModel):
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="evaluation_results")
    audiofilechunk = models.ForeignKey(AudioFileChunk, on_delete=models.CASCADE, related_name="evaluation_results")
    dual_speaker = models.BooleanField(default=False)
    speaker_overlap = models.BooleanField(default=False)
    background_noise = models.BooleanField(default=False)
    prolonged_silence = models.BooleanField(default=False)
    not_normal_speech_rate = models.BooleanField(default=False)
    echo_noise = models.BooleanField(default=False)
    incomplete_sentence = models.BooleanField(default=False)
    evaluation_start = models.DateTimeField(null=True)
    evaluation_end = models.DateTimeField(null=True)
    evaluation_duration = models.TimeField(null=True)
    evaluation_notes = models.TextField(null=True)

    class Meta:
        unique_together = ('audiofilechunk', 'created_by')
