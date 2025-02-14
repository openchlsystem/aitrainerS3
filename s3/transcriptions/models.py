from django.db import models
import uuid


class base_model(models.Model):
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_by = models.CharField(max_length=50, null=True)
    updated_by = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = (
            True  # Marking as abstract avoids table creation and field conflicts.
        )


# Audio file must be downloaded prior
class AudioFile(base_model):
    audio_id = models.CharField(max_length=50, unique=True)
    audio_file = models.FileField(upload_to="audios/")
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)
    is_cleaned = models.BooleanField(default=False)

    def __str__(self):
        return self.unique_id


# confirm audio files are usable example long silence , volume , within selected specttogram
class cleaned_audio_file(base_model):
    # audio_id = models.OneToOneField(AudioFile, on_delete=models.CASCADE, related_name="evaluated_audio_file",null=True,unique=True)
    audio_file = models.FileField(upload_to="cleaned-audio/")
    is_evaluated = models.BooleanField(default=False)
    file_size = models.PositiveIntegerField(null=True)
    duration = models.FloatField(null=True)
    # is_evaluated_by = models.CharField(max_length=50, null=True)
    # evaluation_date = models.DateTimeField(null=True)
    # evaluation_notes = models.TextField(null=True)
    # evaluation_score = models.FloatField(null=True)
    # evaluation_status = models.CharField(max_length=50, null=True)
    # evaluation_result = models.CharField(max_length=50, null=True)
    # evaluation_result_notes = models.TextField(null=True)
    # evaluation_result_score = models.FloatField(null=True)
    # evaluation_result_status = models.CharField(max_length=50, null=True)
    # evaluation_result_notes = models.TextField(null=True)


# This should be imported from a CSV file generated by the helpline
class CaseRecord(base_model):
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


# The records should be created by the automated process to determine the sight spectogram and the transcription
class evaluation_record(base_model):
    audio_id = models.OneToOneField(
        AudioFile,
        on_delete=models.CASCADE,
        related_name="evaluation_record",
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
    true_transcription = models.TextField()
    true_transcription_locale = models.CharField

class AudioFileChunk(base_model):
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

    chunk_file = models.FileField(
        upload_to="audio-chunks/"
    )  # Order of the chunk in the original file
    duration = models.FloatField(null=True)
    feature_text = models.TextField(
        blank=True, null=True
    )  # ✅ Holds ground-truth transcriptions
    gender = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default="not_sure"
    )  # ✅ Gender field
    locale = models.CharField(
        max_length=5, choices=LOCALE_CHOICES, default="both"
    )  # ✅ Locale field
    is_evaluated = models.BooleanField(
        default=False
    )  # ✅ Tracks whether chunk is evaluated
    evaluation_count = models.PositiveIntegerField(default=0)
    transcribe_chunk = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Set is_evaluated to True if evaluation_count >= 3.
        if self.evaluation_count >= 1:
            self.is_evaluated = True
        else:
            self.is_evaluated = False
        super().save(*args, **kwargs)


class evaluation_results(base_model):
    audiofilechunk = models.ForeignKey(
        AudioFileChunk, on_delete=models.CASCADE, related_name="evaluation_results"
    )
    single_speaker = models.BooleanField(default=False)
    speaker_overlap = models.BooleanField(default=False)
    background_noise = models.BooleanField(default=False)
    prolonged_silence = models.BooleanField(default=False)
    # background_noise_level = models.FloatField(null=False)
    not_speech_rate = models.BooleanField(default=False)
    echo_noise = models.BooleanField(default=False)
    is_evaluated = models.BooleanField(default=False)
    is_evaluated_by = models.CharField(max_length=50, null=True)
    # is_evaluated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="evaluations")
    evaluation_date = models.DateTimeField(null=True)
    evaluation_notes = models.TextField(null=True)

    class Meta:
        unique_together = ('audiofilechunk', 'is_evaluated_by')

