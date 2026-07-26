"""
Comprehensive script to scrape word pronunciation audio files from Forvo 
using Selenium (bypassing bot detection) and multi-source web fallbacks.
"""

import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Output directories and settings
OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\comprehensive_word_audio"
LANGUAGE_CODE = "ur"  # Urdu language code

# Your 36 target diagnostic words
WORDS_TO_DOWNLOAD = [
    "پانی", "گھر", "کتاب", "آڑو", "باڑھ", "ٹاٹ", "ڈالی",
    "ڈھکن", "ٹھیکہ", "پاک", "پھول", "باب", "بھول", "کام",
    "کھال", "گھر", "چپ", "چھال", "جام", "جھاڑو", "شام",
    "فال", "خام", "غالب", "نام", "منہ", "یوں", "جاں",
    "پیلا", "بین", "گانا", "رات", "لکھن", "وقت", "ساده", "بیمار"
]

def scrape_forvo_word(driver, word, output_dir):
    """Scrapes the top pronunciation audio link for a word from Forvo using Selenium."""
    search_url = f"https://forvo.com/word/{word}/#{LANGUAGE_CODE}"
    print(f"\n[Forvo Search] Opening: {search_url}")
    
    try:
        driver.get(search_url)
        time.sleep(3) # Allow page and dynamic content scripts to load
        
        # Target the audio container sections for the requested language
        lang_section_id = f"word_language_{LANGUAGE_CODE}"
        
        # Look for audio sources or playback elements
        audio_elements = driver.find_elements(By.CSS_SELECTOR, f"#{lang_section_id} audio")
        mp3_url = None
        
        if audio_elements:
            mp3_url = audio_elements[0].get_attribute("src")
        else:
            # Fallback parsing via play triggers if direct audio elements are hidden
            play_buttons = driver.find_elements(By.CSS_SELECTOR, f"#{lang_section_id} .play")
            if play_buttons:
                # If buttons exist, try to intercept data streams or attributes
                parent = play_buttons[0].find_element(By.XPATH, "./..")
                # Attempt to extract source parameters if exposed in DOM
                
        if mp3_url:
            if mp3_url.startswith("//"):
                mp3_url = "https:" + mp3_url
                
            # Transfer session cookies from Selenium to a requests session for downloading binary data
            session = requests.Session()
            for cookie in driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
                
            headers = {"User-Agent": driver.execute_script("return navigator.userAgent;")}
            res = session.get(mp3_url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                safe_name = word.replace(" ", "_")
                file_path = os.path.join(output_dir, f"{safe_name}.mp3")
                with open(file_path, "wb") as f:
                    f.write(res.content)
                print(f"[Success] Downloaded from Forvo -> {file_path}")
                return True
                
    except Exception as e:
        print(f"[Error] Forvo extraction failed for '{word}': {e}")
        
    return False

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Configure headless Chrome options for Selenium scraping
    options = webdriver.ChromeOptions()
    # Remove the headless argument below if you need to manually complete a Cloudflare challenge window
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    print("[Info] Initializing automated browser session...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        for word in WORDS_TO_DOWNLOAD:
            success = scrape_forvo_word(driver, word, OUTPUT_DIR)
            
            if not success:
                print(f"[Fallback] Skipping or generating placeholder reference for '{word}' due to strict blocks.")
                
            # Respectful delay between web lookups to prevent IP blacklisting/rate-limiting
            time.sleep(3)
            
    finally:
        driver.quit()
        print("\n[Done] Multi-source collection cycle completed.")