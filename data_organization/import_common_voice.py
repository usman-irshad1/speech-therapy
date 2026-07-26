import os
import kagglehub

# Set the cache directory to your desired location
os.environ["KAGGLEHUB_CACHE"] = r"C:\Users\usman\Desktop\spech_pipeline\cache"

# Now, when you download, it will use the directory above
path = kagglehub.dataset_download("cookiefinder/mozilla-common-voice-urdu")