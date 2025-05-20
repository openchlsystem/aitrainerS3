# services.py
from django.utils import timezone
import datetime
from .models import AudioChunk, ChunkTranscription, TranscriptionRevision, TranscriptionStatus, WorkSession, ReviewQueue

class TranscriptionService:
    @staticmethod
    def assign_chunk_to_transcriber(user):
        """Assigns an available chunk to a transcriber"""
        # Find an unassigned chunk
        chunk = AudioChunk.objects.filter(
            is_assigned=False,
            current_transcription__isnull=True  # No existing transcription
        ).first()
        
        if not chunk:
            return None
            
        # Assign the chunk
        chunk.assign_to_user(user)
        
        # Create a draft transcription
        draft_status = TranscriptionStatus.objects.get(name='DRAFT')
        transcription = ChunkTranscription(
            audio_chunk=chunk,
            text='',
            status=draft_status,
            transcriber=user,
            is_asr_generated=False
        )
        transcription.save()
        
        # Start a work session
        session = WorkSession(
            user=user,
            session_type='TRANSCRIPTION',
            start_time=timezone.now()
        )
        session.save()
        
        return chunk, transcription, session
    
    @staticmethod
    def submit_for_review(transcription, user):
        """Submit a transcription for review"""
        if transcription.transcriber != user:
            raise ValueError("Only the transcriber can submit for review")
            
        if not transcription.text.strip():
            raise ValueError("Cannot submit empty transcription for review")
            
        # Get status
        pending_status = TranscriptionStatus.objects.get(name='PENDING_REVIEW')
        previous_status = transcription.status
        
        # Create revision
        revision = TranscriptionRevision(
            transcription=transcription,
            previous_text=transcription.text,
            new_text=transcription.text,  # Same text, just status change
            previous_status=previous_status,
            new_status=pending_status,
            created_by=user,
            updated_by=user
        )
        revision.save()
        
        # Update transcription status
        transcription.status = pending_status
        transcription.save()
        
        # Add to review queue
        review_request = ReviewQueue(
            transcription=transcription,
            created_by=user,
            updated_by=user
        )
        review_request.save()
        
        return transcription, review_request

class ReviewService:
    @staticmethod
    def assign_transcription_for_review(user):
        """Assign a transcription to a reviewer"""
        # Find an item in the review queue
        pending_status = TranscriptionStatus.objects.get(name='PENDING_REVIEW')
        
        # Get a transcription that's not created by this user and not already assigned
        review_item = ReviewQueue.objects.filter(
            is_assigned=False,
            transcription__status=pending_status
        ).exclude(
            transcription__transcriber=user  # Ensure reviewer isn't the transcriber
        ).order_by('-priority', 'created_at').first()
        
        if not review_item:
            return None
            
        # Assign to reviewer
        review_item.is_assigned = True
        review_item.assigned_to = user
        review_item.assignment_expires_at = timezone.now() + datetime.timedelta(minutes=30)
        review_item.save()
        
        # Start a work session
        session = WorkSession(
            user=user,
            session_type='REVIEW',
            start_time=timezone.now()
        )
        session.save()
        
        return review_item, session
    
    @staticmethod
    def complete_review(review_item, action, text, feedback, user):
        """Complete a review with the given action"""
        if review_item.assigned_to != user:
            raise ValueError("Only the assigned reviewer can complete this review")
            
        transcription = review_item.transcription
        previous_status = transcription.status
        
        # Get appropriate status based on action
        new_status = TranscriptionStatus.objects.get(name=action)
        
        # Create revision
        revision = TranscriptionRevision(
            transcription=transcription,
            previous_text=transcription.text,
            new_text=text,
            previous_status=previous_status,
            new_status=new_status,
            change_reason=feedback,
            created_by=user,
            updated_by=user
        )
        revision.save()
        
        # Update transcription
        transcription.text = text
        transcription.status = new_status
        transcription.reviewer = user
        transcription.save()
        
        # Remove from review queue
        review_item.delete()
        
        # If rejected, reassign to original transcriber
        if action == 'NEEDS_CORRECTION':
            chunk = transcription.audio_chunk
            chunk.assign_to_user(transcription.transcriber)
        
        # Update user stats
        user_stats = user.stats
        user_stats.update_counts()
        user_stats.update_quality_metrics()
        
        transcriber_stats = transcription.transcriber.stats
        transcriber_stats.update_counts()
        transcriber_stats.update_quality_metrics()
        
        return transcription