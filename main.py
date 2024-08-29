import os
import subprocess
import moviepy.editor as mp
import whisper
from datetime import timedelta

# Load Whisper model
model = whisper.load_model("base")

def time_to_str(seconds):
    return str(timedelta(seconds=int(seconds))).split('.')[0]

def time_to_srt_format(seconds):
    td = timedelta(seconds=seconds)
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = td.microseconds // 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def process_video(video_path, output_folder):
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_output_folder = os.path.join(output_folder, video_name)
    os.makedirs(video_output_folder, exist_ok=True)

    output_audio = os.path.join(video_output_folder, "audio.mp3")
    output_file = os.path.join(video_output_folder, f"{video_name}-transcription.txt")
    output_srt = os.path.join(video_output_folder, f"{video_name}-subtitles.srt")
    chunks_folder = os.path.join(video_output_folder, "audio_chunks")
    srt_chunks_folder = os.path.join(video_output_folder, "srt_audio_chunks")

    # Extract audio from video
    clip = mp.VideoFileClip(video_path)
    clip.audio.write_audiofile(output_audio)

    # Get total duration of the audio
    total_duration = clip.duration

    # Create chunks folders
    os.makedirs(chunks_folder, exist_ok=True)
    os.makedirs(srt_chunks_folder, exist_ok=True)

    # Clear the output files
    open(output_file, "w").close()
    open(output_srt, "w").close()

    # Split the audio into 1-minute chunks for transcription
    transcription_chunk_duration = 60
    command = [
        "ffmpeg", "-i", output_audio, "-f", "segment", "-segment_time", str(transcription_chunk_duration),
        "-c", "copy", f"{chunks_folder}/chunk%03d.wav"
    ]
    subprocess.run(command)

    # Split the audio into 4-second chunks for SRT
    # srt_chunk_duration = 4
    # command = [
    #     "ffmpeg", "-i", output_audio, "-f", "segment", "-segment_time", str(srt_chunk_duration),
    #     "-c", "copy", f"{srt_chunks_folder}/chunk%03d.wav"
    # ]
    # subprocess.run(command)

    # Process 1-minute chunks for transcription
    total_chunks = len([name for name in os.listdir(chunks_folder) if name.startswith("chunk")])
    for i in range(total_chunks):
        chunk_file = f"{chunks_folder}/chunk{i:03d}.wav"
        start_time = i * transcription_chunk_duration
        end_time = min((i + 1) * transcription_chunk_duration, total_duration)
        
        try:
            result = model.transcribe(chunk_file)
            with open(output_file, "a") as f:
                f.write(f"{time_to_str(start_time)} - {time_to_str(end_time)}: {result['text']}\n\n")
        except Exception as e:
            print(f"Error processing {chunk_file}: {str(e)}")
            with open(output_file, "a") as f:
                f.write(f"{time_to_str(start_time)} - {time_to_str(end_time)}: [Transcription failed]\n\n")
        
        os.remove(chunk_file)

    # Process 4-second chunks for SRT
    # total_srt_chunks = len([name for name in os.listdir(srt_chunks_folder) if name.startswith("chunk")])
    # subtitle_index = 1
    # for i in range(total_srt_chunks):
    #     chunk_file = f"{srt_chunks_folder}/chunk{i:03d}.wav"
    #     start_time = i * srt_chunk_duration
    #     end_time = min((i + 1) * srt_chunk_duration, total_duration)
        
    #     try:
    #         result = model.transcribe(chunk_file)
    #         with open(output_srt, "a") as f:
    #             f.write(f"{subtitle_index}\n")
    #             f.write(f"{time_to_srt_format(start_time)} --> {time_to_srt_format(end_time)}\n")
    #             f.write(f"{result['text']}\n\n")
    #         subtitle_index += 1
    #     except Exception as e:
    #         print(f"Error processing SRT chunk {chunk_file}: {str(e)}")
    #         with open(output_srt, "a") as f:
    #             f.write(f"{subtitle_index}\n")
    #             f.write(f"{time_to_srt_format(start_time)} --> {time_to_srt_format(end_time)}\n")
    #             f.write("[Transcription failed]\n\n")
    #         subtitle_index += 1
        
    #     os.remove(chunk_file)

    print(f"Transcription saved to {output_file}")
    # print(f"SRT file saved to {output_srt}")

    # Clean up
    os.remove(output_audio)
    os.rmdir(chunks_folder)
    os.rmdir(srt_chunks_folder)

def main():
    videos_folder = "videos"
    output_folder = "output"

    os.makedirs(output_folder, exist_ok=True)

    for video_file in os.listdir(videos_folder):
        if video_file.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
            video_path = os.path.join(videos_folder, video_file)
            print(f"Processing video: {video_file}")
            process_video(video_path, output_folder)

if __name__ == "__main__":
    main()