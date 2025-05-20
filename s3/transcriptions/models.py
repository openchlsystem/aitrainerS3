from django.db import models
import uuid
from django.conf import settings
import os
import datetime
from django.utils import timezone


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
    
    # Add workflow type field
    WORKFLOW_CHOICES = (
        ('MANUAL_TRANSCRIPTION', 'Manual Transcription Workflow'),
        ('ASR_CORRECTION', 'ASR Correction Workflow'),
    )
    workflow_type = models.CharField(
        max_length=50,
        choices=WORKFLOW_CHOICES,
        default='MANUAL_TRANSCRIPTION'
    )

    asr_chunk_duration = models.PositiveIntegerField(
        default=30,  # Default 30 seconds
        help_text="Chunk duration in seconds for ASR workflow",
        null=True,
        blank=True  # Make it optional
    )
    
    def __str__(self):
        return f"{self.name} - {self.workflow_type}"


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
    # feature_text field will be removed in final phase
    feature_text = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="not_sure")
    locale = models.CharField(max_length=5, choices=LOCALE_CHOICES, default="EN")
    
    # Add workflow tracking fields
    is_assigned = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_chunks"
    )
    assignment_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Add workflow type reference for behavior
    workflow_type = models.CharField(
        max_length=50,
        choices=Project.WORKFLOW_CHOICES,
        default='MANUAL_TRANSCRIPTION'
    )
    
    @property
    def full_path(self):
        """Return the full path on the S3 server"""
        return os.path.join('shared', self.chunk_file)
    
    @property
    def gpu_path(self):
        """Return the full path on the GPU server"""
        # Path for GPU server uses a different mount point (/mnt/shared)
        return os.path.join('/mnt/shared', self.chunk_file)
        
    def assign_to_user(self, user, expires_in_minutes=30):
        """Assign this chunk to a user with an expiration time"""
        self.is_assigned = True
        self.assigned_to = user
        self.assignment_expires_at = timezone.now() + datetime.timedelta(minutes=expires_in_minutes)
        self.save()
        
    def release_assignment(self):
        """Release assignment if it expired"""
        self.is_assigned = False
        self.assigned_to = None
        self.assignment_expires_at = None
        self.save()


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
    dual_speaker = models.BooleanField(default=False)
    interruptive_background_noise = models.BooleanField(default=False)
    silence = models.BooleanField(default=False)
    incomplete_word = models.BooleanField(default=False)
    evaluation_start = models.DateTimeField(null=True)
    evaluation_end = models.DateTimeField(null=True)
    evaluation_duration = models.TimeField(null=True)
    evaluation_notes = models.TextField(null=True)

    class Meta:
        unique_together = ("audiofilechunk", "created_by")


class TranscriptionActivity(BaseModel):
    audio_chunk = models.ForeignKey(
        AudioChunk, 
        on_delete=models.CASCADE,
        related_name="transcription_activities",
    )
    original_text = models.TextField(blank=True, null=True)
    new_text = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ("audio_chunk", "created_by")
        indexes = [
            models.Index(fields=['created_by', 'created_at']),
        ]
        
    def __str__(self):
        username = self.created_by.username if self.created_by else "Unknown"
        return f"Transcription by {username} on {self.created_at}"


# New models for enhanced workflow

