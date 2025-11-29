from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path

from flask import current_app

try:  # pragma: no cover - optional dependency at runtime
    import google.generativeai as genai
    from google.api_core import exceptions as google_exceptions
except Exception:  # pragma: no cover
    genai = None  # type: ignore[assignment]
    google_exceptions = Exception  # type: ignore[assignment, misc]

# Gemini 1.5 Pro limits:
# - Max file size: 20MB
# - Max duration: 2 minutes per chunk
# - We'll split longer videos into 2-minute chunks
GEMINI_MAX_SIZE = 20 * 1024 * 1024  # 20 MB
GEMINI_MAX_DURATION_SECONDS = 120  # 2 minutes


def _get_video_duration(video_path: Path) -> float:
    """
    Get video duration in seconds using ffprobe.
    Returns 0.0 if duration cannot be determined.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            logger.info("Video duration: %.2f seconds", duration)
            return duration
        else:
            logger.warning("Could not determine video duration: %s", result.stderr)
            return 0.0
    except FileNotFoundError:
        logger.warning("ffprobe not found, cannot determine video duration")
        return 0.0
    except Exception as e:
        logger.warning("Error getting video duration: %s", e)
        return 0.0


def _split_video_into_chunks(video_path: Path, chunk_duration: int = GEMINI_MAX_DURATION_SECONDS) -> list[Path]:
    """
    Split video into chunks of max duration (default 2 minutes).
    Returns list of chunk file paths.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    duration = _get_video_duration(video_path)
    
    # If video is short enough, return original
    if duration <= chunk_duration:
        logger.info("Video is short enough (%.2f seconds), no chunking needed", duration)
        return [video_path]
    
    logger.info("Splitting video into chunks (duration: %.2f seconds)", duration)
    chunks = []
    chunk_dir = tempfile.mkdtemp()
    num_chunks = int(duration / chunk_duration) + (1 if duration % chunk_duration > 0 else 0)
    
    try:
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = Path(chunk_dir) / f"chunk_{i:03d}.mp4"
            
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-ss", str(start_time),
                "-t", str(chunk_duration),
                "-c", "copy",  # Copy codec (fast, no re-encoding)
                "-avoid_negative_ts", "make_zero",
                "-y",
                str(chunk_path),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode == 0 and chunk_path.exists():
                chunks.append(chunk_path)
                logger.info("Created chunk %d/%d: %s (%.2f MB)", 
                          i + 1, num_chunks, chunk_path, 
                          chunk_path.stat().st_size / (1024 * 1024))
            else:
                logger.error("Failed to create chunk %d: %s", i, result.stderr)
                # Clean up partial chunks
                for c in chunks:
                    if c.exists():
                        c.unlink(missing_ok=True)
                raise RuntimeError(f"Failed to split video: {result.stderr}")
        
        logger.info("Successfully split video into %d chunks", len(chunks))
        return chunks
        
    except FileNotFoundError:
        logger.error("ffmpeg not found. Please install ffmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
        raise RuntimeError("ffmpeg is required to split video files. Please install ffmpeg.")
    except Exception as e:
        # Clean up on error
        for chunk in chunks:
            if chunk.exists():
                chunk.unlink(missing_ok=True)
        logger.exception("Failed to split video: %s", e)
        raise


def _prepare_video_for_gemini(video_path: Path) -> tuple[list[Path], bool]:
    """
    Prepare video file(s) for Gemini API.
    - If file is small enough and short enough, return as single file
    - Otherwise, split into chunks
    - Returns (list of video paths, whether temp files were created)
    """
    file_size = video_path.stat().st_size
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    
    # Check if file needs compression or chunking
    duration = _get_video_duration(video_path)
    needs_chunking = duration > GEMINI_MAX_DURATION_SECONDS
    needs_compression = file_size > GEMINI_MAX_SIZE
    
    if not needs_chunking and not needs_compression:
        logger.info("Video file OK (%d bytes, %.2f seconds), using directly", 
                   file_size, duration)
        return [video_path], False
    
    # If we need chunking, split first
    if needs_chunking:
        logger.info("Video too long (%.2f seconds), splitting into chunks", duration)
        chunks = _split_video_into_chunks(video_path)
        return chunks, True
    
    # If we only need compression (large file but short duration)
    if needs_compression:
        logger.info("Video file too large (%d bytes), compressing", file_size)
        try:
            temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_video.close()
            temp_path = Path(temp_video.name)
            
            # Compress video using ffmpeg
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-c:v", "libx264",
                "-crf", "28",  # Higher CRF = more compression
                "-preset", "fast",
                "-c:a", "aac",
                "-b:a", "64k",
                "-y",
                str(temp_path),
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
            )
            
            if result.returncode == 0 and temp_path.exists():
                compressed_size = temp_path.stat().st_size
                logger.info("Compressed video to %d bytes (%.2f MB)", 
                          compressed_size, compressed_size / (1024 * 1024))
                if compressed_size > GEMINI_MAX_SIZE:
                    logger.warning("Compressed video still too large, may need further processing")
                return [temp_path], True
            else:
                temp_path.unlink(missing_ok=True)
                raise RuntimeError(f"Failed to compress video: {result.stderr}")
                
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)")
            raise RuntimeError("ffmpeg is required to compress large video files. Please install ffmpeg.")
        except Exception as e:
            logger.exception("Failed to compress video: %s", e)
            raise
    
    return [video_path], False


