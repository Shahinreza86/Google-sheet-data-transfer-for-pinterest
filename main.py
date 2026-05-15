import os
import json
import time
import requests
import random
import re
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

# ==========================================
# ১. কানেকশন ও সেটিংস (Gemma ২ ব্যবহার)
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")

# গুগল শিট কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_SERVICE_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# এখানে Gemma ২ মডেলটি সেট করা হয়েছে (সম্পূর্ণ ১.৫ মুক্ত)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemma-2-9b-it")

SEARCH_KEYWORDS = ["Kitchen organizers", "Modern pantry storage", "Smart home gadgets"]
BOARD_NAMES = ["Smart Home Organization", "Kitchen Storage Ideas", "Modern Kitchen Gadgets"]

# ==========================================
# ২. অটোমেশন লজিক
# ==========================================
def run_automation():
    print("Gemma ২ দিয়ে অটোমেশন শুরু হচ্ছে...")
    
    # আপাতত সরাসরি কাজ শুরু করার জন্য আমাজন লিঙ্ক
    links = [
        "https://www.amazon.com/dp/B0D1TW5BX7",
        "https://www.amazon.com/dp/B0CX23Z9R8"
    ]
    
    existing_links = sheet.col_values(3) # Column C
    
    for link in links:
        if link in existing_links:
            continue
            
        print(f"প্রসেসিং লিঙ্ক: {link}")
        
        try:
            # Gemma ২ এর জন্য প্রোম্পট
            prompt = (f"Analyze this product: {link}. Pick one board from {BOARD_NAMES}. "
                      f"Return ONLY valid JSON: {{\"name\": \"...\", \"short_title\": \"...\", \"board\": \"...\"}}")
            
            response = model.generate_content(prompt)
            
            # JSON ডাটা এক্সট্রাক্ট করা (যাতে কোনো এরর না আসে)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            
            if json_match:
                res_data = json.loads(json_match.group())
                
                # আপনার শিটের নির্দিষ্ট কলামগুলো আপডেট (A, D, E, F, I)
                new_row = [
                    res_data['name'],          # A: Product Name
                    "Kitchen Gadgets",         # B: Category
                    link,                      # C: Product Link
                    "https://m.media-amazon.com/images/I/placeholder.jpg", # D: Image URL
                    res_data['board'],         # E: Board Name
                    "Ready",                   # F: Post Status
                    "Homeowners",              # G: Target Audience
                    time.strftime("%Y-%m-%d"), # H: Date
                    res_data['short_title']    # I: Short Title
                ]
                
                sheet.append_row(new_row)
                print("অভিনন্দন! শিটে তথ্য যোগ হয়েছে।")
                time.sleep(5)
                
        except Exception as e:
            print(f"ত্রুটি: {e}")

if __name__ == "__main__":
    run_automation()
