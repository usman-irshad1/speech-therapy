import os
import csv
import shutil

# --- Configuration ---
SNAPSHOT_DIR = r"C:\Users\usman\.cache\huggingface\hub\datasets--abidanoaman--unified-urdu-speech-asr\snapshots\06dcc2efe7740de3d515361769cd20f0204c85e9"
OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\test_batch"

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Building an index of all audio files on disk...")
    audio_file_map = {}
    for root, _, files in os.walk(SNAPSHOT_DIR):
        for file in files:
            if file.endswith(('.wav', '.mp3', '.flac')):
                audio_file_map[file] = os.path.join(root, file)

    print(f"Found {len(audio_file_map)} audio files. Parsing metadata...")
    found_count = 0

    for root, _, files in os.walk(SNAPSHOT_DIR):
        if "metadata.csv" in files:
            metadata_path = os.path.join(root, "metadata.csv")
            
            with open(metadata_path, encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row.get("audio")
                    transcript = row.get("transcript")

                    if not filename or not transcript:
                        continue

                    filename = os.path.basename(filename)

                    if filename in audio_file_map:
                        source_path = audio_file_map[filename]
                        dest_filename = f"eval_{found_count + 1}.wav"
                        dest_path = os.path.join(OUTPUT_DIR, dest_filename)

                        shutil.copy2(source_path, dest_path)
                        found_count += 1
                        
                        print(f"✅ Extracted: {dest_filename} ({filename})")
                        print(f"   Transcript: {transcript}\n")

                        if found_count >= 10:
                            print("-" * 50)
                            print(f"Successfully extracted {found_count} test files and transcripts to {OUTPUT_DIR}!")
                            return

    print("-" * 50)
    print(f"Extraction complete! Total extracted: {found_count} files.")

if __name__ == "__main__":
    main()