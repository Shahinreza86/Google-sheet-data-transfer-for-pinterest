import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time
import requests
from bs4 import BeautifulSoup

# ১. গুগল শিট ও জেমিনি সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# জেমিনি সেটআপ - আপনার তালিকাভুক্ত 'Gemini Flash-Lite Latest'
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def get_amazon_details_perfectly(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # টাইটেল স্ক্র্যাপিং (আমাজনের আসল নাম)
            title_tag = soup.find("span", {"id": "productTitle"})
            actual_name = title_tag.get_text().strip() if title_tag else "N/A"
            
            # ইমেজ স্ক্র্যাপিং (সবচেয়ে বড় ছবি)
            img_tag = soup.find('img', {'id': 'landingImage'})
            image_url = "N/A"
            if img_tag and img_tag.get('data-a-dynamic-image'):
                image_url = list(json.loads(img_tag.get('data-a-dynamic-image')).keys())[-1]
            elif img_tag:
                image_url = img_tag.get('src')
                
            return actual_name, image_url
    except Exception as e:
        print(f"Scraping Error: {e}")
    return "N/A", "N/A"

def process_data():
    all_rows = sheet.get_all_values()
    print(f"Total rows: {len(all_rows)}")
    
    for i, row in enumerate(all_rows[1:], start=2):
        # যদি প্রোডাক্ট লিঙ্ক থাকে এবং কলাম A (প্রোডাক্ট নাম) খালি থাকে
        if len(row) > 2 and "amazon" in row[2].lower() and (len(row) < 1 or not row[0].strip() or row[3] == "N/A"):
            product_link = row[2].strip()
            print(f"--- সারি {i} ঠিক করা হচ্ছে ---")
            
            # সরাসরি আমাজন থেকে আসল নাম এবং ইমেজ সংগ্রহ
            amazon_name, actual_image_url = get_amazon_details_perfectly(product_link)
            
            try:
                # জেমিনিকে শুধু বোর্ড আর শর্ট টাইটেল বানাতে বলা হচ্ছে
                prompt = f"Product: {amazon_name}. Task: 1. Create a Short Pinterest Title. 2. Select one board from {BOARDS}. Format: SHORT_TITLE: | BOARD:"
                response = model.generate_content(prompt)
                lines = response.text.split('\n')
                
                short_title = next((l.split('SHORT_TITLE:')[1] for l in lines if 'SHORT_TITLE:' in l), "Awesome Product").strip()
                selected_board = next((l.split('BOARD:')[1] for l in lines if 'BOARD:' in l), BOARDS[0]).strip()

                # শিটে ডাটা এন্ট্রি - আপনার ছবি অনুযায়ী কলাম সাজানো
                sheet.update_cell(i, 1, amazon_name)      # Column A (Original Amazon Name)
                sheet.update_cell(i, 4, actual_image_url) # Column D (Direct Image Link)
                sheet.update_cell(i, 5, selected_board)   # Column E (Board)
                sheet.update_cell(i, 6, "Ready")          # Column F (Status)
                sheet.update_cell(i, 9, short_title)      # Column I (Short Title)
                
                print(f"সারি {i} সফলভাবে আপডেট হয়েছে।")
                time.sleep(2) # আমাজন ব্লক এড়াতে গ্যাপ
            except Exception as e:
                print(f"সারি {i} এ জেমিনি সমস্যা: {e}")

if __name__ == "__main__":
    process_data()
