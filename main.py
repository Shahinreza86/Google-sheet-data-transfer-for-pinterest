import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time
import requests
from bs4 import BeautifulSoup

# ১. গুগল শিট কানেকশন সেটআপ
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

def get_real_amazon_image(url):
    """এটি ঠিক সেই কাজটাই করবে যা আপনি রাইট ক্লিক করে করেন"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # আমাজনের মেইন প্রোডাক্ট ইমেজ খোঁজা (landingImage আইডি দিয়ে)
            img_tag = soup.find('img', {'id': 'landingImage'}) or soup.find('img', {'id': 'imgBlkFront'})
            if img_tag:
                # ডিকশনারি ফরম্যাট থেকে হাই-রেজোলিউশন ইমেজ বের করা
                data_dynamic_img = img_tag.get('data-a-dynamic-image')
                if data_dynamic_img:
                    return list(json.loads(data_dynamic_img).keys())[-1] # সবচাইতে বড় সাইজের ছবি
                return img_tag.get('src')
        return None
    except:
        return None

def process_data():
    all_rows = sheet.get_all_values()
    for i, row in enumerate(all_rows[1:], start=2):
        if len(row) > 2 and "amazon.com" in row[2].lower() and (len(row) < 1 or not row[0].strip()):
            link = row[2].strip()
            print(f"--- সারি {i} প্রসেস হচ্ছে ---")
            
            # জেমিনির বদলে সরাসরি পাইথন দিয়ে ইমেজ লিঙ্ক বের করা (১০০% সঠিক হবে)
            real_image = get_real_amazon_image(link)
            
            if real_image:
                try:
                    # জেমিনি এখন শুধু নাম, টাইটেল আর বোর্ড ঠিক করবে
                    prompt = f"Product URL: {link}. Task: Provide 1. Full Product Name, 2. Short Catchy Title, 3. Best Pinterest Board from {BOARDS}. Format: Name | Title | Board"
                    response = model.generate_content(prompt)
                    parts = response.text.split('|')
                    
                    p_name = parts[0].strip() if len(parts) > 0 else "Product"
                    p_title = parts[1].strip() if len(parts) > 1 else "Cool Product"
                    p_board = parts[2].strip() if len(parts) > 2 else BOARDS[0]

                    # শিটে ডাটা পাঠানো
                    sheet.update_cell(i, 1, p_name)   # A
                    sheet.update_cell(i, 4, real_image) # D (এখানেই আপনার দেয়া সেই ছবির লিঙ্ক বসবে)
                    sheet.update_cell(i, 5, p_board)  # E
                    sheet.update_cell(i, 6, "Ready")  # F (এখন থেকে Ready আসবে)
                    sheet.update_cell(i, 9, p_title)  # I
                    
                    print(f"সারি {i} সফল! ইমেজ লিঙ্ক পাওয়া গেছে।")
                    time.sleep(2)
                except Exception as e:
                    print(f"সারি {i} ডাটা প্রসেস করতে এরর: {e}")
            else:
                print(f"সারি {i}: ইমেজ লিঙ্ক খুঁজে পাওয়া যায়নি।")

if __name__ == "__main__":
    process_data()
