"""
Speaker Diarization Service Module

Integrates face detection, clustering, VLM naming, and LLM assignment.
"""
from .pipeline import SpeakerDiarizationPipeline, process_speaker_diarization

__all__ = ['SpeakerDiarizationPipeline', 'process_speaker_diarization']
