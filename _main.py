import os
import json
import warnings
import librosa
import subprocess
import logging
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import traceback
import re

warnings.simplefilter(action='ignore')

logging.basicConfig(filename='bpm.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')


def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename)


def get_max_workers():
    return multiprocessing.cpu_count() * 2 + 1


def download_audio(music_name, is_url=False):
    try:
        current_directory = os.getcwd()

        if is_url:
            query = music_name
        else:
            query = f"ytsearch:{music_name}"

        output_template = os.path.join(current_directory, "%(title)s.%(ext)s")
        cmd_download = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '-f', 'bestaudio/best',
            '--output', output_template,
            '--print-json',
            query
        ]
        result = subprocess.run(cmd_download, stdout=subprocess.PIPE, text=True)
        video_info = json.loads(result.stdout)
        sanitized_title = sanitize_filename(video_info['title'])
        file_path = os.path.join(current_directory, f"{sanitized_title}.mp3")
        
        print(f"Downloaded File Path: {file_path}")  # Debugging line

        return (file_path, video_info['webpage_url'])


    except Exception as e:
        logging.error(f"Error downloading {music_name}: {e}")
        logging.error(traceback.format_exc())
        return (None, None)


def calculate_bpm(audio_file):
    try:
        print(f"Trying to load file from path: {audio_file}")  # Debugging line
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"File {audio_file} not found")

        y, sr = librosa.load(audio_file, sr=44100)

        if y is None or len(y) == 0:
            raise ValueError("Audio data is empty")

        if y.dtype != 'float32':
            y = y.astype('float32')

        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        bpm, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        
        return round(bpm, 2)
    except Exception as e:
        logging.error(f"Error calculating BPM for {audio_file}: {e}")
        logging.error(traceback.format_exc())
        return None

if __name__ == '__main__':
    try:
        with open('music_list.txt', 'r') as f:
            music_entries = f.readlines()
        music_entries = [x.strip() for x in music_entries]
    except Exception as e:
        logging.error(f"Error reading music_list.txt: {e}")
        logging.error(traceback.format_exc())
        raise

    downloaded_files = []
    bpm_results = []
    bpm_json_results = []

    # Download all the files first
    with ThreadPoolExecutor(max_workers=get_max_workers()) as executor:
        downloaded_files = list(executor.map(download_audio, music_entries))

    # Then process them
    with ThreadPoolExecutor(max_workers=get_max_workers()) as executor:
        bpm_results = list(executor.map(calculate_bpm, [x[0] for x in downloaded_files if x[0]]))

    # Save results and errors
    bpm_errors = []
    try:
        with open('bpm_results.json', 'w') as jf:
            for (title_file, title_url), bpm in zip(downloaded_files, bpm_results):
                if bpm is not None:  # No error in calculating bpm
                    title_text = os.path.basename(os.path.splitext(title_file)[0])
                    bpm_json_results.append({"title": title_text, "url": title_url, "bpm": float(bpm)})
                else:  # Error in calculating bpm
                    bpm_errors.append(f"BPM calculation failed for {title_file}")
                    logging.error(f"BPM calculation failed for {title_file}")

            json.dump(bpm_json_results, jf)

        if bpm_errors:
            with open('bpm_errors.txt', 'w') as ef:
                for error in bpm_errors:
                    ef.write(f"{error}\n")

    except Exception as e:
        logging.error(f"Error saving results to bpm_results.json: {e}")
        logging.error(traceback.format_exc())
        raise

    # Remove all downloaded files
    for entry in os.listdir():
        if entry.endswith('.mp3'):
            os.remove(entry)