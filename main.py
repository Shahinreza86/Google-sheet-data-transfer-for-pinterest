import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import requests
from bs4 import BeautifulSoup

# ১. গুগল শিট কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# আপনার শিট আইডি
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
    # সার্চ টার্ম আরও সুনির্দিষ্ট করা হয়েছে
    url = "https://www.amazon.com/s?k=smart+home+kitchen+organization+gadgets"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        links = []
        for a in soup.select('h2 a.a-link-normal'):
            link = "https://www.amazon.com" + a['href']
            if "/dp/" in link:
                links.append(link)
        return list(set(links))
    except Exception as e:
        print(f"Scraping Error: {e}")
        return []

def run_automation():
    links = get_amazon_data()
    if not links:
        print("No products found from Amazon. Try running again or check search term.")
        return

    data = sheet.get_all_values()
    link_idx = 0
    
    # ৮ নম্বর সারি থেকে ডাটা বসানো শুরু হবে
    for i in range(8, 20): # ৮ থেকে ২০ নম্বর সারি পর্যন্ত চেক করবে
        current_row = sheet.row_values(i)
        # যদি প্রথম কলাম (A) ফাঁকা থাকে
        if not current_row or not current_row[0]:
            if link_idx < len(links):
                target_url = links[link_idx]
                print(f"Processing Row {i}...")
                
                prompt = f"Product Link: {target_url}. Provide: 1. Clean Product Name, 2. Pinterest Title (Max 50 chars), 3. Select one board from {BOARDS}, 4. Direct Image URL. Format: Name | Title | Board | Image"
                
                try:
                    response = model.generate_content(prompt)
                    parts = response.text.split('|')
                    if len(parts) >= 4:
                        # শিট আপডেট
                        sheet.update_cell(i, 1, parts[0].strip()) # A: Product Name
                        sheet.update_cell(i, 3, target_url)        # C: Product Link
                        sheet.update_cell(i, 4, parts[3].strip()) # D: Image URL
                        sheet.update_cell(i, 5, parts[2].strip()) # E: Board Name
                        sheet.update_cell(i, 6, "Ready")           # F: Post Status
                        sheet.update_cell(i, 9, parts[1].strip()) # I: Short Title
                        link_idx += 1
                        print(f"Updated Row {i}")
                except Exception as e:
                    print(f"Row {i} Error: {e}")

if __name__ == "__main__":
    run_automation()
