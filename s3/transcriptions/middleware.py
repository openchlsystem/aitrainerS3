# middleware.py
from django.http import JsonResponse
from .models import Project

class ProjectContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract project ID from header
        project_id = request.headers.get('x-project-id')
        
        # If project ID is present, try to get the project
        if project_id:
            try:
                request.project = Project.objects.get(unique_id=project_id)
            except Project.DoesNotExist:
                return JsonResponse(
                    {"error": f"Project with ID {project_id} not found"}, 
                    status=404
                )
        else:
            request.project = None
            
        response = self.get_response(request)
        return response