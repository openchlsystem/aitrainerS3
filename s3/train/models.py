import uuid
from django.db import models
from django.conf import settings

class BaseModel(models.Model):
    """Abstract base model for common fields."""
    unique_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, unique=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="updated_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TrainingSession(BaseModel):
    """Stores metadata about a training session."""
    SESSION_STATUS = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    model_name = models.CharField(max_length=100)  # e.g Whisper
    config = models.JSONField()  # Stores the training config as JSON
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default="pending")

    def __str__(self):
        return f"{self.model_name} ({self.unique_id}) - {self.status}"


class TrainingProgress(BaseModel):
    """Stores training progress updates."""
    session = models.ForeignKey(
        TrainingSession, on_delete=models.CASCADE, related_name="progress"
    )
    step = models.IntegerField()  # Training step number
    loss = models.FloatField(null=True, blank=True)
    grad_norm = models.FloatField(null=True, blank=True)
    learning_rate = models.FloatField(null=True, blank=True)
    epoch = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Step {self.step} - Loss: {self.loss}, Epoch: {self.epoch}"


class EvaluationMetric(BaseModel):
    """Stores evaluation metrics done during training."""
    session = models.ForeignKey(
        TrainingSession, on_delete=models.CASCADE, related_name="metrics"
    )
    step = models.IntegerField()  # Evaluation step number
    eval_loss = models.FloatField(null=True, blank=True)
    eval_wer = models.FloatField(null=True, blank=True)
    eval_runtime = models.FloatField(null=True, blank=True)
    eval_samples_per_second = models.FloatField(null=True, blank=True)
    eval_steps_per_second = models.FloatField(null=True, blank=True)
    epoch = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Step {self.step} - Eval Loss: {self.eval_loss}, Epoch: {self.epoch}"
