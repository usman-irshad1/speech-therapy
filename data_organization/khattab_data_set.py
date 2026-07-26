from datasets import load_dataset
import os

# Define the target path
target_path = r"C:\Users\usman\Desktop\spech_pipeline\data\indic_superb_urdu"

# The Kathbath dataset contains the Urdu speech data used in IndicSUPERB
# Note: You may need to be logged in with `huggingface-cli login` 
# if the dataset requires access agreement.
dataset = load_dataset("ai4bharat/Kathbath", "urdu")

# Save to your local directory
dataset.save_to_disk(target_path)
print(f"IndicSUPERB (Kathbath Urdu) saved to {target_path}")