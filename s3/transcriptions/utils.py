import os
import librosa
import numpy as np
import soundfile as sf
from concurrent.futures import ThreadPoolExecutor
from django.conf import settings
from transcriptions.models import cleaned_audio_file, AudioFileChunk


def adjust_to_frame_length(chunk_length_ms, frame_length_ms):
    return (
        (chunk_length_ms + frame_length_ms - 1) // frame_length_ms
    ) * frame_length_ms


def samples_per_ms(sample_rate, ms):
    return int(sample_rate * ms / 1000)


def compute_dynamic_thresholds(audio, sr, frame_length_samples, segment_length_samples):
    energy_thresholds = []
    zcr_thresholds = []

    for i in range(0, len(audio), segment_length_samples):
        segment = audio[i : i + segment_length_samples]
        n_frames = max(int(len(segment) / frame_length_samples), 1)
        energy = np.array(
            [
                np.sum(
                    segment[j * frame_length_samples : (j + 1) * frame_length_samples]
                    ** 2
                )
                for j in range(n_frames)
            ]
        )
        zcr = np.array(
            [
                np.sum(
                    librosa.zero_crossings(
                        segment[
                            j * frame_length_samples : (j + 1) * frame_length_samples
                        ],
                        pad=False,
                    )
                )
                for j in range(n_frames)
            ]
        )
        energy_thresholds.append(np.mean(energy) + 3 * np.std(energy))
        zcr_thresholds.append(np.mean(zcr) + 3 * np.std(zcr))

    return energy_thresholds, zcr_thresholds


def analyze_chunks(
    audio,
    sr,
    min_chunk_length_samples,
    max_chunk_length_samples,
    frame_length_samples,
    overlap_samples,
):
    segment_length_samples = len(audio) // 5
    energy_thresholds, zcr_thresholds = compute_dynamic_thresholds(
        audio, sr, frame_length_samples, segment_length_samples
    )

    chunks = []
    current_chunk_start = None
    last_valid_end = None
    is_previous_frame_silent = False

    for i in range(0, len(audio), frame_length_samples):
        segment_index = i // segment_length_samples
        segment_index = min(segment_index, len(energy_thresholds) - 1)

        energy_threshold = energy_thresholds[segment_index]
        zcr_threshold = zcr_thresholds[segment_index]

        frame = audio[i : min(i + frame_length_samples, len(audio))]
        frame_energy = np.sum(frame**2)
        frame_zcr = np.sum(librosa.zero_crossings(frame, pad=False))

        is_silent = frame_energy <= energy_threshold and frame_zcr <= zcr_threshold

        if current_chunk_start is None and not is_silent:
            current_chunk_start = i
            last_valid_end = i + frame_length_samples

        if current_chunk_start is not None:
            if is_silent and (
                is_previous_frame_silent
                or i + frame_length_samples - current_chunk_start
                >= max_chunk_length_samples
            ):
                if (
                    last_valid_end
                    and last_valid_end - current_chunk_start >= min_chunk_length_samples
                ):
                    chunks.append(
                        (current_chunk_start, last_valid_end + overlap_samples)
                    )
                    current_chunk_start = None
            else:
                last_valid_end = i + frame_length_samples
                if (
                    not is_silent
                    and i + frame_length_samples - current_chunk_start
                    >= max_chunk_length_samples
                ):
                    chunks.append(
                        (
                            current_chunk_start,
                            min(len(audio), last_valid_end + overlap_samples),
                        )
                    )
                    current_chunk_start = None

        is_previous_frame_silent = is_silent

    if (
        current_chunk_start is not None
        and last_valid_end - current_chunk_start >= min_chunk_length_samples
    ):
        chunks.append(
            (current_chunk_start, min(len(audio), last_valid_end + overlap_samples))
        )

    return chunks


def save_chunk(y, sr, start_end_tuple, index, output_dir, file_prefix, output_format):
    start, end = start_end_tuple
    chunk = y[start:end]
    chunk_audio_path = os.path.join(
        output_dir, f"{file_prefix}_chunk_{str(index).zfill(4)}.{output_format}"
    )
    sf.write(chunk_audio_path, chunk, sr)

    AudioFileChunk.objects.create(
        chunk_file=os.path.relpath(chunk_audio_path, settings.MEDIA_ROOT),
        duration=librosa.get_duration(y=chunk, sr=sr),
    )
    return chunk_audio_path


def split_and_save_chunks(
    audio_obj,
    output_format="wav",
    min_chunk_length_ms=3000,
    max_chunk_length_ms=7000,
    frame_length_ms=30,
    sr=16000,
    overlap_ms=2000,
):
    input_file = audio_obj.audio_file.path
    output_dir = os.path.join(settings.MEDIA_ROOT, "audio_chunks")
    os.makedirs(output_dir, exist_ok=True)
    file_prefix = os.path.splitext(os.path.basename(input_file))[0]

    y, _ = librosa.load(input_file, sr=sr)
    overlap_samples = samples_per_ms(sr, overlap_ms)
    frame_length_samples = samples_per_ms(sr, frame_length_ms)
    min_chunk_length_samples = samples_per_ms(
        sr, adjust_to_frame_length(min_chunk_length_ms, frame_length_ms)
    )
    max_chunk_length_samples = samples_per_ms(
        sr, adjust_to_frame_length(max_chunk_length_ms, frame_length_ms)
    )
    chunks = analyze_chunks(
        y,
        sr,
        min_chunk_length_samples,
        max_chunk_length_samples,
        frame_length_samples,
        overlap_samples,
    )

    chunk_paths = []
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                save_chunk, y, sr, chunk, i, output_dir, file_prefix, output_format
            )
            for i, chunk in enumerate(chunks)
        ]
        for future in futures:
            chunk_paths.append(future.result())

    # Save to ChunkedAudio model
    # for chunk_path in chunk_paths:
    #     AudioFileChunk.objects.create(
    #         chunk_file=os.path.relpath(chunk_path, settings.MEDIA_ROOT),
    #         defaults={
    #             "file_size": os.path.getsize(chunk_path),
    #             "duration": librosa.get_duration(y=chunk, sr=sr),
    #         },
    #     )

    return len(chunk_paths)


def process_all_cleaned_audio():
    cleaned_audio_files = cleaned_audio_file.objects.all()
    for audio_file in cleaned_audio_files:
        split_and_save_chunks(audio_file)
