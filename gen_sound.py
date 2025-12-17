import wave
import math
import struct
import base64
import os

# Generate 0.5 seconds of 880Hz sine wave at 8000Hz (Smaller file)
sample_rate = 8000
duration = 0.5
frequency = 880 

n_frames = int(sample_rate * duration)
data = b""
for i in range(n_frames):
    value = int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate))
    data += struct.pack('<h', value)

filename = "temp_beep.wav"
with wave.open(filename, "w") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(data)

with open(filename, "rb") as f:
    wav_bytes = f.read()
    b64 = base64.b64encode(wav_bytes).decode('utf-8')
    
    # Write to file to ensure we get it all
    with open("beep_base64.txt", "w") as text_file:
        text_file.write(b64)
    
os.remove(filename)
