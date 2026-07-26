from datasets import load_dataset

# 1. Load the dataset from cache (it will find it automatically)
fleurs = load_dataset("google/fleurs", "ur_pk")

# 2. Save it explicitly to your project folder
save_path = r"C:\Users\usman\Desktop\spech_pipeline\data\google_fleurs_ur"
fleurs.save_to_disk(save_path)

print(f"Dataset successfully moved to: {save_path}")