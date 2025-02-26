from transcriptions.models import Project, AudioFile, CaseRecord, AudioFileChunk, EvaluationResults

# Create a default project
default_project, _ = Project.objects.get_or_create(name="Default Project")

# Assign the default project to existing records
models_to_update = [AudioFile, CaseRecord, AudioFileChunk, EvaluationResults]

for model in models_to_update:
    model.objects.filter(project__isnull=True).update(project=default_project)

# run the following command to add the default project to the existing records:

# python manage.py shell < transcriptions/management/default_project.py
