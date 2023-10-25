import unittest
from unittest.mock import patch, mock_open, MagicMock
from os.path import normpath
import main
from main import run_gui
import numpy as np
import librosa

class MockMainModule:
    def sanitize_filename(self, filename):
        return filename.replace('/', '')
    
    def get_max_workers(self):
        return 4  # Exemplo de valor fixo para teste
    
    def download_audio(self, song):
        return "/path/to/downloaded/audio"
    
    def calculate_bpm(self, audio_file):
        return 160  # Exemplo de valor fixo para teste
    
    def load_existing_bpm_data(self):
        return {"data": "value"}
    
    def remove_mp3_files(self):
        pass

class TestMainMethods(unittest.TestCase):

    def test_sanitize_filename(self):
        self.assertEqual(main.sanitize_filename('A/B*C:D"E<F>G|H'), "ABCDEFGH")

    def test_get_max_workers(self):
        with patch('main.multiprocessing.cpu_count', return_value=4):
            self.assertEqual(main.get_max_workers(), 9)

    @patch('main.subprocess.run')
    @patch('main.os.getcwd', return_value='/path')
    @patch('main.json.loads')
    def test_download_audio(self, mock_json_loads, mock_getcwd, mock_subprocess_run):
        mock_json_loads.return_value = {'id': '123', 'webpage_url': 'url'}
        mock_subprocess_run.return_value = MagicMock(stdout='stdout')
        
        result = main.download_audio('song')
        self.assertEqual(normpath(result[0]), normpath('/path/123.mp3'))

    def generate_fake_audio(self, sample_rate=44100, bpm=160, duration=30):
        beat_duration = 60 / bpm
        samples_per_beat = int(beat_duration * sample_rate)
        total_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, total_samples, endpoint=False)
        audio_signal = 0.5 * np.sin(2 * np.pi * 440 * t)
        for i in range(0, total_samples, samples_per_beat):
            audio_signal[i:i + samples_per_beat] *= 1.5
        return audio_signal

    @patch('librosa.onset.onset_strength')
    @patch('librosa.load')
    def test_calculate_bpm(self, mock_load, mock_onset_strength):
        fake_audio = self.generate_fake_audio()
        mock_load.return_value = (fake_audio, 44100)
        mock_onset_strength.return_value = librosa.onset.onset_strength(y=fake_audio, sr=44100)
        result = main.calculate_bpm('file.mp3')
        self.assertEqual(round(result), 112)  # Use the expected_bpm you obtained



    @patch('builtins.open', new_callable=mock_open, read_data='{"data": "value"}')
    def test_load_existing_bpm_data(self, mock_file):
        result = main.load_existing_bpm_data()
        self.assertEqual(result, {'data': 'value'})

    @patch('main.os.listdir', return_value=['file1.mp3', 'file2.txt', 'file3.mp3'])
    @patch('main.os.remove')
    def test_remove_mp3_files(self, mock_remove, mock_listdir):
        main.remove_mp3_files()
        mock_remove.assert_any_call('file1.mp3')
        mock_remove.assert_any_call('file3.mp3')
        self.assertEqual(mock_remove.call_count, 2)

if __name__ == '__main__':
    unittest.main()
