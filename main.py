import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import requests
from bs4 import BeautifulSoup
import time

# ১. কানেকশন ও শিট সেটআপ
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

def get_amazon_links():
    # অ্যামাজন ব্লক এড়াতে উন্নত হেডার সেটআপ
    url = "https://www.amazon.com/s?k=smart+kitchen+gadgets+essentials+2026"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")
        links = []
        
        # প্রোডাক্ট লিঙ্কগুলো খুঁজে বের করা
        for a in soup.select('h2 a.a-link-normal'):
            link = "https://www.amazon.com" + a['href']
            if "/dp/" in link and "ref=" in link:
                links.append(link.split("ref=")[0]) # লিঙ্ক ক্লিন করা
        
        return list(set(links)) # ডুপ্লিকেট বাদ
    except Exception as e:
        print(f"Scraping Error: {e}")
        return []

def process_automation():
    links = get_amazon_links()
    if not links:
        print("No products found. Amazon might be blocking the request. Try again later.")
        return

    print(f"Found {len(links)} products. Updating sheet...")
    link_idx = 0
    
    # ৮ নম্বর সারি থেকে শুরু করা হচ্ছে
    for i in range(8, 25): 
        row_data = sheet.row_values(i)
        
        # যদি ঘরটি খালি থাকে (Column A)
        if not row_data or not row_data[0]:
            if link_idx < len(links):
                target_url = links[link_idx]
                
                # জেমিনিকে দিয়ে ডাটা সাজানো
                prompt = f"""
                Product Link: {target_url}
                Act as an affiliate marketer for Smart Kitchen niche.
                1. Product Name (Clean & Short)
                2. Pinterest Title (Max 50 chars)
                3. Choose Board from: {BOARDS}
                4. Image URL of the product
                Format: Name | Title | Board | Image
                """
                
                try:
                    response = model.generate_content(prompt)
                    res = response.text.split('|')
                    
                    if len(res) >= 4:
                        # সঠিক কলামে ডাটা পাঠানো
                        sheet.update_cell(i, 1, res[0].strip()) # A: Product Name
                        sheet.update_cell(i, 3, target_url)     # C: Product Link
                        sheet.update_cell(i, 4, res[3].strip()) # D: Image URL
                        sheet.update_cell(i, 5, res[2].strip()) # E: Board Name
                        sheet.update_cell(i, 6, "Ready")        # F: Post Status
                        sheet.update_cell(i, 9, res[1].strip()) # I: Short Title
                        
                        print(f"Row {i} Success!")
                        link_idx += 1
                        time.sleep(2) # গুগল শিটের এপিআই রেট লিমিট এড়াতে বিরতি
                except Exception as e:
                    print(f"Error at row {i}: {e}")

if __name__ == "__main__":
    process_automation()
