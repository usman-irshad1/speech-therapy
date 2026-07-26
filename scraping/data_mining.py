import os
import pyarrow as pa
import pyarrow.ipc

# --- Configuration ---
SEARCH_DIRS = [
    r"C:\Users\usman\Desktop\spech_pipeline",
    r"C:\Users\usman\.cache\huggingface\datasets"
]
OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\test_batch"

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("Hunting for cache files that contain BOTH audio and text...\n")
    arrow_files = []
    
    for search_dir in SEARCH_DIRS:
        if os.path.exists(search_dir):
            for root, dirs, files in os.walk(search_dir):
                for f in files:
                    if f.endswith(".arrow"):
                        arrow_files.append(os.path.join(root, f))

    if not arrow_files:
        print("Could not find any .arrow files.")
        return

    found_count = 0

    for arrow_path in arrow_files:
        try:
            with pa.OSFile(arrow_path, 'rb') as f:
                reader = pa.ipc.RecordBatchStreamReader(f)
                table = reader.read_all()
        except Exception:
            continue

        column_names = table.column_names
        
        # STRICT FILTER: Must have both audio AND a recognizable text column
        if "audio" not in column_names:
            continue
            
        text_col_name = None
        for col in ["sentence", "text", "transcript"]:
            if col in column_names:
                text_col_name = col
                break
                
        # If this arrow file doesn't have text, skip it entirely!
        if not text_col_name:
            continue

        audio_col = table["audio"]
        text_col = table[text_col_name]

        for i in range(len(table)):
            audio_struct = audio_col[i].as_py()
            
            if audio_struct and "bytes" in audio_struct and audio_struct["bytes"] is not None:
                audio_bytes = audio_struct["bytes"]
                text_content = text_col[i].as_py()
                
                # Skip if the text is empty
                if not text_content:
                    continue
                
                filename = f"sample_{found_count + 1}.mp3"
                out_path = os.path.join(OUTPUT_DIR, filename)
                
                with open(out_path, "wb") as out_file:
                    out_file.write(audio_bytes)
                
                print(f"✅ Saved Raw MP3: {filename}")
                print(f"   Transcript: {text_content}\n")
                
                found_count += 1
                
                if found_count >= 5:
                    print("-" * 50)
                    print(f"Extraction complete! 5 test MP3s saved to {OUTPUT_DIR}")
                    return

    print("-" * 50)
    print(f"Extraction complete! Saved {found_count} MP3 files.")

if __name__ == "__main__":
    main()