def _get_gemini_client():
    """
    Configure and return Gemini client.
    Raises RuntimeError if library is missing or API key is not set.
    """
    if genai is None:
        raise RuntimeError(
            "google-generativeai package is not installed. Make sure requirements are up to date.",
        )
    
    # Get API key from Flask config or environment
    try:
        api_key = current_app.config.get("GEMINI_API_KEY", "")
    except RuntimeError:
        # Outside Flask context, use os.getenv directly
        api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Check your .env file or environment variables.")
    
    genai.configure(api_key=api_key)
    return genai


def _transcribe_video_chunk(video_path: Path, model_name: str = "gemini-2.5-flash") -> str:
    """
    Transcribe a single video chunk using Gemini API.
    Returns transcript text.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    _get_gemini_client()  # Configure API key
    
    file_size = video_path.stat().st_size
    logger.info("Transcribing video chunk: %s (%d bytes, %.2f MB)", 
               video_path, file_size, file_size / (1024 * 1024))
    
    video_file = None
    try:
        # Upload video file to Gemini
        video_file = genai.upload_file(path=str(video_path))
        logger.info("Uploaded video file: %s (state: %s)", video_file.name, video_file.state)
        
        # Wait for file to be processed
        import time
        max_wait = 60  # Max 60 seconds wait
        wait_time = 0
        while video_file.state.name == "PROCESSING":
            if wait_time >= max_wait:
                raise RuntimeError("Video file processing timed out")
            logger.info("Waiting for video processing... (%.0f seconds)", wait_time)
            time.sleep(2)
            wait_time += 2
            video_file = genai.get_file(video_file.name)
        
        # Check if processing failed
        if video_file.state.name == "FAILED":
            raise RuntimeError(f"Video file processing failed: {video_file.state}")
        
        # Generate transcript using Gemini
        model = genai.GenerativeModel(model_name)
        prompt = "Transcribe the spoken words clearly and accurately."
        
        # Pass video file and prompt to model
        response = model.generate_content([video_file, prompt])
        
        # Extract text from response
        transcript = response.text.strip()
        
        logger.info("Transcription complete (%d chars)", len(transcript))
        return transcript
        
    except Exception as e:
        logger.exception("Failed to transcribe video chunk: %s", e)
        raise
    finally:
        # Clean up uploaded file
        if video_file is not None:
            try:
                genai.delete_file(video_file.name)
                logger.info("Cleaned up uploaded video file")
            except Exception as e:
                logger.warning("Failed to delete uploaded file: %s", e)


def _summarize_transcript(transcript: str) -> str:
    """
    Generate a professional, job-focused summary from the transcript using Gemini.
    This summary will replace the user's professional summary field.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    _get_gemini_client()  # Configure API key
    
    logger.info("Generating job-focused professional summary from transcript (%d chars)", len(transcript))
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        "You are helping an employee create a professional summary for their resume/profile. "
        "Based ONLY on the transcript provided, create a compelling professional summary that:\n"
        "1. Highlights relevant experience and achievements\n"
        "2. Emphasizes key skills and qualifications\n"
        "3. Is tailored to appeal to employers across various job roles\n"
        "4. Uses professional, confident language\n"
        "5. Is concise (3-4 sentences, maximum 300 words)\n\n"
        "IMPORTANT: Only use information explicitly mentioned in the transcript. "
        "Do NOT invent jobs, companies, dates, or skills that are not mentioned.\n\n"
        "Format: Write as a cohesive paragraph (not bullet points). "
        "Make it sound professional and ready to use as a resume summary.\n\n"
        f"Transcript:\n\n{transcript}"
    )
    
    response = model.generate_content(prompt)
    summary = response.text.strip()
    
    logger.info("Professional summary generated (%d chars)", len(summary))
    return summary


