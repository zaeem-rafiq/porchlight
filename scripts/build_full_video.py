"""
Full video assembly script for Porchlight 1080p demo.
Renders all scene clips with synchronized narration and concatenates
into docs/media/porchlight-demo.mp4.
"""

import os
import subprocess
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

SCENE_CONFIG = [
    {
        "scene_id": "scene_1",
        "shots": [
            ("build_media/frames/shot_1a.png", 13.0),
            ("build_media/frames/shot_1b.png", None)  # None means remainder of audio
        ],
        "audio": "build_media/audio/scene_1.mp3"
    },
    {
        "scene_id": "scene_2",
        "shots": [
            ("build_media/frames/shot_2a.png", 18.0),
            ("build_media/frames/shot_2b.png", None)
        ],
        "audio": "build_media/audio/scene_2.mp3"
    },
    {
        "scene_id": "scene_3",
        "shots": [
            ("build_media/frames/shot_3a.png", 13.5),
            ("build_media/frames/shot_3b.png", None)
        ],
        "audio": "build_media/audio/scene_3.mp3"
    },
    {
        "scene_id": "scene_4",
        "shots": [
            ("build_media/frames/shot_4a.png", 9.5),
            ("build_media/frames/shot_4b.png", None)
        ],
        "audio": "build_media/audio/scene_4.mp3"
    },
    {
        "scene_id": "scene_5",
        "shots": [
            ("build_media/frames/shot_5a.png", 11.5),
            ("build_media/frames/shot_5b.png", None)
        ],
        "audio": "build_media/audio/scene_5.mp3"
    },
    {
        "scene_id": "scene_6",
        "shots": [
            ("build_media/frames/shot_6a.png", 10.0),
            ("build_media/frames/shot_6b.png", None)
        ],
        "audio": "build_media/audio/scene_6.mp3"
    },
    {
        "scene_id": "scene_7",
        "shots": [
            ("build_media/frames/shot_7a.png", 10.0),
            ("build_media/frames/shot_7b.png", None)
        ],
        "audio": "build_media/audio/scene_7.mp3"
    },
    {
        "scene_id": "scene_8",
        "shots": [
            ("build_media/frames/shot_8a.png", 14.0),
            ("build_media/frames/shot_8b.png", None)
        ],
        "audio": "build_media/audio/scene_8.mp3"
    },
    {
        "scene_id": "scene_9",
        "shots": [
            ("build_media/frames/shot_9a.png", None)
        ],
        "audio": "build_media/audio/scene_9.mp3"
    },
]

def get_duration(file_path):
    cmd = [FFMPEG, "-i", file_path]
    res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    for line in res.stderr.splitlines():
        if "Duration:" in line:
            parts = line.split("Duration:")[1].split(",")[0].strip()
            h, m, s = parts.split(":")
            return float(h) * 3600 + float(m) * 60 + float(s)
    return 0.0

def build_scene_clip(cfg, out_dir="build_media/clips"):
    os.makedirs(out_dir, exist_ok=True)
    scene_id = cfg["scene_id"]
    audio_path = cfg["audio"]
    total_audio_dur = get_duration(audio_path)
    print(f"\n--- Building {scene_id} (Audio: {total_audio_dur:.2f}s) ---")
    
    shots = cfg["shots"]
    shot_clips = []
    
    # Calculate durations
    dur_assigned = sum(d for _, d in shots if d is not None)
    for idx, (img_path, dur) in enumerate(shots):
        if dur is None:
            shot_dur = max(1.0, total_audio_dur - dur_assigned)
        else:
            shot_dur = dur
        
        shot_clip = f"{out_dir}/{scene_id}_shot_{idx}.mp4"
        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-t", f"{shot_dur:.3f}",
            "-i", img_path,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            shot_clip
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        shot_clips.append(shot_clip)
        print(f"  Shot {idx} ({img_path}): {shot_dur:.2f}s -> {shot_clip}")

    # Merge shots and audio
    scene_out = f"{out_dir}/{scene_id}.mp4"
    if len(shot_clips) == 1:
        cmd = [
            FFMPEG, "-y",
            "-i", shot_clips[0],
            "-i", audio_path,
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            scene_out
        ]
    else:
        # Filter complex concat
        inputs = []
        for sc in shot_clips:
            inputs.extend(["-i", sc])
        inputs.extend(["-i", audio_path])
        
        filter_str = "".join([f"[{i}:v]" for i in range(len(shot_clips))]) + f"concat=n={len(shot_clips)}:v=1:a=0[v]"
        audio_idx = len(shot_clips)
        cmd = [
            FFMPEG, "-y",
            *inputs,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", f"{audio_idx}:a",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            scene_out
        ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    actual_scene_dur = get_duration(scene_out)
    print(f"  Scene Clip {scene_out} created (Duration: {actual_scene_dur:.2f}s)")
    return scene_out

def main():
    clips = []
    for cfg in SCENE_CONFIG:
        clip_path = build_scene_clip(cfg)
        clips.append(clip_path)
    
    # Write concat demuxer file
    concat_list_path = "build_media/clips/concat_list.txt"
    with open(concat_list_path, "w") as f:
        for c in clips:
            abs_c = os.path.abspath(c).replace("\\", "/")
            f.write(f"file '{abs_c}'\n")

    out_final = "docs/media/porchlight-demo.mp4"
    os.makedirs(os.path.dirname(out_final), exist_ok=True)
    
    print("\n--- Concatenating all scenes into final video ---")
    cmd = [
        FFMPEG, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        out_final
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    final_dur = get_duration(out_final)
    file_size_mb = os.path.getsize(out_final) / (1024 * 1024)
    print("\n" + "=" * 60)
    print(f"FINAL VIDEO CREATED: {out_final}")
    print(f"Total Duration: {final_dur:.2f}s ({final_dur/60:.2f} minutes)")
    print(f"File Size: {file_size_mb:.2f} MB")
    print("=" * 60)

if __name__ == "__main__":
    main()
