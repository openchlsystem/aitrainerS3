import pytest
from rest_framework.test import APIClient
from train.models import TrainingSession, TrainingProgress, EvaluationMetric
from authapp.models import User
from django.urls import reverse

@pytest.fixture
def api_client():
    """Fixture to provide API client."""
    return APIClient()

@pytest.fixture
def test_user(db):
    """Create a regular test user."""
    return User.objects.create_user(
        whatsapp_number="+1234567890", 
        password="testpassword"
    )

@pytest.fixture
def test_staff_user(db):
    """Create a staff user (for GPU server actions)."""
    return User.objects.create_user(
        whatsapp_number="+1234567891", 
        password="testpassword",
        is_staff=True
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

# 🚀 Test Training Session Views
def test_list_training_sessions(api_client, test_user, test_training_session):
    """Test retrieving the list of training sessions."""
    api_client.force_authenticate(user=test_user)
    response = api_client.get(reverse("session-list-create"))
    assert response.status_code == 200
    assert len(response.data) == 1

def test_create_training_session(api_client, test_user):
    """Test creating a new training session."""
    api_client.force_authenticate(user=test_user)
    payload = {
        "model_name": "Whisper",
        "config": {"epochs": 20, "learning_rate": 0.001},
        "status": "pending",
    }
    response = api_client.post(reverse("session-list-create"), payload, format="json")
    assert response.status_code == 201
    assert TrainingSession.objects.count() == 1

def test_retrieve_training_session(api_client, test_user, test_training_session):
    """Test retrieving a single training session."""
    api_client.force_authenticate(user=test_user)
    response = api_client.get(reverse("session-detail", args=[test_training_session.unique_id]))
    assert response.status_code == 200
    assert response.data["model_name"] == "YOLOv5"

# 🚀 Test Training Progress Views
def test_list_training_progress(api_client, test_user, test_training_session):
    """Test listing training progress for a session."""
    api_client.force_authenticate(user=test_user)
    response = api_client.get(reverse("progress-list-create", args=[test_training_session.unique_id]))
    assert response.status_code == 200

def test_create_training_progress(api_client, test_staff_user, test_training_session):
    """Test recording training progress."""
    api_client.force_authenticate(user=test_staff_user)
    payload = {"step": 2, "loss": 0.45, "epoch": 0.2}
    response = api_client.post(reverse("progress-list-create", args=[test_training_session.unique_id]), payload, format="json")
    assert response.status_code == 201
    assert TrainingProgress.objects.count() == 1

def test_create_training_progress_denied_for_non_staff(api_client, test_user, test_training_session):
    """Ensure normal users cannot record training progress."""
    api_client.force_authenticate(user=test_user)
    payload = {"step": 2, "loss": 0.45, "epoch": 0.2}
    response = api_client.post(reverse("progress-list-create", args=[test_training_session.unique_id]), payload, format="json")
    assert response.status_code == 403

# 🚀 Test Evaluation Metrics Views
def test_create_evaluation_metric(api_client, test_staff_user, test_training_session):
    """Test recording evaluation metrics."""
    api_client.force_authenticate(user=test_staff_user)
    payload = {"step": 1, "eval_loss": 0.35, "eval_wer": 0.2}
    response = api_client.post(reverse("evaluation-list-create", args=[test_training_session.unique_id]), payload, format="json")
    assert response.status_code == 201
    assert EvaluationMetric.objects.count() == 1

def test_create_evaluation_metric_denied_for_non_staff(api_client, test_user, test_training_session):
    """Ensure normal users cannot post evaluation metrics."""
    api_client.force_authenticate(user=test_user)
    payload = {"step": 1, "eval_loss": 0.35, "eval_wer": 0.2}
    response = api_client.post(reverse("evaluation-list-create", args=[test_training_session.unique_id]), payload, format="json")
    assert response.status_code == 403
