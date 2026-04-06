"""FFmpeg-based video rendering engine.

Composes a final MP4 from:
  - Video clips (concatenated with optional transitions)
  - Voiceover audio track
  - BGM audio track (mixed at lower volume)
  - Subtitle burn-in (ASS format)

This module is a pure rendering engine — it operates on local file paths only.
The caller (API layer) is responsible for downloading assets from MinIO to a
temp directory and uploading the output back to MinIO.

Usage:
    renderer = FFmpegRenderer(work_dir="/tmp/render_xxx")
    output_path = await renderer.render(plan)
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models for the render plan
# ---------------------------------------------------------------------------


@dataclass
class RenderClip:
    """A single video clip in the render plan."""
    clip_id: str
    file_path: str          # Local path to the video file
    start_ms: int = 0       # Timeline start (used for ordering)
    end_ms: int = 0         # Timeline end
    trim_start_ms: int = 0  # Trim from beginning of source file
    speed: float = 1.0


@dataclass
class RenderAudioTrack:
    """An audio track (voiceover or BGM) in the render plan."""
    track_type: str          # "voiceover" or "bgm"
    file_path: str           # Local path to the audio file
    volume: float = 1.0      # Volume multiplier (0.0 - 1.0)
    start_ms: int = 0
    end_ms: int = 0


@dataclass
class RenderSubtitle:
    """A subtitle segment for burn-in."""
    start_ms: int
    end_ms: int
    text: str


@dataclass
class RenderTransition:
    """A transition between two clips."""
    from_clip_id: str
    to_clip_id: str
    type: str = "fade"       # fade, dissolve, wipe
    duration_ms: int = 300


@dataclass
class RenderPlan:
    """Complete render plan — everything needed to produce the final video."""
    video_clips: list[RenderClip] = field(default_factory=list)
    audio_tracks: list[RenderAudioTrack] = field(default_factory=list)
    subtitles: list[RenderSubtitle] = field(default_factory=list)
    transitions: list[RenderTransition] = field(default_factory=list)
    resolution: str = "1080p"      # 720p, 1080p, 2k, 4k
    format: str = "mp4"            # mp4, mov
    burn_subtitle: bool = True
    duration_ms: int = 0           # Expected total duration


# Resolution map: name -> (width, height)
RESOLUTION_MAP = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "2k": (2560, 1440),
    "4k": (3840, 2160),
}


class FFmpegRenderer:
    """Renders a final video from a RenderPlan using FFmpeg.

    The renderer uses a work directory for intermediate files. The caller
    should clean up the work directory after retrieving the output.
    """

    def __init__(self, work_dir: str | None = None, ffmpeg_bin: str = "ffmpeg"):
        self.work_dir = Path(work_dir or tempfile.mkdtemp(prefix="render_"))
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_bin = ffmpeg_bin

    async def render(self, plan: RenderPlan) -> str:
        """Execute the full render pipeline.

        Returns the path to the final output file.

        Steps:
          1. Concatenate video clips
          2. Generate subtitle file (ASS)
          3. Mix audio tracks
          4. Compose everything into final output
        """
        if not plan.video_clips:
            raise ValueError("No video clips in render plan")

        width, height = RESOLUTION_MAP.get(plan.resolution, (1920, 1080))

        # Step 1: Concatenate video clips
        concat_path = await self._concat_videos(plan.video_clips, width, height)

        # Step 2: Generate subtitle file if needed
        subtitle_path: str | None = None
        if plan.burn_subtitle and plan.subtitles:
            subtitle_path = self._generate_ass_subtitles(plan.subtitles, width, height)

        # Step 3: Build final composite command
        output_ext = plan.format if plan.format in ("mp4", "mov") else "mp4"
        output_path = str(self.work_dir / f"output.{output_ext}")

        await self._compose_final(
            video_path=concat_path,
            audio_tracks=plan.audio_tracks,
            subtitle_path=subtitle_path,
            output_path=output_path,
            width=width,
            height=height,
        )

        if not os.path.exists(output_path):
            raise RuntimeError(f"FFmpeg render failed: output file not created at {output_path}")

        file_size = os.path.getsize(output_path)
        logger.info("Render complete: %s (%.1f MB)", output_path, file_size / 1024 / 1024)

        return output_path

    async def extract_cover(self, video_path: str, timestamp_ms: int = 1000) -> str:
        """Extract a cover frame from the video at the given timestamp.

        Returns path to the output PNG file.
        """
        output_path = str(self.work_dir / "cover.png")
        timestamp_sec = timestamp_ms / 1000.0

        cmd = [
            self.ffmpeg_bin, "-y",
            "-ss", f"{timestamp_sec:.3f}",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ]

        await self._run_ffmpeg(cmd, "extract_cover")
        return output_path

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    async def _concat_videos(
        self, clips: list[RenderClip], width: int, height: int
    ) -> str:
        """Concatenate video clips using the FFmpeg concat demuxer.

        All clips are first scaled/padded to a uniform resolution,
        then concatenated via a file list.
        """
        if len(clips) == 1:
            # Single clip — just scale it
            scaled_path = str(self.work_dir / "scaled_0.mp4")
            await self._scale_video(clips[0].file_path, scaled_path, width, height)
            return scaled_path

        # Scale each clip to uniform resolution
        scaled_paths: list[str] = []
        for i, clip in enumerate(clips):
            scaled = str(self.work_dir / f"scaled_{i}.mp4")
            await self._scale_video(clip.file_path, scaled, width, height)
            scaled_paths.append(scaled)

        # Write concat list file
        concat_list = str(self.work_dir / "concat_list.txt")
        with open(concat_list, "w") as f:
            for path in scaled_paths:
                f.write(f"file '{path}'\n")

        output = str(self.work_dir / "concat.mp4")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            output,
        ]

        await self._run_ffmpeg(cmd, "concat_videos")
        return output

    async def _scale_video(
        self, input_path: str, output_path: str, width: int, height: int
    ) -> None:
        """Scale a video to target resolution, padding if needed to preserve aspect ratio."""
        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", input_path,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                   f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        await self._run_ffmpeg(cmd, f"scale_video -> {output_path}")

    def _generate_ass_subtitles(
        self, subtitles: list[RenderSubtitle], width: int, height: int
    ) -> str:
        """Generate an ASS subtitle file from subtitle segments."""
        output_path = str(self.work_dir / "subtitles.ass")

        # ASS header
        ass_content = f"""[Script Info]
