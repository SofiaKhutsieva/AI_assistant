from pydub import AudioSegment


def convert_wav_to_ogg(orig_song) :
    song = AudioSegment.from_wav(orig_song)
    dest_song = orig_song.replace('.wav', '.ogg')
    song.export(dest_song, format="ogg")
    return dest_song