import logging
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import AudioFile, DiarizedAudioFile, ProcessedAudioFile

# Configure logging
logger = logging.getLogger(__name__)

# Define the preprocessing API endpoint URL
# You should store this in your Django settings
GPU_SERVER_BASE_URL = getattr(settings, 'GPU_SERVER_BASE_URL')
PREPROCESSING_API_URL = f'{GPU_SERVER_BASE_URL}/audio/preprocess/'
DIARIZING_API_URL = f'{GPU_SERVER_BASE_URL}/audio/diarize/'
CHUNKING_API_URL = f'{GPU_SERVER_BASE_URL}/audio/chunk/'

@receiver(post_save, sender=AudioFile)
def trigger_audio_preprocessing(sender, instance, created, **kwargs):
    """
    Signal to trigger audio preprocessing when a new AudioFile is created
    or when an existing one is updated.
    """
    # Only send preprocessing request if:
    # 1. It's a new audio file (created=True) OR
    # 2. It's an update but the file is not already processed
    if created or (not instance.is_processed):
        # Get the full path of the audio file
        audio_path = instance.gpu_path
        
        # Prepare request payload
        payload = {
            'audio_path': audio_path,
            'noise_reduction': 0.3,  # Default value, can be customized
            'normalize': True,      # Default value, can be customized
            'project_id': str(instance.project_id),
        }
        
        try:
            # Send the request to the preprocessing service
            response = requests.post(
                PREPROCESSING_API_URL,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            
            # Check if the request was successful
            if response.status_code == 202:  # HTTP_202_ACCEPTED
                task_data = response.json()
                
                # Update is_processed flag to True
                # We need to be careful about recursion here by avoiding another post_save trigger
                # Using update() directly on the queryset bypasses the signal
                AudioFile.objects.filter(pk=instance.pk).update(is_processed=True)
                
                # Optionally store the task_id if needed
                # AudioFile.objects.filter(pk=instance.pk).update(
                #     is_processed=True,
                #     preprocessing_task_id=task_data.get('task_id')
                # )
                
                print(f"Preprocessing started for audio {instance.audio_id}. Task ID: {task_data.get('task_id')}")
            else:
                print(f"Failed to start preprocessing for audio {instance.audio_id}. Status: {response.status_code}")
                print(f"Response: {response.text}")
        
        except Exception as e:
            print(f"Error sending preprocessing request for audio {instance.audio_id}: {str(e)}")

@receiver(post_save, sender=ProcessedAudioFile)
def trigger_diarization(sender, instance, created, **kwargs):
    """
    Signal to trigger diarization when a ProcessedAudioFile is approved.
    This signal sends a POST request to the diarization endpoint with the GPU path.
    """
    # Only proceed if the is_approved flag was changed to True
    # We can detect this by checking if instance.is_approved is True and either:
    # 1. This is a new instance (created=True) with is_approved=True
    # 2. This is an existing instance that was updated (created=False)
    
    # Skip if not approved
    if not instance.is_approved:
        return
    
    # Get the GPU path of the audio file
    audio_path = instance.gpu_path
    
    # Prepare the payload for the API request
    payload = {
        "audio_path": audio_path,
        'project_id': str(instance.project_id),
    }
    
    # Make the API call to the diarization endpoint
    try:
        response = requests.post(
            DIARIZING_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Optional: Log the successful response
        print(f"Diarization triggered for {instance.processed_file.name}. Response: {response.json()}")
        
    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        print(f"Error triggering diarization for {instance.processed_file.name}: {str(e)}")
        # You might want to log this error or handle it in some other way
        # depending on your application's error handling strategy

@receiver(post_save, sender=DiarizedAudioFile)
def trigger_chunking(sender, instance, created, **kwargs):
    """
    Signal to trigger chunking when a DiarizedAudioFile is created or updated.
    This signal sends a POST request to the chunking endpoint with the necessary paths.
    """
    # Only proceed if this is a new instance
    # For chunking, we typically want to process new files immediately
    if not created:
        return
    
    # Get the GPU path of the audio file and diarization result
    audio_path = instance.gpu_path
    diarization_result = instance.diarization_json_gpu_path
    
    # Prepare the payload for the API request
    payload = {
        "audio_path": audio_path,
        "diarization_result": diarization_result,
        "project_id": str(instance.project_id),
    }
    
    logger.info(f"Preparing to trigger chunking for {instance.diarized_file.name}")
    
    # Make the API call to the chunking endpoint
    try:
        response = requests.post(
            CHUNKING_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        # Check if the request was successful
        response.raise_for_status()
        
        # Log the successful response
        logger.info(f"Chunking triggered for {instance.diarized_file.name}. Response: {response.json()}")
        
    except requests.exceptions.RequestException as e:
        # Handle any errors that occur during the request
        logger.error(f"Error triggering chunking for {instance.diarized_file.name}: {str(e)}")
        
        # If there's a response, try to log it for debugging
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_details = e.response.json()
                logger.error(f"Error details: {error_details}")
            except ValueError:
                logger.error(f"Error response (non-JSON): {e.response.text}")