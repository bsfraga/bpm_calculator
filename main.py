import os
import json
import warnings
import librosa
import subprocess
import logging
import re
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
import traceback

BPM_RESULTS_JSON = "bpm_results.json"
warnings.simplefilter(action='ignore')
logging.basicConfig(filename='bpm.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

def sanitize_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename.title().replace(" ", ""))

def get_max_workers():
    return multiprocessing.cpu_count() * 2 + 1

def download_audio(music_name, is_url=False):
    current_directory = os.getcwd()
    query = music_name if is_url else f"ytsearch:{music_name}"
    output_template = os.path.join(current_directory, "%(id)s.%(ext)s")
    cmd_download = ['yt-dlp', '--extract-audio', '--audio-format', 'mp3', '-f', 'bestaudio/best', '--output', output_template, '--print-json', query]
    result = subprocess.run(cmd_download, stdout=subprocess.PIPE, text=True)
    video_info = json.loads(result.stdout)
    file_path = os.path.join(current_directory, f"{video_info['id']}.mp3")
    return file_path, video_info['webpage_url'], video_info['id']

def calculate_bpm(audio_file):
    y, sr = librosa.load(audio_file, sr=44100)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    bpm, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
    return round(bpm, 2)

def load_existing_bpm_data():
    try:
        with open(BPM_RESULTS_JSON, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logging.error("Failed to parse existing JSON BPM data.")
        return []

def remove_mp3_files():
    for filename in os.listdir('.'):
        if filename.endswith('.mp3'):
            os.remove(filename)

def threaded_download_and_calculate(music_list):
    existing_bpm_data = load_existing_bpm_data()
    to_process = []
    to_reuse = []
    for title in music_list:
        if any(title == data.get('imported_title') for data in existing_bpm_data):
            to_reuse.append(title)
        else:
            to_process.append(title)
    btn_calculate.config(state=tk.DISABLED)
    downloaded_files = []
    if to_process:
        with ThreadPoolExecutor(max_workers=get_max_workers()) as executor:
            downloaded_files = list(executor.map(download_audio, to_process))
    valid_files = [x[0] for x in downloaded_files if x[0] and os.path.exists(x[0])]
    bpm_results = []
    if valid_files:
        with ThreadPoolExecutor(max_workers=get_max_workers()) as executor:
            bpm_results = list(executor.map(calculate_bpm, valid_files))
    bpm_json_results = []
    for (title_file, title_url, video_id), imported_title, bpm in zip(downloaded_files, to_process, bpm_results):
        if bpm is not None and title_file in valid_files:
            bpm_json_results.append({
                "title": os.path.basename(os.path.splitext(title_file)[0]),
                "imported_title": imported_title,
                "url": title_url,
                "video_id": video_id,
                "bpm": float(bpm)
            })
    reused_bpm_data = [data for data in existing_bpm_data if data.get('imported_title') in to_reuse]
    all_bpm_results = bpm_json_results + reused_bpm_data
    bpms = [item['bpm'] for item in all_bpm_results]
    avg_bpm = sum(bpms) / len(bpms) if bpms else 0
    avg_bpm_var.set(f"Average BPM: {avg_bpm:.2f}")
    with open(BPM_RESULTS_JSON, 'w') as jf:
        json.dump(all_bpm_results, jf, indent=4)
    results_var.set(json.dumps(all_bpm_results, indent=4))
    progress_var.set(100)
    remove_mp3_files()
    elapsed_time = time.time() - start_time
    elapsed_label.config(text=f"Elapsed time: {elapsed_time:.2f} seconds")
    items_processed.set(f"Items Processed: {len(all_bpm_results)}")
    btn_calculate.config(state=tk.NORMAL)

def import_txt_file():
    filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filepath:
        with open(filepath, 'r') as f:
            music_input.delete('1.0', tk.END)
            music_input.insert(tk.END, f.read())

def clear_text_fields():
    music_input.delete('1.0', tk.END)
    bpm_output.delete('1.0', tk.END)
    items_mapped.set("Items Mapped: 0")
    items_processed.set("Items Processed: 0")

def clear_results():
    if os.path.exists(BPM_RESULTS_JSON):
        with open(BPM_RESULTS_JSON, 'w') as f:
            f.write("")
    bpm_output.delete('1.0', tk.END)
    avg_bpm_var.set("Average BPM: 0")
    results_var.set("")

def get_music_list_and_start_thread():
    global start_time
    start_time = time.time()
    progress_var.set(0)
    music_list = music_input.get("1.0", tk.END).splitlines()
    music_list = [x.strip() for x in music_list if x.strip()]
    items_mapped.set(f"Items Mapped: {len(music_list)}")
    threading.Thread(target=threaded_download_and_calculate, args=(music_list,)).start()

def update_text_colors():
    bpm_data = []
    try:
        with open(BPM_RESULTS_JSON, 'r') as f:
            content = f.read()
            if content:
                bpm_data = json.loads(content)
        music_list = music_input.get("1.0", tk.END).splitlines()
        for i, line in enumerate(music_list):
            found = any(line in bpm_result.get('imported_title', '')
                        for bpm_result in bpm_data)
            color = "green" if found else "red"
            tag_name = f"color{i}"
            music_input.tag_add(tag_name, f"{i+1}.0", f"{i+1}.end")
            music_input.tag_config(tag_name, foreground=color)
    except Exception as e:
        logging.error(f"Failed to update text colors: {e}")
        logging.error(traceback.format_exc())

def update_ui():
    bpm_output.delete('1.0', tk.END)
    json_str = results_var.get().strip()
    if json_str:
        try:
            bpm_data = json.loads(json_str)
            formatted_output = ""
            for idx, item in enumerate(bpm_data):
                line_position = idx + 1
                bpm = item.get('bpm', 'N/A')
                formatted_output += f"[{line_position}] - {bpm}\n"
            bpm_output.insert(tk.END, formatted_output)
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON")
            logging.error(traceback.format_exc())
    progress_bar["value"] = progress_var.get()
    update_text_colors()
    root.after(1000, update_ui)

def run_gui():
    global root, progress_var, results_var, items_mapped, items_processed, btn_calculate, avg_bpm_var, elapsed_label, music_input, bpm_output, progress_bar
    root = tk.Tk()
    root.title("BPM Calculator")
    progress_var = tk.IntVar()
    results_var = tk.StringVar()
    results_var.set("")
    items_mapped = tk.StringVar()
    items_mapped.set("Items Mapped: 0")
    items_processed = tk.StringVar()
    items_processed.set("Items Processed: 0")
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    left_frame = ttk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    music_label = ttk.Label(left_frame, text="Musics", font=("Helvetica", 12, 'bold'))
    music_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
    music_input = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, width=40, height=10)
    music_input.grid(row=1, column=0, sticky=(tk.W, tk.E))
    btn_import = ttk.Button(left_frame, text="Import", command=import_txt_file)
    btn_import.grid(row=2, column=0, sticky=tk.W)
    btn_clear = ttk.Button(left_frame, text="Clear", command=clear_text_fields)
    btn_clear.grid(row=2, column=0, sticky=tk.N)
    btn_result_clear = ttk.Button(left_frame, text="Clear Results", command=clear_results)
    btn_result_clear.grid(row=2, column=0, sticky=tk.E)
    btn_calculate = ttk.Button(left_frame, text="Download and Calculate BPM", command=get_music_list_and_start_thread)
    btn_calculate.grid(row=3, column=0, sticky=tk.W)
    progress_bar = ttk.Progressbar(left_frame, variable=progress_var, orient=tk.HORIZONTAL, length=100, mode="determinate")
    progress_bar.grid(row=3, column=0, sticky=tk.E)
    elapsed_label = ttk.Label(left_frame, text="Elapsed time: 0.00 seconds", font=("Helvetica", 10))
    elapsed_label.grid(row=4, column=0, sticky=tk.W)
    mapped_label = ttk.Label(left_frame, textvariable=items_mapped, font=("Helvetica", 10))
    mapped_label.grid(row=5, column=0, sticky=tk.W)
    processed_label = ttk.Label(left_frame, textvariable=items_processed, font=("Helvetica", 10))
    processed_label.grid(row=6, column=0, sticky=tk.W)
    right_frame = ttk.Frame(main_frame)
    right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
    bpm_label = ttk.Label(right_frame, text="Calculated BPMs", font=("Helvetica", 12, 'bold'))
    bpm_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
    bpm_output = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, width=15, height=10)
    bpm_output.grid(row=1, column=0, rowspan=3, sticky=(tk.W, tk.E))
    avg_bpm_var = tk.StringVar()
    avg_bpm_var.set("Average BPM: 0")
    avg_bpm_label = ttk.Label(right_frame, textvariable=avg_bpm_var, font=("Helvetica", 10))
    avg_bpm_label.grid(row=4, column=0, sticky=tk.W)
    root.after(1000, update_ui)
    root.mainloop()

if __name__ == "__main__":
    run_gui()
