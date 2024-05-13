import os
import torch
import logging

from pathlib import Path

from utils.t2s.utils_t2s import convert_wav_to_ogg

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


device = torch.device('cpu')
torch.set_num_threads(4)
speaker = 'aidar'  # 'aidar', 'baya', 'kseniya', 'xenia', 'random'
sample_rate = 48000  # 8000, 24000, 48000
put_accent = True
put_yo = True

local_file = "utils/t2s/silero_model/ru_v3.pt"

if not os.path.isfile(local_file):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/ru_v3.pt',
                                   local_file)

def t2s_silero_model_ru_v3(text, buttons=None):
    if buttons:
        audio_text = text + ': ' + ', '.join([button["title"] for button in buttons])
    else:
        audio_text = text
    audio_text = audio_text.replace(',', '.,').replace('?', '.?').replace(':', '.:').replace('!', '.!') + '.'
    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

    # audio = model.apply_tts(text=audio_text,
    #                         speaker=speaker,
    #                         sample_rate=sample_rate,
    #                         put_accent=put_accent,
    #                         put_yo=put_yo)
    logger.debug(f'audio_text = {audio_text}')
    audio_path_old = model.save_wav(text=audio_text,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)
    audio_path_new_wav = os.path.join('files', 'audio_files_t2s', audio_path_old)
    if os.path.isfile(audio_path_new_wav):
        os.remove(audio_path_new_wav)
    Path(audio_path_old).rename(audio_path_new_wav)
    audio_path_new_ogg = convert_wav_to_ogg(audio_path_new_wav)
    return audio_path_new_ogg

# t2s_silero_model_ru_v3('привет., как дела.?')