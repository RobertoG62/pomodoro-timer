import wave
import math
import struct

def save_wav(file_name, freq_list, duration_ms=200):
    sample_rate = 44100
    n_samples = int(sample_rate * (duration_ms / 1000.0))
    
    with wave.open(file_name, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for freq in freq_list:
            for i in range(n_samples):
                t = float(i) / sample_rate
                # Sine wave generation
                value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * t))
                data = struct.pack('<h', value)
                wav_file.writeframes(data)

# צור צליל "דינג" (גבוה וחד)
save_wav("ding.wav", [1500], 300)

# צור צליל "Chime" (רצף של שני טונים נעימים)
save_wav("chime.wav", [600, 800], 250)

print("✅ Created ding.wav and chime.wav successfully!")