import pytest
from train.models import TrainingSession, TrainingProgress, EvaluationMetric
from train.serializers import (
    TrainingSessionSerializer,
    TrainingProgressSerializer,
    EvaluationMetricSerializer,
)

@pytest.mark.django_db
def test_training_session_serializer_create():
    data = {
        "model_name": "Whisper",
        "config": {"lr": 0.001, "batch_size": 32},
        "status": "pending",
    }
    serializer = TrainingSessionSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.model_name == "Whisper"
    assert instance.config == {"lr": 0.001, "batch_size": 32}
    assert instance.status == "pending"


@pytest.mark.django_db
def test_training_progress_serializer_create():
    session = TrainingSession.objects.create(
        model_name="YOLOv5",
        config={"epochs": 10},
        status="running",
    )
    data = {
        "session": session.unique_id,
        "step": 1,
        "loss": 0.05,
        "grad_norm": 0.1,
        "learning_rate": 0.001,
        "epoch": 1.0,
    }
    serializer = TrainingProgressSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.step == 1
    assert instance.loss == 0.05
    assert instance.grad_norm == 0.1
    assert instance.learning_rate == 0.001
    assert instance.epoch == 1.0


@pytest.mark.django_db
def test_evaluation_metric_serializer_create():
    session = TrainingSession.objects.create(
        model_name="Whisper",
        config={"epochs": 10},
        status="running",
    )
    data = {
        "session": session.unique_id,
        "step": 2,
        "eval_loss": 0.02,
        "eval_wer": 0.1,
        "eval_runtime": 0.5,
        "eval_samples_per_second": 20.0,
        "eval_steps_per_second": 5.0,
        "epoch": 2.0,
    }
    serializer = EvaluationMetricSerializer(data=data, context={"request": None})
    assert serializer.is_valid(), serializer.errors
    instance = serializer.save()
    assert instance.step == 2
    assert instance.eval_loss == 0.02
    assert instance.eval_wer == 0.1
    assert instance.eval_runtime == 0.5
    assert instance.eval_samples_per_second == 20.0
    assert instance.eval_steps_per_second == 5.0
    assert instance.epoch == 2.0
