# import os
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.conf import settings
# from .models import CleanedAudioFile
# from .utils import split_and_save_chunks

# @receiver(post_save, sender=CleanedAudioFile)
# def handle_cleaned_audio_file_save(sender, instance, created, **kwargs):
#     """
#     Signal that listens for the post_save event of the cleaned_audio_file model.
#     If is_evaluated is True, it triggers the split_and_save_chunks function.
#     """
#     if instance.is_approved:
#         # Call the chunk splitting function
#         num_chunks = split_and_save_chunks(
#             audio_obj=instance,
#             output_format='wav',                # Output format
#             min_chunk_length_ms=3000,          # Minimum chunk length in ms
#             max_chunk_length_ms=7000,          # Maximum chunk length in ms
#             frame_length_ms=30,                # Frame length in ms
#             sr=16000,                          # Sample rate
#             overlap_ms=2000                    # Overlap in ms
#         )
#         print(f"{num_chunks} chunks created and saved for audio: {instance.audio_file.name}.")

import os
import requests
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import AudioFile

# Define the preprocessing API endpoint URL
# You should store this in your Django settings
GPU_SERVER_BASE_URL = getattr(settings, 'GPU_SERVER_BASE_URL')
PREPROCESSING_API_URL = f'{GPU_SERVER_BASE_URL}/audio/preprocess/'

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