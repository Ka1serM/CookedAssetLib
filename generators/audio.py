import math
import os
import struct
import tempfile
import wave

import unreal

from common import create_asset, import_file


def write_wav(path, channels, rate, seconds):
    with wave.open(path, "wb") as file:
        file.setnchannels(channels)
        file.setsampwidth(2)
        file.setframerate(rate)
        for frame in range(int(rate * seconds)):
            sample = int(12000 * math.sin(frame * math.tau * 440 / rate))
            file.writeframes(struct.pack("<h", sample) * channels)


def generate():
    folder = tempfile.gettempdir()
    mono, stereo = os.path.join(folder, "tone_mono.wav"), os.path.join(folder, "tone_stereo.wav")
    write_wav(mono, 1, 22050, 1.0)
    write_wav(stereo, 2, 44100, 1.0)
    import_file(mono, "Audio", "S_ToneMono")
    import_file(stereo, "Audio", "S_ToneStereo")
    create_asset("Audio", "SA_Attenuation", unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    create_asset("Audio", "SC_Class", unreal.SoundClass, unreal.SoundClassFactory())
    create_asset("Audio", "SM_Mix", unreal.SoundMix, unreal.SoundMixFactory())
    create_asset("Audio", "SCue_Tone", unreal.SoundCue, unreal.SoundCueFactoryNew())
