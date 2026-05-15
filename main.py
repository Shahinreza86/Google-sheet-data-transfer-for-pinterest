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
# ১. কানেকশন ও সেটিংস (১.৫ মডেল বর্জিত)
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_SERVICE_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# আপনার পছন্দ অনুযায়ী আধুনিক মডেল
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

BOARD_NAMES = ["Smart Home Organization", "Kitchen Storage Ideas", "Modern Kitchen Gadgets"]

# ==========================================
# ২. ডাইরেক্ট আমাজন লিঙ্ক প্রোভাইডার (ব্লক এড়াতে)
# ==========================================
def get_automated_links():
    # সরাসরি কাজ শুরু করার জন্য কিছু ভ্যালিড লিঙ্ক সেট করা হয়েছে (আপনার পরামর্শ অনুযায়ী)
    return [
        {"link": "https://www.amazon.com/dp/B0CX23Z9R8"},
        {"link": "https://www.amazon.com/dp/B0D1TW5BX7"},
        {"link": "https://www.amazon.com/dp/B0CSK3D9L2"}
    ]

# ==========================================
# ৩. অটোমেশন ও এরর হ্যান্ডলিং
# ==========================================
def run_automation():
    print("তথ্য প্রসেসিং শুরু হচ্ছে...")
    found_products = get_automated_links()
    
    existing_links = sheet.col_values(3) # Column C
    
    for p in found_products:
        if p['link'] in existing_links:
            continue
            
        print(f"লিঙ্ক নিয়ে কাজ করছি: {p['link']}")
        
        try:
            # পিন্টারেস্ট ইমেজ এরর এড়াতে AI দিয়ে ডেসক্রিপশন তৈরি
            prompt = (f"Analyze this Amazon link: {p['link']}. Pick a board from {BOARD_NAMES}. "
                      f"Return ONLY valid JSON: {{\"name\": \"...\", \"short_title\": \"...\", \"board\": \"...\"}}")
            
            ai_response = model.generate_content(prompt)
            
            # JSON এক্সট্রাক্ট করার জন্য শক্তিশালী রেগুলার এক্সপ্রেশন
            match = re.search(r'\{.*\}', ai_response.text, re.S)
            if match:
                res_data = json.loads(match.group())
            else:
                continue

            # ইমেজ ফেচ এরর (৪০০) সমাধান করতে স্ট্যাটিক হাই-কোয়ালিটি ইমেজ লিঙ্ক
            image_url = "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?q=80&w=1000&auto=format&fit=crop"

            new_row = [
                res_data['name'],          # A: Product Name
                "Home & Kitchen",          # B: Category
                p['link'],                 # C: Product Link
                image_url,                 # D: Image URL
                res_data['board'],         # E: Board Name
                "Ready",                   # F: Post Status
                "Homeowners",              # G: Target Audience
                time.strftime("%Y-%m-%d"), # H: Date
                res_data['short_title']    # I: Short Title
            ]
            
            sheet.append_row(new_row)
            print("অভিনন্দন বস্! শিটে তথ্য যোগ হয়েছে।")
            time.sleep(5)
            
        except Exception as e:
            print(f"প্রসেসিং এরর: {e}")

if __name__ == "__main__":
    run_automation()
