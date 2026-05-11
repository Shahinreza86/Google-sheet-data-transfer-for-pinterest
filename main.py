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

def get_amazon_data():
    # অ্যামাজন থেকে ডাটা ডাইরেক্টলি স্ক্র্যাপ করার জন্য উন্নত প্রক্সি মেথড
    search_url = "https://www.amazon.com/s?k=trending+smart+kitchen+gadgets+2026"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/"
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")
        links = []
        for item in soup.select(".s-result-item[data-component-type='s-search-result']"):
            link_tag = item.select_one("h2 a")
            if link_tag:
                full_link = "https://www.amazon.com" + link_tag['href'].split('?')[0]
                links.append(full_link)
        return list(set(links))
    except:
        return []

def run_automation():
    links = get_amazon_data()
    if not links:
        print("Amazon detection issues. Using Gemini for real product discovery...")
        # যদি স্ক্র্যাপিং ফেইল করে, জেমিনি তার নলেজ থেকে আসল রিয়েল-লাইফ প্রোডাক্ট দিবে
        prompt = f"Give me 5 real trending Amazon product links for {BOARDS[0]}. Format: Link only."
        links = model.generate_content(prompt).text.split('\n')

    # ৩. প্রথম ফাঁকা রো (Empty Row) খুঁজে বের করা
    all_values = sheet.get_all_values()
    start_row = len(all_values) + 1 # যেখানে ডাটা শেষ, তার পরের লাইন
    
    print(f"Starting from empty row: {start_row}")
    link_idx = 0
    
    for i in range(start_row, start_row + 5): # একবারে ৫টি করে ঘর পূরণ করবে
        if link_idx < len(links):
            target_url = links[link_idx].strip()
            if "http" not in target_url: continue
            
            print(f"Processing Row {i}...")
            
            prompt = f"""
            Analyze this product link: {target_url}
            Provide: 1. Clean Name, 2. Pinterest Title (Max 50 chars), 3. Select Board from: {BOARDS}, 4. Direct Image URL.
            Format: Name | Title | Board | Image
            """
            
            try:
                response = model.generate_content(prompt)
                res = response.text.split('|')
                
                if len(res) >= 4:
                    sheet.update_cell(i, 1, res[0].strip()) # A: Product Name
                    sheet.update_cell(i, 3, target_url)     # C: Product Link
                    sheet.update_cell(i, 4, res[3].strip()) # D: Image URL
                    sheet.update_cell(i, 5, res[2].strip()) # E: Board Name
                    sheet.update_cell(i, 6, "Ready")        # F: Post Status
                    sheet.update_cell(i, 9, res[1].strip()) # I: Short Title
                    
                    print(f"Row {i} updated successfully!")
                    link_idx += 1
                    time.sleep(2)
            except Exception as e:
                print(f"Error at row {i}: {e}")

if __name__ == "__main__":
    run_automation()
