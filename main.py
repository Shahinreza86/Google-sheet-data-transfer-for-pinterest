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

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# কীওয়ার্ড লিস্ট (এগুলোর ওপর ভিত্তি করে প্রোডাক্ট খুঁজবে)
SEARCH_KEYWORDS = ["Kitchen organization gadgets", "smart home storage ideas", "pantry organizer"]
BOARD_NAMES = ["Smart Home Organization", "Kitchen Storage Ideas", "Modern Kitchen Gadgets"]

# ==========================================
# ২. আমাজন সার্চ ও অটো-লিঙ্ক স্ক্র্যাপার
# ==========================================

def get_automated_links():
    keyword = random.choice(SEARCH_KEYWORDS)
    search_url = f"https://www.amazon.com/s?k={keyword.replace(' ', '+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    product_data = []
    try:
        response = requests.get(search_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")
        
        # আমাজন সার্চ রেজাল্ট থেকে প্রোডাক্ট ব্লকগুলো খোঁজা
        results = soup.select('[data-component-type="s-search-result"]')
        
        for item in results[:10]: # প্রথম ১০টি প্রোডাক্ট নিবে
            try:
                title_tag = item.select_one("h2 a span")
                link_tag = item.select_one("h2 a")
                img_tag = item.select_one("img")
                
                if title_tag and link_tag:
                    name = title_tag.text.strip()
                    link = "https://www.amazon.com" + link_tag['href']
                    # হাই রেজোলিউশন ইমেজ পাওয়ার চেষ্টা
                    image = img_tag.get('src') 
                    
                    product_data.append({"name": name, "link": link, "image": image})
            except:
                continue
    except Exception as e:
        print(f"Search Error: {e}")
        
    return product_data

# ==========================================
# ৩. জেমিনি এআই প্রসেসিং ও শিট আপডেট
# ==========================================

def run_fully_automatic():
    print("আমাজনে প্রোডাক্ট খোঁজা হচ্ছে...")
    found_products = get_automated_links()
    
    if not found_products:
        print("কোনো প্রোডাক্ট পাওয়া যায়নি।")
        return

    # শিটে আগে থেকে থাকা লিঙ্কগুলো চেক করা (ডুপ্লিকেট এড়াতে)
    existing_links = sheet.col_values(3) # Column C
    
    for p in found_products:
        if p['link'] in existing_links:
            continue # অলরেডি শিটে থাকলে বাদ দিবে
            
        print(f"প্রসেসিং: {p['name'][:50]}...")
        
        # জেমিনি দিয়ে শর্ট টাইটেল ও বোর্ড সিলেকশন
        prompt = f"Product: {p['name']}. Boards: {BOARD_NAMES}. Return ONLY JSON: {{\"short_title\": \"...\", \"board\": \"...\"}}"
        
        try:
            ai_response = model.generate_content(prompt)
            clean_res = ai_response.text.replace("```json", "").replace("```", "").strip()
            res_data = json.loads(clean_res)
            
            # নতুন রো (Row) হিসেবে শিটে ডাটা ইনসার্ট করা
            new_row = [
                p['name'],                 # A: Product Name
                "Kitchen & Home",          # B: Category
                p['link'],                 # C: Product Link
                p['image'],                # D: Image URL
                res_data['board'],          # E: Board Name
                "Ready",                   # F: Post Status
                "Homeowners",              # G: Target Audience
                time.strftime("%Y-%m-%d"), # H: Date
                res_data['short_title']     # I: Short Title
            ]
            
            sheet.append_row(new_row)
            print("শিটে সফলভাবে যোগ করা হয়েছে!")
            time.sleep(3) # ব্লক এড়াতে সামান্য গ্যাপ
            
        except Exception as e:
            print(f"AI/Sheet Error: {e}")

if __name__ == "__main__":
    run_fully_automatic()
