import pytest
from train.models import TrainingSession, TrainingProgress, EvaluationMetric
from authapp.models import User

@pytest.fixture
def test_user(db):
    """Create a test user."""
    return User.objects.create_user(
        whatsapp_number="+1234567890",  # Ensure the correct field is used
        password="testpassword",
    )

@pytest.fixture
def test_training_session(db, test_user):
    """Create a sample training session."""
    return TrainingSession.objects.create(
        model_name="YOLOv5",
        config={"epochs": 10, "batch_size": 16},
        status="pending",
        created_by=test_user,
        updated_by=test_user,
    )

def test_create_training_session(test_training_session):
    """Test that a training session can be created."""
    assert TrainingSession.objects.count() == 1
    assert test_training_session.model_name == "YOLOv5"

def test_create_training_progress(db, test_training_session, test_user):
    """Test that training progress can be recorded."""
    progress = TrainingProgress.objects.create(
        session=test_training_session,
        step=1,
        loss=0.5,
        grad_norm=1.2,
        learning_rate=0.001,
        epoch=0.1,
        created_by=test_user,
        updated_by=test_user,
    )
    assert TrainingProgress.objects.count() == 1
    assert progress.loss == 0.5

def test_create_evaluation_metric(db, test_training_session, test_user):
    """Test that an evaluation metric can be recorded."""
    metric = EvaluationMetric.objects.create(
        session=test_training_session,
        step=1,
        eval_loss=0.3,
        eval_wer=0.1,
        eval_runtime=2.5,
        eval_samples_per_second=5.0,
        eval_steps_per_second=2.0,
        epoch=0.1,
        created_by=test_user,
        updated_by=test_user,
    )
    assert EvaluationMetric.objects.count() == 1
    assert metric.eval_loss == 0.3
