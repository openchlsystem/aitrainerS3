import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import cleaned_audio_file
from .utils import split_and_save_chunks

@receiver(post_save, sender=cleaned_audio_file)
def handle_cleaned_audio_file_save(sender, instance, created, **kwargs):
    """
    Signal that listens for the post_save event of the cleaned_audio_file model.
    If is_evaluated is True, it triggers the split_and_save_chunks function.
    """
    if instance.is_evaluated:
        # Call the chunk splitting function
        num_chunks = split_and_save_chunks(
            cleaned_audio_obj=instance,
            output_format='wav',                # Output format
            min_chunk_length_ms=3000,          # Minimum chunk length in ms
            max_chunk_length_ms=7000,          # Maximum chunk length in ms
            frame_length_ms=30,                # Frame length in ms
            sr=16000,                          # Sample rate
            overlap_ms=2000                    # Overlap in ms
        )
        print(f"{num_chunks} chunks created and saved for audio: {instance.audio_file.name}.")
