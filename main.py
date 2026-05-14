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

# জেমিনি সেটআপ - এখানে আপনার সফল হওয়া লাইট মডেল ব্যবহার করা হয়েছে
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05') 

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def get_amazon_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            img_tag = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'id': 'imgBlkFront'})
            image_url = "N/A"
            if img_tag:
                if img_tag.get('data-a-dynamic-image'):
                    image_url = list(json.loads(img_tag.get('data-a-dynamic-image')).keys())[-1]
                else:
                    image_url = img_tag.get('src')
            return image_url
    except:
        pass
    return "N/A"

def process_data():
    all_rows = sheet.get_all_values()
    print(f"Total rows found: {len(all_rows)}")
    
    for i, row in enumerate(all_rows[1:], start=2):
        if len(row) > 2 and "amazon.com" in row[2].lower():
            # যদি কলাম A ফাঁকা থাকে এবং কলাম C-তে লিঙ্ক থাকে
            if len(row) < 1 or not row[0].strip():
                product_link = row[2].strip()
                print(f"--- সারি {i} প্রসেস হচ্ছে ---")
                
                actual_image_url = get_amazon_data(product_link)
                
                try:
                    prompt = f"Link: {product_link}. Provide: NAME: [Full Name], TITLE: [Short Title], BOARD: [Select from {BOARDS}]. Format: NAME: | TITLE: | BOARD:"
                    response = model.generate_content(prompt)
                    lines = response.text.split('\n')
                    
                    p_name = next((l.split('NAME:')[1] for l in lines if 'NAME:' in l), "Product").strip()
                    p_title = next((l.split('TITLE:')[1] for l in lines if 'TITLE:' in l), "Cool Item").strip()
                    p_board = next((l.split('BOARD:')[1] for l in lines if 'BOARD:' in l), BOARDS[0]).strip()

                    # শিট আপডেট
                    sheet.update_cell(i, 1, p_name)      # কলাম A
                    sheet.update_cell(i, 4, actual_image_url) # কলাম D
                    sheet.update_cell(i, 5, p_board)     # কলাম E
                    sheet.update_cell(i, 6, "Ready")     # কলাম F
                    sheet.update_cell(i, 9, p_title)     # কলাম I
                    
                    print(f"সারি {i} সফলভাবে আপডেট হয়েছে।")
                    time.sleep(2)
                except Exception as e:
                    print(f"সারি {i} এ সমস্যা: {e}")

if __name__ == "__main__":
    process_data()
