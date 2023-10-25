
# BPM Calculator

## Overview

The BPM Calculator is a Python application that calculates the Beats Per Minute (BPM) for a list of music tracks. The application uses a graphical user interface (GUI) built with Tkinter. It downloads audio files from YouTube based on the given search queries, calculates the BPM using the `librosa` library, and displays the results in the GUI.

## Features

- Download audio files from YouTube based on search queries or URLs
- Calculate BPM for downloaded audio files
- Display calculated BPMs and an average BPM in the GUI
- Import a list of search queries from a text file
- Clear input fields and results
- Persistent storage of BPM results in a JSON file
- Multi-threaded downloading and BPM calculation for improved speed

## Dependencies

- Python 3.x
- Tkinter
- librosa
- yt-dlp
- multiprocessing
- concurrent.futures
- json

To install required Python packages, run:

To install the required packages, run the following command:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the script.
2. The GUI will appear, and you can:
   - Manually enter music titles or YouTube URLs in the text field.
   - Import a list of music titles from a `.txt` file by clicking the "Import" button.
3. Click the "Download and Calculate BPM" button to start the process.
4. The calculated BPMs will be displayed on the right side of the GUI.
5. The average BPM of all processed tracks will also be displayed.
6. You can clear the input fields and results using the "Clear" and "Clear Results" buttons respectively.

## Functions

- `sanitize_filename()`: Sanitizes filenames to remove illegal characters.
- `get_max_workers()`: Gets the maximum number of workers for ThreadPoolExecutor.
- `download_audio()`: Downloads an audio file from YouTube.
- `calculate_bpm()`: Calculates BPM for an audio file using `librosa`.
- `load_existing_bpm_data()`: Loads existing BPM data from a JSON file.
- `remove_mp3_files()`: Deletes all `.mp3` files in the current directory.
- `threaded_download_and_calculate()`: Multi-threaded function to download audio and calculate BPM.
- `import_txt_file()`: Imports a list of music titles from a `.txt` file.
- `clear_text_fields()`: Clears the input fields in the GUI.
- `clear_results()`: Clears the results and the JSON file.
- `get_music_list_and_start_thread()`: Gets the list of music titles and starts the calculation thread.
- `update_text_colors()`: Updates the text colors in the GUI based on whether a track has been processed.
- `update_ui()`: Updates the UI periodically.
- `run_gui()`: Main function to run the GUI.

## Notes

- The code logs errors to a file named `bpm.log`.
- The BPM results are stored in a JSON file named `bpm_results.json`.

## Author

This project is authored and maintained by [Bruno Schuster Fraga](mailto:brunofraga_@outlook.com.br). For any questions, feedback, or contributions, please feel free to contact me.


## TODO:

- [X] Add a GitHub Actions workflow to build a executable.
- [ ] Add a functionality to manage playlists as they are downloaded and calculated.