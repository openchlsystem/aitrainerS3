from django.urls import resolve, reverse
from train.views import (
    TrainingSessionListCreateView,
    TrainingSessionRetrieveUpdateView,
    TrainingProgressListCreateView,
    TrainingProgressRetrieveView,
    EvaluationMetricListCreateView,
    EvaluationMetricRetrieveView,
)

def test_training_session_list_create_url():
    """Test training session list/create URL."""
    url = reverse("session-list-create")
    assert resolve(url).func.view_class == TrainingSessionListCreateView

def test_training_session_detail_url():
    """Test training session detail URL."""
    url = reverse("session-detail", args=["123e4567-e89b-12d3-a456-426614174000"])
    assert resolve(url).func.view_class == TrainingSessionRetrieveUpdateView

def test_training_progress_list_create_url():
    """Test training progress list/create URL."""
    url = reverse("progress-list-create", args=["123e4567-e89b-12d3-a456-426614174000"])
    assert resolve(url).func.view_class == TrainingProgressListCreateView

def test_training_progress_detail_url():
    """Test training progress detail URL."""
    url = reverse("progress-detail", args=["123e4567-e89b-12d3-a456-426614174000"])
    assert resolve(url).func.view_class == TrainingProgressRetrieveView

def test_evaluation_metric_list_create_url():
    """Test evaluation metric list/create URL."""
    url = reverse("evaluation-list-create", args=["123e4567-e89b-12d3-a456-426614174000"])
    assert resolve(url).func.view_class == EvaluationMetricListCreateView

def test_evaluation_metric_detail_url():
    """Test evaluation metric detail URL."""
    url = reverse("evaluation-detail", args=["123e4567-e89b-12d3-a456-426614174000"])
    assert resolve(url).func.view_class == EvaluationMetricRetrieveView
