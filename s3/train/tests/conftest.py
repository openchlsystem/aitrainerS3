import pytest
from rest_framework.test import APIClient
from authapp.models import User
from train.models import TrainingSession

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

