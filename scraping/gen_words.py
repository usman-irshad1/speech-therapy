import os
import asyncio
import edge_tts

OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\comprehensive_word_audio"
VOICE = "ur-PK-AsadNeural"  # Natural sounding Urdu male voice (alternative: ur-PK-NafeesNeural)

WORDS_TO_DOWNLOAD = [
    "پانی", "گھر", "کتاب", "آڑو", "باڑھ", "ٹاٹ", "ڈالی",
    "ڈھکن", "ٹھیکہ", "پاک", "پھول", "باب", "بھول", "کام",
    "کھال", "گھر", "چپ", "چھال", "جام", "جھاڑو", "شام",
    "فال", "خام", "غالب", "نام", "منہ", "یوں", "جاں",
    "پیلا", "بین", "گانا", "رات", "لکھن", "وقت", "ساده", "بیمار"
]

async def generate_audio():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"[Info] Generating reference audio for {len(WORDS_TO_DOWNLOAD)} words using Edge TTS...")
    
    for word in WORDS_TO_DOWNLOAD:
        safe_name = word.replace(" ", "_")
        file_path = os.path.join(OUTPUT_DIR, f"{safe_name}.mp3")
        
        communicate = edge_tts.Communicate(word, VOICE)
        await communicate.save(file_path)
        print(f"[Success] Generated: {file_path}")

if __name__ == "__main__":
    asyncio.run(generate_audio())
    print("\n[Done] All reference audio files successfully created locally!")