def _extract_profile_data(transcript: str) -> dict[str, str | list[str]]:
    """
    Extract structured profile data from transcript using AI.
    Returns a dictionary with: headline, summary, skills, certifications, experience.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    _get_gemini_client()  # Configure API key
    
    logger.info("Extracting profile data from transcript (%d chars)", len(transcript))
    
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = (
        "You are helping extract structured profile information from a video transcript. "
        "Based ONLY on the transcript provided, extract the following information:\n\n"
        "1. HEADLINE: A short professional headline (max 140 characters) that summarizes their role/experience. "
        "Example: 'Experienced Chef with 5+ years in fine dining' or 'Customer Service Professional seeking retail opportunities'\n\n"
        "2. SUMMARY: A compelling professional summary (3-4 sentences, max 300 words) that highlights:\n"
        "   - Relevant experience and achievements\n"
        "   - Key skills and qualifications\n"
        "   - Professional strengths\n"
        "   Format as a cohesive paragraph (not bullet points).\n\n"
        "3. SKILLS: Extract all mentioned skills, technical abilities, and competencies. "
        "Return as a comma-separated list. Include both hard skills (e.g., 'Cooking', 'Food Safety') "
        "and soft skills (e.g., 'Team Leadership', 'Communication') if mentioned.\n\n"
        "4. CERTIFICATIONS: Extract any certifications, licenses, or credentials mentioned. "
        "Return as a comma-separated list. If none are mentioned, return empty string.\n\n"
        "5. EXPERIENCE: Extract work experience, job history, or career background mentioned. "
        "Format as a brief description. If specific jobs/companies are mentioned, include them. "
        "If no specific experience is mentioned, create a brief summary based on what they said about their background.\n\n"
        "IMPORTANT RULES:\n"
        "- Only extract information EXPLICITLY mentioned in the transcript\n"
        "- Do NOT invent or assume any information\n"
        "- If something is not mentioned, leave that field empty or create a reasonable summary based on what IS mentioned\n"
        "- Be accurate and professional\n\n"
        "Return your response in the following JSON format (no markdown, just raw JSON):\n"
        '{\n'
        '  "headline": "short headline here",\n'
        '  "summary": "professional summary paragraph here",\n'
        '  "skills": "skill1, skill2, skill3",\n'
        '  "certifications": "cert1, cert2" or "",\n'
        '  "experience": "experience description here"\n'
        '}\n\n'
        f"Transcript:\n\n{transcript}"
    )
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        data = json.loads(response_text)
        
        # Normalize the data
        result = {
            "headline": str(data.get("headline", "")).strip()[:140],
            "summary": str(data.get("summary", "")).strip()[:2000],
            "skills": [s.strip() for s in str(data.get("skills", "")).split(",") if s.strip()],
            "certifications": [c.strip() for c in str(data.get("certifications", "")).split(",") if c.strip()],
            "experience": str(data.get("experience", "")).strip()[:5000],
        }
        
        logger.info(
            "Profile data extracted - headline: %d chars, skills: %d, certs: %d, experience: %d chars",
            len(result["headline"]), len(result["skills"]), len(result["certifications"]), len(result["experience"])
        )
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON from AI response: %s. Response: %s", e, response_text[:500])
        # Fallback: return basic structure with summary only
        return {
            "headline": "",
            "summary": _summarize_transcript(transcript),
            "skills": [],
            "certifications": [],
            "experience": "",
        }
    except Exception as e:
        logger.exception("Failed to extract profile data: %s", e)
        # Fallback: return basic structure with summary only
        return {
            "headline": "",
            "summary": _summarize_transcript(transcript),
            "skills": [],
            "certifications": [],
            "experience": "",
        }


def transcribe_and_summarize(video_path: str | Path) -> tuple[str, str]:
    """
    Use Google Gemini API to:
    1) Transcribe the spoken words in the video (real transcript).
    2) Generate a concise professional summary based ONLY on that transcript.
    
    Handles video chunking automatically if video is longer than 2 minutes.
    
    Returns (transcript, summary_text).
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(path)

    logger = getattr(current_app, "logger", logging.getLogger(__name__))

    # Prepare video file(s) - may split into chunks
    video_chunks, has_temp_files = _prepare_video_for_gemini(path)
    
    try:
        # Transcribe each chunk
        transcripts = []
        for i, chunk_path in enumerate(video_chunks):
            logger.info("Processing chunk %d/%d", i + 1, len(video_chunks))
            chunk_transcript = _transcribe_video_chunk(chunk_path)
            transcripts.append(chunk_transcript)
        
        # Combine all transcripts
        full_transcript = "\n\n".join(transcripts)
        logger.info("Combined transcript length: %d chars", len(full_transcript))
        
        # Generate summary from combined transcript
        summary_text = _summarize_transcript(full_transcript)
        
        return full_transcript, summary_text
        
    finally:
        # Clean up temporary chunk files
        if has_temp_files:
            for chunk in video_chunks:
                if chunk != path and chunk.exists():  # Don't delete original
                    try:
                        chunk.unlink()
                        logger.info("Cleaned up temporary chunk: %s", chunk)
                    except Exception as e:
                        logger.warning("Failed to delete chunk %s: %s", chunk, e)


