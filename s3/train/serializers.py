from rest_framework import serializers
from .models import TrainingSession, TrainingProgress, EvaluationMetric


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer to handle created_by and updated_by fields"""

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        validated_data["created_by"] = user
        validated_data["updated_by"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        validated_data["updated_by"] = user
        return super().update(instance, validated_data)


class TrainingSessionSerializer(BaseSerializer):
    """Serializer for Training Sessions"""

    class Meta:
        model = TrainingSession
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )  # Prevent modifications by users


class TrainingProgressSerializer(BaseSerializer):
    """Serializer for Training Progress"""
    session = serializers.UUIDField(source="session.unique_id", read_only=True)  # ✅ Include session in response

    class Meta:
        model = TrainingProgress
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )


class EvaluationMetricSerializer(BaseSerializer):
    """Serializer for Evaluation Metrics"""
    session = serializers.UUIDField(source="session.unique_id", read_only=True)  # ✅ Include session in response

    class Meta:
        model = EvaluationMetric
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )