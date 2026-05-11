import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import requests
from bs4 import BeautifulSoup
import random

# ১. কানেকশন ও শিট সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি সেটআপ (আপনার দেওয়া মডেল নাম)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def get_amazon_products():
    # আপনার নিচ অনুযায়ী অ্যামাজন সার্চ ইউআরএল (Smart Kitchen/Home)
    search_url = "https://www.amazon.com/s?k=smart+kitchen+gadgets+and+home+organization"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    
    products = []
    # অ্যামাজন পেজ থেকে প্রোডাক্ট লিঙ্ক খুঁজে বের করা
    for item in soup.select(".s-result-item[data-component-type='s-search-result']"):
        link_tag = item.select_one("h2 a")
        if link_tag:
            full_link = "https://www.amazon.com" + link_tag['href']
            products.append(full_link)
    
    return list(set(products)) # ডুপ্লিকেট বাদ দেওয়া

def process_automation():
    data = sheet.get_all_values()
    found_links = get_amazon_products()
    link_index = 0
    
    # ৭ নম্বর সারি থেকে চেক করা
    for i, row in enumerate(data[6:], start=7): 
        # যদি প্রোডাক্ট নেম (A) এবং লিঙ্ক (C) দুইটাই ফাঁকা থাকে
        if not row[0] and not row[2]:
            if link_index < len(found_links):
                target_url = found_links[link_index]
                print(f"Finding data for row {i} from Amazon...")
                
                # জেমিনিকে দিয়ে ডাটা ক্লিন ও বোর্ড সিলেকশন করা
                prompt = f"""
                Analyze this Amazon product link: {target_url}
                Your niche is Smart Living & Kitchen. 
                1. Provide a short, professional Product Name.
                2. Provide a Catchy Title for Pinterest (max 50 chars).
                3. Choose best board from: {BOARDS}
                4. Give me the direct Image URL.
                
                Format: Name | Title | Board | Image
                """
                
                try:
                    response = model.generate_content(prompt)
                    res = response.text.split('|')
                    
                    if len(res) >= 4:
                        # শিটে ডাটা ইনপুট দেওয়া
                        sheet.update_cell(i, 1, res[0].strip()) # A: Product Name
                        sheet.update_cell(i, 3, target_url)     # C: Product Link (এখন অটো আসবে)
                        sheet.update_cell(i, 4, res[3].strip()) # D: Image URL
                        sheet.update_cell(i, 5, res[2].strip()) # E: Board Name
                        sheet.update_cell(i, 6, "Ready")        # F: Post Status
                        sheet.update_cell(i, 9, res[1].strip()) # I: Short Title
                        
                        print(f"Row {i} Success!")
                        link_index += 1
                except Exception as e:
                    print(f"Error at row {i}: {e}")

if __name__ == "__main__":
    process_automation()
