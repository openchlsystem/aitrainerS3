from django.db import models
import uuid
from django.conf import settings
import os


class BaseModel(models.Model):
    unique_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Correctly reference the user model
        related_name="created_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Correctly reference the user model
        related_name="updated_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
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


# Original audio files
class AudioFile(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="audio_files",
    )
    audio_id = models.CharField(max_length=50, unique=False)
    # Store relative path to the NFS shared folder
    audio_file = models.FileField(upload_to='raw/')
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return self.audio_id
    
    @property
    def full_path(self):
        """Return the full path on the S3 server"""
        return os.path.join('shared', self.audio_file.name)
    
    @property
    def gpu_path(self):
        """Return the full path on the GPU server"""
        # Path for GPU server uses a different mount point (/mnt/shared)
        return os.path.join('/mnt/shared', self.audio_file.name)


# Preprocessed/cleaned audio files
class ProcessedAudioFile(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="processed_audio_files",
    )
    # Store relative path to the NFS shared folder
    processed_file = models.FileField(upload_to='processed/')
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)
    is_approved = models.BooleanField(default=False)
    is_disapproved = models.BooleanField(default=False)
    
    @property
    def full_path(self):
        """Return the full path on the S3 server"""
        return os.path.join('shared', self.processed_file.name)
    
    @property
    def gpu_path(self):
        """Return the full path on the GPU server"""
        # Path for GPU server uses a different mount point (/mnt/shared)
        return os.path.join('/mnt/shared', self.processed_file.name)

class CaseRecord(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="case_records",
    )
    audio_id = models.OneToOneField(
        AudioFile,
        on_delete=models.CASCADE,
        related_name="case_record",
        null=True,
        unique=True,
    )
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
    
# Diarized audio files and their metadata
class DiarizedAudioFile(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="diarized_audio_files",
    )
    # Store relative path to the NFS shared folder
    diarized_file = models.FileField(upload_to='diarized/', max_length=500)
    # Store the path to the diarization results JSON
    diarization_result_json_path = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)
    
    @property
    def full_path(self):
        """Return the full path on the S3 server"""
        return os.path.join('shared', self.diarized_file.name)
    
    @property
    def diarization_json_full_path(self):
        """Return the full path to the diarization JSON on the S3 server"""
        return os.path.join('shared', self.diarization_result_json_path)
    
    @property
    def gpu_path(self):
        """Return the full path on the GPU server"""
        # Path for GPU server uses a different mount point (/mnt/shared)
        return os.path.join('/mnt/shared', self.diarized_file.name)
    
    @property
    def diarization_json_gpu_path(self):
        """Return the full path to the diarization JSON on the GPU server"""
        return os.path.join('/mnt/shared', self.diarization_result_json_path)


# Audio chunks without direct foreign key relationships to promote anonymity
class AudioChunk(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="audio_chunks",
    )
    chunk_file = models.FileField(upload_to='chunks/', max_length=500)
    
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("not_sure", "Not Sure"),
    ]
    LOCALE_CHOICES = [
        ("EN", "English"),
        ("SW", "Swahili"),
        ("KI", "Kikuyu"),
        ("LU", "Luo"),
        ("LH", "Luhya"),
        ("KA", "Kalenjin"),
        ("KB", "Kamba"),
        ("ME", "Meru"),
        ("MA", "Maasai"),
        ("SO", "Somali"),
        ("CH", "Chaga"),
        ("SU", "Sukuma"),
        ("HA", "Haya"),
        ("NY", "Nyamwezi"),
        ("MK", "Makonde"),
        ("ZA", "Zanaki"),
        ("HE", "Hehe"),
        ("LG", "Luganda"),
        ("RN", "Runyankore"),
        ("RK", "Rukiga"),
        ("AC", "Acholi"),
        ("LA", "Langi"),
        ("LS", "Lusoga"),
        ("AL", "Alur"),
        ("RR", "Runyoro-Rutooro"),
    ]

    duration = models.FloatField(null=True)
    feature_text = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="not_sure")
    locale = models.CharField(max_length=5, choices=LOCALE_CHOICES, default="EN")
    
    @property
    def full_path(self):
        """Return the full path on the S3 server"""
        return os.path.join('shared', self.chunk_file)
    
    @property
    def gpu_path(self):
        """Return the full path on the GPU server"""
        # Path for GPU server uses a different mount point (/mnt/shared)
        return os.path.join('/mnt/shared', self.chunk_file)

class EvaluationResults(BaseModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="evaluation_results",
    )
    audiofilechunk = models.ForeignKey(
        AudioChunk, on_delete=models.CASCADE, related_name="evaluation_results"
    )
    not_clear = models.BooleanField(default=False)
    speaker_overlap = models.BooleanField(default=False)
    background_noise = models.BooleanField(default=False)
    silence = models.BooleanField(default=False)
    incomplete_word = models.BooleanField(default=False)
    evaluation_start = models.DateTimeField(null=True)
    evaluation_end = models.DateTimeField(null=True)
    evaluation_duration = models.TimeField(null=True)
    evaluation_notes = models.TextField(null=True)

    class Meta:
        unique_together = ("audiofilechunk", "created_by")

# Asynchronous task tracking
# class ProcessingTask(BaseModel):
#     project = models.ForeignKey(
#         Project,
#         on_delete=models.CASCADE,
#         related_name="processing_tasks",
#     )
#     TASK_TYPES = [
#         ('PREPROCESS', 'Audio Preprocessing'),
#         ('DIARIZE', 'Speaker Diarization'),
#         ('CHUNK', 'Audio Chunking'),
#     ]
    
#     STATUS_CHOICES = [
#         ('PENDING', 'Pending'),
#         ('PROCESSING', 'Processing'),
#         ('COMPLETED', 'Completed'),
#         ('FAILED', 'Failed'),
#     ]
    
#     # Store the audio_id as a string reference without direct FK relationship
#     audio_id = models.CharField(max_length=50)
#     task_type = models.CharField(max_length=20, choices=TASK_TYPES)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
#     error_message = models.TextField(null=True, blank=True)
#     result_path = models.CharField(max_length=255, null=True, blank=True)
    
#     # Add timestamps for tracking task progress
#     started_at = models.DateTimeField(null=True, blank=True)
#     completed_at = models.DateTimeField(null=True, blank=True)