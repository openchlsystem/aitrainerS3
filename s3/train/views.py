from rest_framework import generics, permissions, serializers
from .models import TrainingSession, TrainingProgress, EvaluationMetric
from .serializers import TrainingSessionSerializer, TrainingProgressSerializer, EvaluationMetricSerializer


# ✅ Custom Permissions
class GPUOnlyPermission(permissions.BasePermission):
    """Only GPU Server (staff) can send training updates."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return request.user.is_staff  # GPU server (or admins) can POST


# 🔹 Training Session Views
class TrainingSessionListCreateView(generics.ListCreateAPIView):
    """
    - GET: Users fetch all training sessions
    - POST: Users create a new training session from AI Trainer
    """
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]  # Users can create & view sessions


class TrainingSessionRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    """
    - GET: Fetch details of a training session
    - PATCH: (Future) Allow limited updates if needed
    """
    queryset = TrainingSession.objects.all()
    serializer_class = TrainingSessionSerializer
    lookup_field = "unique_id"
    permission_classes = [permissions.IsAuthenticated]  # Users can fetch


# 🔹 Training Progress Views
class TrainingProgressListCreateView(generics.ListCreateAPIView):
    serializer_class = TrainingProgressSerializer
    permission_classes = [GPUOnlyPermission]  

    def get_queryset(self):
        session_id = self.kwargs["session_id"]
        return TrainingProgress.objects.filter(session__unique_id=session_id).order_by("step")

    def perform_create(self, serializer):
        session_id = self.kwargs.get("session_id")
        try:
            session = TrainingSession.objects.get(unique_id=session_id)
            serializer.save(session=session)  # Automatically attach session
        except TrainingSession.DoesNotExist:
            raise serializers.ValidationError({"error": "Session not found."})



class TrainingProgressRetrieveView(generics.RetrieveAPIView):
    """
    - GET: Users fetch details of a single progress update
    """
    queryset = TrainingProgress.objects.all()
    serializer_class = TrainingProgressSerializer
    lookup_field = "unique_id"
    permission_classes = [permissions.IsAuthenticated]  # Users can fetch


# 🔹 Evaluation Metrics Views
class EvaluationMetricListCreateView(generics.ListCreateAPIView):
    """
    - GET: Users fetch evaluation metrics of a session
    - POST: GPU server sends evaluation metrics
    """
    serializer_class = EvaluationMetricSerializer
    permission_classes = [GPUOnlyPermission]  # Only GPU posts evaluation results

    def get_queryset(self):
        session_id = self.kwargs["session_id"]
        return EvaluationMetric.objects.filter(session__unique_id=session_id).order_by("step")
    
    def perform_create(self, serializer):
        session_id = self.kwargs.get("session_id")
        try:
            session = TrainingSession.objects.get(unique_id=session_id)
            serializer.save(session=session)  # Automatically attach session
        except TrainingSession.DoesNotExist:
            raise serializers.ValidationError({"error": "Session not found."})


class EvaluationMetricRetrieveView(generics.RetrieveAPIView):
    """
    - GET: Users fetch details of a specific evaluation metric
    """
    queryset = EvaluationMetric.objects.all()
    serializer_class = EvaluationMetricSerializer
    lookup_field = "unique_id"
    permission_classes = [permissions.IsAuthenticated]  # Users can fetch
