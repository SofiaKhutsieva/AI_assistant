import whisper # pip install openai-whisper
import torch
from pytorch_lightning import LightningModule
from transformers import WhisperProcessor, WhisperForConditionalGeneration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def s2t_whisper(audio_file):
    # базовый вариант
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]

def s2t_rus_whisper(audio_file):
    # для русского языка
    class Config:
        warmup_steps = 2
        batch_size = 16
        num_worker = 2
    cfg = Config()
    class RusModel(LightningModule):
        def __init__(self, cfg:Config, model_name="base", lang="ru") -> None:
            super().__init__()
            self.options = whisper.DecodingOptions(fp16=False, language=lang, without_timestamps=True)
            self.model = whisper.load_model(model_name)
            self.tokenizer = whisper.tokenizer.get_tokenizer(True, language="ru", task=self.options.task)
            self.cfg = cfg
        def forward(self, x):
            return self.model(x)
    rus_model = RusModel(cfg)
    woptions = whisper.DecodingOptions(language="ru", without_timestamps=True)


    audio = whisper.load_audio(audio_file)
    input_speech = audio
    print(f'audio = {audio.shape}')
    audio = whisper.pad_or_trim(audio)
    print(f'audio = {audio.shape}')
    mel = whisper.log_mel_spectrogram(audio).to(DEVICE)
    print(f'mel = {mel.shape}')
    result = rus_model.model.decode(mel, woptions)
    return result.text


# load model and processor
processor = WhisperProcessor.from_pretrained("openai/whisper-small") # tiny / base / small / medium / large
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small", from_tf=True)
forced_decoder_ids = processor.get_decoder_prompt_ids(language="russian", task="transcribe")

def s2t_rus_whisper_transformers(audio_file):
    # через транформеры

    # load audio
    sampling_rate = 16_000
    audio = whisper.load_audio(audio_file)
    input_speech = audio
    audio = whisper.pad_or_trim(audio)

    input_features = processor(audio=input_speech, sampling_rate=sampling_rate, return_tensors="pt").input_features

    # generate token ids
    predicted_ids = model.generate(input_features, forced_decoder_ids=forced_decoder_ids)
    # decode token ids to text
    # transcription = processor.batch_decode(predicted_ids)
    # print(transcription)

    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)
    # print(transcription)
    return transcription

# import os
# audio_file = os.path.join('..', '..', 'files', 'audio_files_s2t', '2023-08-07-21-15-43-185750.wav')
# print(s2t_whisper(audio_file))
# print(s2t_rus_whisper_transformers(audio_file))
# print(s2t_rus_whisper(audio_file)) # не работает на CPU