# transcriptions/management/commands/validate_migration.py
from django.core.management.base import BaseCommand
from transcriptions.models import AudioChunk, ChunkTranscription, TranscriptionRevision

class Command(BaseCommand):
    help = 'Validates the migration from AudioChunk to ChunkTranscription'

    def handle(self, *args, **options):
        total_chunks = AudioChunk.objects.count()
        chunks_with_transcriptions = ChunkTranscription.objects.count()
        
        self.stdout.write(f"Total AudioChunks: {total_chunks}")
        self.stdout.write(f"Chunks with transcriptions: {chunks_with_transcriptions}")
        
        # Check for chunks with text but no transcription
        problematic_chunks = AudioChunk.objects.filter(
            feature_text__isnull=False
        ).exclude(
            current_transcription__isnull=False
        )
        
        self.stdout.write(f"Chunks with text but no transcription: {problematic_chunks.count()}")
        
        # Check revisions
        total_revisions = TranscriptionRevision.objects.count()
        self.stdout.write(f"Total transcription revisions: {total_revisions}")
        
        # Find transcriptions without revisions
        transcriptions_without_revisions = ChunkTranscription.objects.filter(revisions__isnull=True)
        self.stdout.write(f"Transcriptions without revisions: {transcriptions_without_revisions.count()}")
        
        # Report success or failure
        if problematic_chunks.count() > 0:
            self.stdout.write(self.style.ERROR('Migration validation failed: Some chunks with text have no transcription'))
        else:
            self.stdout.write(self.style.SUCCESS('Migration validation successful!'))
        
        # Don't return anything (implicitly returns None)