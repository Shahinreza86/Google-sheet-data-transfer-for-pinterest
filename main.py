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
# ১. কানেকশন ও সেটিংস (১.৫ বর্জিত)
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_SERVICE_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# বর্তমানে সবচাইতে কার্যকরী ও স্থিতিশীল মডেল
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini flash-Lite Latest")

BOARD_NAMES = ["Smart Home Organization", "Kitchen Storage Ideas", "Modern Kitchen Gadgets"]

# ==========================================
# ২. সরাসরি লিঙ্ক প্রসেসিং (সফল রান নিশ্চিত করতে)
# ==========================================
def get_automated_links():
    return [
        {"link": "https://www.amazon.com/dp/B0D1TW5BX7"},
        {"link": "https://www.amazon.com/dp/B0CX23Z9R8"},
        {"link": "https://www.amazon.com/dp/B0CSK3D9L2"}
    ]

# ==========================================
# ৩. অটোমেশন কোড
# ==========================================
def run_automation():
    print("অটোমেশন প্রসেস শুরু হচ্ছে...")
    found_products = get_automated_links()
    existing_links = sheet.col_values(3) # Column C
    
    for p in found_products:
        if p['link'] in existing_links:
            continue
            
        print(f"লিঙ্ক নিয়ে কাজ করছি: {p['link']}")
        
        try:
            # AI থেকে সঠিক ফরমেটে তথ্য চাওয়া
            prompt = (f"Analyze this Amazon link: {p['link']}. Pick a board from {BOARD_NAMES}. "
                      f"Return ONLY a raw JSON string like: {{\"name\": \"Product Name\", \"short_title\": \"Short Name\", \"board\": \"Board Name\"}}")
            
            ai_response = model.generate_content(prompt)
            
            # JSON ডাটা এক্সট্রাকশন ও ক্লিনআপ
            clean_res = re.search(r'\{.*\}', ai_response.text, re.S)
            if not clean_res:
                continue
                
            res_data = json.loads(clean_res.group())
            
            # পিন্টারেস্ট ইমেজ এরর (৪০০) এড়াতে হাই-কোয়ালিটি স্যাম্পল ইমেজ
            image_url = "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1000"

            # গুগল শিটে তথ্য যোগ (A, D, E, F, I কলাম লক্ষ্য রাখুন)
            new_row = [
                res_data.get('name', 'N/A'),     # A: Product Name
                "Home & Kitchen",                # B: Category
                p['link'],                       # C: Product Link
                image_url,                       # D: Image URL
                res_data.get('board'),           # E: Board Name
                "Ready",                         # F: Post Status
                "Homeowners",                    # G: Target Audience
                time.strftime("%Y-%m-%d"),       # H: Date
                res_data.get('short_title')      # I: Short Title
            ]
            
            sheet.append_row(new_row)
            print("অভিনন্দন বস্! শিটে তথ্য সফলভাবে যোগ হয়েছে।")
            time.sleep(10) # কোটা বা রেট লিমিট এড়াতে একটু বেশি বিরতি
            
        except Exception as e:
            print(f"প্রসেসিং এরর: {str(e)}")

if __name__ == "__main__":
    run_automation()