class TranscriptionStatus(models.Model):
    """Defines possible statuses for transcriptions"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Transcription statuses"


class ChunkTranscription(BaseModel):
    """Represents the current state of transcription for an audio chunk"""
    audio_chunk = models.OneToOneField(
        AudioChunk,
        on_delete=models.CASCADE,
        related_name="current_transcription"
    )
    text = models.TextField(blank=True)
    status = models.ForeignKey(
        TranscriptionStatus,
        on_delete=models.PROTECT,
        related_name="transcriptions"
    )
    transcriber = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transcribed_chunks"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_chunks"
    )
    is_asr_generated = models.BooleanField(default=False)
    
    class Meta:
        constraints = [
            # Ensure transcriber and reviewer are different people
            models.CheckConstraint(
                check=~models.Q(transcriber=models.F('reviewer')),
                name='transcriber_reviewer_different'
            )
        ]


class TranscriptionRevision(BaseModel):
    """Tracks each revision made to a transcription"""
    transcription = models.ForeignKey(
        ChunkTranscription,
        on_delete=models.CASCADE,
        related_name="revisions"
    )
    previous_text = models.TextField()
    new_text = models.TextField()
    previous_status = models.ForeignKey(
        TranscriptionStatus,
        on_delete=models.PROTECT,
        related_name="previous_revisions"
    )
    new_status = models.ForeignKey(
        TranscriptionStatus,
        on_delete=models.PROTECT,
        related_name="new_revisions"
    )
    change_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']


class WorkSession(BaseModel):
    """Tracks user work sessions for accurate compensation"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="work_sessions"
    )
    session_type = models.CharField(
        max_length=20,
        choices=[
            ('TRANSCRIPTION', 'Transcription'),
            ('REVIEW', 'Review'),
        ]
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)
    chunks_processed = models.PositiveIntegerField(default=0)
    
    def close_session(self):
        """End the session and calculate duration"""
        if not self.end_time:
            self.end_time = timezone.now()
            self.duration = self.end_time - self.start_time
            self.save()


class ReviewQueue(BaseModel):
    """Manages chunks waiting for review"""
    transcription = models.OneToOneField(
        ChunkTranscription,
        on_delete=models.CASCADE,
        related_name="review_request"
    )
    priority = models.PositiveSmallIntegerField(default=5)  # 1-10 scale
    is_assigned = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reviews"
    )
    assignment_expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-priority', 'created_at']


# Enhanced UserStats to replace the current one
class UserStats(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stats",
    )
    transcriptions_created = models.PositiveIntegerField(default=0)
    transcriptions_reviewed = models.PositiveIntegerField(default=0)
    transcriptions_approved = models.PositiveIntegerField(default=0)
    transcriptions_rejected = models.PositiveIntegerField(default=0)
    
    # Track time spent
    total_transcription_time = models.DurationField(default=datetime.timedelta(0))
    total_review_time = models.DurationField(default=datetime.timedelta(0))
    
    # Track quality metrics
    transcription_approval_rate = models.FloatField(default=0.0)
    review_agreement_rate = models.FloatField(default=0.0)
    
    class Meta:
        indexes = [
            models.Index(fields=['transcriptions_created']),  
            models.Index(fields=['transcriptions_reviewed']),
            models.Index(fields=['transcription_approval_rate']),
        ]
    
    def update_counts(self):
        """Update all count fields"""
        # Count transcriptions created
        self.transcriptions_created = ChunkTranscription.objects.filter(
            transcriber=self.user
        ).count()
        
        # Count reviews performed
        reviewed_chunks = ChunkTranscription.objects.filter(
            reviewer=self.user
        )
        self.transcriptions_reviewed = reviewed_chunks.count()
        
        # Count approvals and rejections
        approved_status = TranscriptionStatus.objects.get(name="APPROVED")
        rejected_status = TranscriptionStatus.objects.get(name="REJECTED")
        
        self.transcriptions_approved = reviewed_chunks.filter(
            status=approved_status
        ).count()
        
        self.transcriptions_rejected = reviewed_chunks.filter(
            status=rejected_status
        ).count()
        
        self.save()
        
    def update_quality_metrics(self):
        """Calculate quality metrics"""
        # Calculate approval rate for this user's transcriptions
        if self.transcriptions_created > 0:
            approved_count = ChunkTranscription.objects.filter(
                transcriber=self.user,
                status__name="APPROVED"
            ).count()
            
            self.transcription_approval_rate = approved_count / self.transcriptions_created
        
        # Calculate agreement rate with other reviewers
        # This is a placeholder for more complex logic that could be implemented
        # to measure how often this reviewer agrees with others
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.transcriptions_created} transcriptions, {self.transcriptions_reviewed} reviews"