Title: AI Video Studio Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,30,30,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        for sub in subtitles:
            start = _ms_to_ass_time(sub.start_ms)
            end = _ms_to_ass_time(sub.end_ms)
            # Escape special ASS characters
            text = sub.text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
            ass_content += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        return output_path

    async def _compose_final(
        self,
        video_path: str,
        audio_tracks: list[RenderAudioTrack],
        subtitle_path: str | None,
        output_path: str,
        width: int,
        height: int,
    ) -> None:
        """Compose the final output: overlay audio tracks and burn subtitles.

        Strategy:
          - Start with the concatenated video as base
          - Mix in voiceover and BGM audio tracks
          - Burn subtitles using the ASS filter
        """
        inputs = ["-i", video_path]
        filter_parts: list[str] = []
        audio_inputs: list[str] = []

        # Add audio track inputs
        input_idx = 1  # 0 is the video
        for track in audio_tracks:
            inputs.extend(["-i", track.file_path])
            # Apply volume filter
            audio_inputs.append(
                f"[{input_idx}:a]volume={track.volume:.2f}[a{input_idx}]"
            )
            input_idx += 1

        # Build video filter
        video_filter = f"[0:v]"
        if subtitle_path:
            video_filter += f"ass='{subtitle_path}'"
        else:
            video_filter += "null"
        video_filter += "[vout]"
        filter_parts.append(video_filter)

        # Build audio mix
        if audio_inputs:
            filter_parts.extend(audio_inputs)

            # Mix all audio sources: original video audio (if any) + added tracks
            mix_inputs = "[0:a]" if True else ""  # Always try the video's audio
            for i in range(1, input_idx):
                mix_inputs += f"[a{i}]"

            num_audio = input_idx  # video audio + extra tracks
            filter_parts.append(
                f"{mix_inputs}amix=inputs={num_audio}:duration=longest:dropout_transition=2[aout]"
            )
            audio_map = ["-map", "[aout]"]
        else:
            # No extra audio — just use the video's audio stream
            audio_map = ["-map", "0:a?"]

        # Combine filter complex
        filter_complex = ";".join(filter_parts)

        cmd = [
            self.ffmpeg_bin, "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            *audio_map,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-r", "30",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ]

        await self._run_ffmpeg(cmd, "compose_final")

    async def _run_ffmpeg(self, cmd: list[str], step_name: str) -> None:
        """Run an FFmpeg command asynchronously.

        Raises RuntimeError if the process exits with a non-zero code.
        """
        logger.info("FFmpeg [%s]: %s", step_name, " ".join(cmd))

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            stderr_text = stderr.decode(errors="replace")[-2000:]
            logger.error(
                "FFmpeg [%s] failed (code=%d): %s",
                step_name, proc.returncode, stderr_text,
            )
            raise RuntimeError(
                f"FFmpeg {step_name} failed (exit code {proc.returncode}): {stderr_text}"
            )

        logger.debug("FFmpeg [%s] completed successfully", step_name)

    def cleanup(self) -> None:
        """Remove the work directory and all intermediate files."""
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir, ignore_errors=True)


def _ms_to_ass_time(ms: int) -> str:
    """Convert milliseconds to ASS time format: H:MM:SS.cc (centiseconds)."""
    total_seconds = ms / 1000.0
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    return f"{hours}:{minutes:02d}:{seconds:05.2f}"