def transcribe_and_extract_profile(video_path: str | Path) -> tuple[str, dict[str, str | list[str]]]:
    """
    Use Google Gemini API to:
    1) Transcribe the spoken words in the video (real transcript).
    2) Extract all profile fields (headline, summary, skills, certifications, experience).
    
    Handles video chunking automatically if video is longer than 2 minutes.
    
    Returns (transcript, profile_data_dict).
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(path)

    logger = getattr(current_app, "logger", logging.getLogger(__name__))

    # Prepare video file(s) - may split into chunks
    video_chunks, has_temp_files = _prepare_video_for_gemini(path)
    
    try:
        # Transcribe each chunk
        transcripts = []
        for i, chunk_path in enumerate(video_chunks):
            logger.info("Processing chunk %d/%d", i + 1, len(video_chunks))
            chunk_transcript = _transcribe_video_chunk(chunk_path)
            transcripts.append(chunk_transcript)
        
        # Combine all transcripts
        full_transcript = "\n\n".join(transcripts)
        logger.info("Combined transcript length: %d chars", len(full_transcript))
        
        # Extract all profile data from combined transcript
        profile_data = _extract_profile_data(full_transcript)
        
        return full_transcript, profile_data
        
    finally:
        # Clean up temporary chunk files
        if has_temp_files:
            for chunk in video_chunks:
                if chunk != path and chunk.exists():  # Don't delete original
                    try:
                        chunk.unlink()
                        logger.info("Cleaned up temporary chunk: %s", chunk)
                    except Exception as e:
                        logger.warning("Failed to delete chunk %s: %s", chunk, e)


def transcribe_and_summarize_safe(video_path: str | Path) -> tuple[str | None, str | None]:
    """
    Wrapper that never raises in production routes.
    Logs any error and returns (None, None) on failure.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    try:
        return transcribe_and_summarize(video_path)
    except FileNotFoundError as exc:
        logger.error("Video file not found: %s", exc)
        return None, None
    except RuntimeError as exc:
        error_msg = str(exc)
        if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
            logger.error("Video processing failed (ffmpeg/ffprobe issue): %s", exc)
        elif "GEMINI_API_KEY" in error_msg:
            logger.error("Gemini API key not configured: %s", exc)
        else:
            logger.error("Runtime error during transcription: %s", exc)
        return None, None
    except google_exceptions.GoogleAPIError as exc:
        error_str = str(exc)
        logger.error("Google Gemini API error: %s", error_str)
        return None, None
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to transcribe/summarize video %s: %s", video_path, exc)
        return None, None


def transcribe_and_extract_profile_safe(video_path: str | Path) -> tuple[str | None, dict[str, str | list[str]] | None]:
    """
    Wrapper that never raises in production routes.
    Logs any error and returns (None, None) on failure.
    """
    logger = getattr(current_app, "logger", logging.getLogger(__name__))
    try:
        return transcribe_and_extract_profile(video_path)
    except FileNotFoundError as exc:
        logger.error("Video file not found: %s", exc)
        return None, None
    except RuntimeError as exc:
        error_msg = str(exc)
        if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
            logger.error("Video processing failed (ffmpeg/ffprobe issue): %s", exc)
        elif "GEMINI_API_KEY" in error_msg:
            logger.error("Gemini API key not configured: %s", exc)
        else:
            logger.error("Runtime error during transcription: %s", exc)
        return None, None
    except google_exceptions.GoogleAPIError as exc:
        error_str = str(exc)
        logger.error("Google Gemini API error: %s", error_str)
        return None, None
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to transcribe/extract profile from video %s: %s", video_path, exc)
        return None, None
