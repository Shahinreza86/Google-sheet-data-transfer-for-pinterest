import os
import json
import gspread
import google.generativeai as genai
from oauth2client.service_account import ServiceAccountCredentials
import requests
from bs4 import BeautifulSoup

# ১. সেটিংস ও ক্রেডেনশিয়াল (GitHub Secrets থেকে আসবে)
GOOGLE_SHEET_NAME = "Pinterest automatic pin post"
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GOOGLE_SERVICE_JSON = json.loads(os.environ["GOOGLE_SERVICE_JSON"])

# আপনার ৫টি পিন্টারেস্ট বোর্ডের সঠিক নাম
MY_BOARDS = [
    "Smart Home Organization & Storage Ideas",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Living Solutions & Home Tech",
    "DIY Home Improvement & Life Hacks",
    "Modern Kitchen Gadgets & Smart Tools"
]

# জেমিনি কনফিগারেশন - আপনার নির্দেশিত লেটেস্ট মডেল
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-flash-lite-latest') 

# ২. গুগল শিট কানেক্ট করা
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_SERVICE_JSON, scope)
client = gspread.authorize(creds)
sheet = client.open(GOOGLE_SHEET_NAME).sheet1

def get_ai_data(original_title):
    # জেমিনিকে দিয়ে শর্ট নাম এবং বোর্ড সিলেকশন করা
    prompt = f"""
    Product: {original_title}
    Boards: {', '.join(MY_BOARDS)}
    
    Task:
    1. Create a very short, catchy Pinterest title (max 5 words).
    2. Pick the most relevant board from the list above.
    
    Response format (JSON only):
    {{"short_title": "...", "selected_board": "..."}}
    """
    response = model.generate_content(prompt)
    # JSON ডাটা ক্লিন করা
    clean_response = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_response)

def run_automation():
    # সার্চ টার্ম: হোম এবং কিচেন ট্রেন্ডিং প্রোডাক্ট
    search_query = "trending smart home and kitchen gadgets 2026"
    url = f"https://www.amazon.com/s?k={search_query.replace(' ', '+')}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    # প্রথম ৫টি প্রোডাক্ট নিয়ে কাজ করবে
    products = soup.find_all("div", {"data-component-type": "s-search-result"})[:5]

    for product in products:
        try:
            full_name = product.h2.text.strip()
            img_url = product.find("img")['src']
            p_link = "https://www.amazon.com" + product.h2.a['href']
            
            # এআই দিয়ে প্রসেস করা (বোর্ড এবং শর্ট টাইটেল)
            ai_info = get_ai_data(full_name)
            
            # গুগল শিটে তথ্য পাঠানো (A, C, D, E, F, I কলাম)
            # কলাম বিন্যাস: [A: Product Name, B: Category, C: Link, D: Image URL, E: Board Name, F: Post Status, G: Target, H: Date, I: Short Title]
            row = [
                full_name, 
                "Home & Kitchen", 
                p_link, 
                img_url, 
                ai_info['selected_board'], 
                "Pending", 
                "Homeowners", 
                "2026-05-10", 
                ai_info['short_title']
            ]
            sheet.append_row(row)
            print(f"Added: {ai_info['short_title']} to {ai_info['selected_board']}")
        except Exception as e:
            print(f"Error: {e}")
            continue

if __name__ == "__main__":
    run_automation()
