import os
import librosa
import soundfile as sf
import logging
from django.core.files import File
from django.core.management.base import BaseCommand
from transcriptions.models import AudioFile, cleaned_audio_file
import hashlib
import time
from django.conf import settings


class Command(BaseCommand):
    help = "Clean saved audio files, remove silences, and save the cleaned versions."

    def handle(self, *args, **kwargs):
        # Configure logging
        logging.basicConfig(
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

        # Ensure the output directory exists within MEDIA_ROOT
        output_dir = os.path.join(settings.MEDIA_ROOT, "cleaned-audio")
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                logging.info(f"Created directory: {output_dir}")
            except Exception as e:
                logging.error(f"Failed to create directory {output_dir}: {e}")
                self.stderr.write(self.style.ERROR(f"⚠️ Failed to create directory {output_dir}: {e}"))
                return

        # Process each AudioFile instance
        audio_files = AudioFile.objects.filter(is_cleaned=False)

        if not audio_files.exists():
            self.stdout.write(self.style.WARNING("⚠️ No audio files to clean."))
            return

        for audio_instance in audio_files:
            file_path = audio_instance.audio_file.path

            try:
                # ✅ Load the audio file
                y, sr = librosa.load(file_path, sr=16000)

                # ✅ Remove silences (example process using librosa.effects.trim)
                y_cleaned, _ = librosa.effects.trim(y, top_db=20)  # Adjust `top_db` as needed

                # Generate a unique hash-based name
                hash_seed = f"{file_path}{time.time()}".encode("utf-8")
                cleaned_file_name = f"{hashlib.sha256(hash_seed).hexdigest()[:16]}.wav"

                # ✅ Save the cleaned audio using soundfile
                cleaned_file_path = os.path.join(output_dir, cleaned_file_name)
                sf.write(cleaned_file_path, y_cleaned, sr)  # Save as WAV

                # Open the file for saving in the database
                with open(cleaned_file_path, "rb") as f:
                    django_file = File(f)

                    # Save cleaned_audio_file instance (ensures it's saved only once)
                    cleaned_instance, created = cleaned_audio_file.objects.get_or_create(
                        audio_file=f"cleaned-audio/{cleaned_file_name}",
                        defaults={
                            "file_size": os.path.getsize(cleaned_file_path),
                            "duration": librosa.get_duration(y=y_cleaned, sr=sr),
                        },
                    )

                    # Only save the file to the model if it was newly created
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"🎵 Cleaned audio file saved: {cleaned_file_path}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"✅ Using existing cleaned audio file: {cleaned_file_path}")
                        )

                # ✅ Update the original AudioFile instance
                audio_instance.is_cleaned = True
                audio_instance.save()

            except Exception as e:
                logging.error(f"Error cleaning {file_path}: {e}")
                self.stderr.write(self.style.ERROR(f"⚠️ Error cleaning {file_path}: {e}"))

        self.stdout.write(self.style.SUCCESS("✅ All audio files processed successfully."))

    def get_audio_duration(self, file_path):
        """Extracts the duration of an audio file."""
        try:
            y, sr = librosa.load(file_path, sr=None)  # Load audio with original sampling rate
            return librosa.get_duration(y=y, sr=sr)  # Calculate duration in seconds
        except Exception as e:
            logging.error(f"⚠️ Error extracting duration for {file_path}: {e}")
            return None  # Return None if duration extraction fails
