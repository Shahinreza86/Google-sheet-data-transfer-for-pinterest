import os
import json
import time
import requests
import random
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai

# ==========================================
# ১. কানেকশন ও সেটিংস
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SERVICE_JSON = os.environ.get("GOOGLE_SERVICE_JSON")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(GOOGLE_SERVICE_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# আপনার দেওয়া তালিকার সঠিক মডেলটি এখানে সেট করা হয়েছে
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

SEARCH_KEYWORDS = ["Best kitchen organizers 2026", "Modern home storage hacks", "Space saving kitchen tools"]
BOARD_NAMES = ["Smart Home Organization", "Kitchen Storage Ideas", "Modern Kitchen Gadgets"]

# ==========================================
# ২. লিঙ্ক সংগ্রহের উন্নত পদ্ধতি
# ==========================================
def get_automated_links():
    keyword = random.choice(SEARCH_KEYWORDS)
    # আমাজন ব্লক এড়াতে গুগল সার্চের মাধ্যমে সরাসরি প্রোডাক্ট পেজ খোঁজা
    search_url = f"https://www.google.com/search?q=site:amazon.com+dp+{keyword.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    product_data = []
    try:
        response = requests.get(search_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "amazon.com/" in href and "/dp/" in href:
                # ক্লিন লিঙ্ক তৈরি
                start = href.find("https://www.amazon.com")
                if start != -1:
                    clean_link = href[start:].split("&")[0].split("%")[0]
                    product_data.append({"link": clean_link})
                if len(product_data) >= 3: break
    except Exception as e:
        print(f"লিঙ্ক পেতে সমস্যা: {e}")
    return product_data

# ==========================================
# ৩. অটোমেশন রান
# ==========================================
def run_automation():
    print("নতুন প্রোডাক্ট খোঁজা হচ্ছে...")
    found_products = get_automated_links()
    
    if not found_products:
        print("কোনো নতুন লিঙ্ক পাওয়া যায়নি।")
        return

    existing_links = sheet.col_values(3) # Column C (Product Link)
    
    for p in found_products:
        if p['link'] in existing_links: continue
            
        print(f"প্রসেসিং: {p['link']}")
        
        try:
            # এআই-কে নির্দেশ দেওয়া হচ্ছে তথ্য তৈরি করতে
            prompt = f"Product Link: {p['link']}. Pick a board from {BOARD_NAMES}. Return ONLY JSON: {{\"name\": \"...\", \"short_title\": \"...\", \"board\": \"...\"}}"
            
            ai_response = model.generate_content(prompt)
            clean_res = ai_response.text.strip().lstrip("```json").rstrip("```").strip()
            res_data = json.loads(clean_res)
            
            # আপনার শিটের টিক চিহ্ন দেওয়া কলামগুলো আপডেট (A, D, E, F, I)
            new_row = [
                res_data['name'],          # A: Product Name
                "Home & Kitchen",          # B: Category
                p['link'],                 # C: Product Link
                "https://m.media-amazon.com/images/I/placeholder.jpg", # D: Image URL
                res_data['board'],         # E: Board Name
                "Ready",                   # F: Post Status
                "Homeowners",              # G: Target Audience
                time.strftime("%Y-%m-%d"), # H: Date
                res_data['short_title']    # I: Short Title
            ]
            
            sheet.append_row(new_row)
            print("শিটে ৭ নম্বর সারি থেকে ডাটা সফলভাবে যোগ হয়েছে!")
            time.sleep(5)
            
        except Exception as e:
            print(f"ত্রুটি: {e}")

if __name__ == "__main__":
    run_automation()
