import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time
import requests
from bs4 import BeautifulSoup

# ১. গুগল শিট কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি সেটআপ
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def get_amazon_info(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find(id="productTitle").get_text().strip() if soup.find(id="productTitle") else "Product"
        # ইমেজ খোঁজা
        img_tag = soup.find(id="landingImage") or soup.find(id="imgBlkFront")
        image_url = img_tag.get('src') if img_tag else ""
        return title, image_url
    except:
        return None, None

def process_data():
    all_rows = sheet.get_all_values()
    for i, row in enumerate(all_rows[1:], start=2):
        # কলাম C-তে লিঙ্ক আছে কিন্তু কলাম A-তে নাম নেই
        if len(row) > 2 and row[2].strip() and (len(row) < 1 or not row[0].strip()):
            link = row[2].strip()
            print(f"সারি {i} প্রসেস হচ্ছে...")
            
            # প্রথমে আমাজন থেকে ডিরেক্ট ডাটা আনার চেষ্টা (কোটা বাঁচাবে)
            raw_title, image_url = get_amazon_info(link)
            
            if raw_title:
                try:
                    # জেমিনি শুধু বোর্ড সিলেক্ট আর টাইটেল অপ্টিমাইজ করবে
                    prompt = f"Product: {raw_title}. Boards: {BOARDS}. Provide: 1. Catchy Short Title (max 50 chars), 2. One board from list. Format: Title | Board"
                    response = model.generate_content(prompt)
                    parts = response.text.split('|')
                    
                    short_title = parts[0].strip() if len(parts) > 0 else raw_title[:50]
                    board_name = parts[1].strip() if len(parts) > 1 else BOARDS[0]

                    # শিটে ডাটা রাইট করা
                    sheet.update_cell(i, 1, raw_title)  # A: Name
                    sheet.update_cell(i, 4, image_url)  # D: Image URL
                    sheet.update_cell(i, 5, board_name) # E: Board
                    sheet.update_cell(i, 6, "Ready")     # F: Status
                    sheet.update_cell(i, 9, short_title) # I: Short Title
                    
                    print(f"সারি {i} সফল!")
                    time.sleep(1)
                except Exception as e:
                    print(f"জেমিনি এরর: {e}")
            else:
                print(f"সারি {i}: লিঙ্ক থেকে তথ্য পাওয়া যায়নি।")

if __name__ == "__main__":
    process_data()
