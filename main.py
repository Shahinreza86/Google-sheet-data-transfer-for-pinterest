import requests
from bs4 import BeautifulSoup
import json
import random
import re
import time
import os
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

# =========================
# ১. কনফিগারেশন (GitHub Secrets ব্যবহার করা ভালো)
# =========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"

BOARD_NAMES = [
    "Smart Home Organization",
    "Kitchen Storage Ideas",
    "Modern Kitchen Gadgets",
    "Pantry Organization",
    "Kitchen Cleaning Hacks"
]

AMAZON_URLS = [
    "https://www.amazon.com/s?k=home+and+kitchen+organization",
    "https://www.amazon.com/s?k=smart+home+storage+solutions",
    "https://www.amazon.com/s?k=aesthetic+kitchen+gadgets"
]

# আমাজন ব্লক এড়াতে শক্তিশালী হেডার
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# =========================
# ২. সেটআপ (Gemini & Google Sheet)
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-flash-lite-latest") # আপনি চাইলে gemini-flash-lite-latest ও দিতে পারেন

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
# service_account.json ফাইলটি আপনার রুটে থাকতে হবে
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# =========================
# ৩. আমাজন স্ক্র্যাপার (উন্নত ভার্সন)
# =========================
def get_high_res_image(item):
    """আইটেম থেকে সবচাইতে বড় ছবির লিঙ্ক বের করার লজিক"""
    img_tag = item.select_one("img")
    if not img_tag: return "N/A"
    
    # আমাজনের ডায়নামিক ইমেজ ডিকশনারি চেক করা
    if img_tag.has_attr('data-a-dynamic-image'):
        try:
            img_dict = json.loads(img_tag['data-a-dynamic-image'])
            return list(img_dict.keys())[-1] # সবচাইতে বড় রেজোলিউশন
        except:
            return img_tag.get('src', 'N/A')
    return img_tag.get('src', 'N/A')

def scrape_amazon():
    all_products = []
    for url in AMAZON_URLS:
        try:
            print(f"Scraping: {url}")
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code != 200: continue
            
            soup = BeautifulSoup(response.text, "lxml")
            products = soup.select('[data-component-type="s-search-result"]')
            
            for item in products[:7]: # প্রতি লিঙ্ক থেকে ৭টি করে প্রোডাক্ট
                title_tag = item.select_one("h2 a span")
                link_tag = item.select_one("h2 a")
                
                if title_tag and link_tag:
                    title = title_tag.text.strip()
                    link = "https://www.amazon.com" + link_tag['href']
                    image = get_high_res_image(item)
                    
                    if image != "N/A":
                        all_products.append({"title": title, "link": link, "image": image})
            time.sleep(2) # আমাজন ব্লক এড়াতে গ্যাপ
        except Exception as e:
            print(f"Error: {e}")
    return all_products

# =========================
# ৪. জেমিনি এআই প্রসেসিং
# =========================
def get_ai_metadata(title):
    prompt = f"""
    Product Name: {title}
    Available Boards: {BOARD_NAMES}
    
    Task: 
    1. Select the most relevant board.
    2. Write a short, catchy Pinterest title (max 50 chars).
    
    Return ONLY JSON format:
    {{
      "board": "Selected Board Name",
      "short_title": "Short Title Here"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # JSON ক্লিনআপ
        clean_text = response.text.replace("```json", "").replace("
```", "").strip()
        data = json.loads(clean_text)
        return data
    except Exception as e:
        print(f"AI Error: {e}")
        return {"board": BOARD_NAMES[0], "short_title": title[:45]}

# =========================
# ৫. মূল প্রসেস
# =========================
def run_automation():
    print("Starting Scraper...")
    products = scrape_amazon()
    print(f"Found {len(products)} products.")
    
    for p in products:
        # ডুপ্লিকেট চেক (লিঙ্ক দিয়ে)
        existing_links = sheet.col_values(3)
        if p['link'] in existing_links:
            print(f"Skipping Duplicate: {p['title'][:30]}")
            continue
            
        ai_data = get_ai_metadata(p['title'])
        
        # শিট কলাম অনুযায়ী ডাটা সাজানো (A to I)
        row = [
            p['title'],                   # A: Product Name
            "Kitchen & Home",             # B: Category
            p['link'],                    # C: Product Link
            p['image'],                   # D: Image URL
            ai_data['board'],             # E: Board Name
            "Ready",                      # F: Post Status
            "Homeowners",                 # G: Target Audience
            datetime.now().strftime("%Y-%m-%d"), # H: Date
            ai_data['short_title']        # I: Short Title
        ]
        
        sheet.append_row(row)
        print(f"Successfully Added: {ai_data['short_title']}")
        time.sleep(1) # API লিমিট এড়াতে

if __name__ == "__main__":
    run_automation()
