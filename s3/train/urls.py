from django.urls import path
from .views import (
    TrainingSessionListCreateView,
    TrainingSessionRetrieveUpdateView,
    TrainingProgressListCreateView,
    TrainingProgressRetrieveView,
    EvaluationMetricListCreateView,
    EvaluationMetricRetrieveView,
)

urlpatterns = [
    # Training Sessions
    path("sessions/", TrainingSessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<uuid:unique_id>/", TrainingSessionRetrieveUpdateView.as_view(), name="session-detail"),

    # Training Progress
    path("sessions/<uuid:session_id>/progress/", TrainingProgressListCreateView.as_view(), name="progress-list-create"),
    path("progress/<uuid:unique_id>/", TrainingProgressRetrieveView.as_view(), name="progress-detail"),

    # Evaluation Metrics
    path("sessions/<uuid:session_id>/evaluation/", EvaluationMetricListCreateView.as_view(), name="evaluation-list-create"),
    path("evaluation/<uuid:unique_id>/", EvaluationMetricRetrieveView.as_view(), name="evaluation-detail"),
]
