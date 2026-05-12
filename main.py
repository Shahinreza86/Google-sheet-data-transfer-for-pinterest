import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import requests
import time

# ১. কানেকশন ও শিট সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. এপিআই ও জেমিনি সেটআপ
SCRAPER_API_KEY = "6542b854201e09b17f31764b626395e4"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash-latest')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def run_automation():
    print("প্রথম ফাঁকা সারি খুঁজছি...")
    all_values = sheet.get_all_values()
    start_row = len(all_values) + 1 #
    
    # জেমিনিকে দিয়ে ১টি রিয়েল প্রোডাক্টের তথ্য জেনারেট করা
    prompt = f"""
    Find 1 trending and real Amazon.com product for the niche: 'Smart Kitchen & Home Organization'.
    You must provide:
    1. Product Name
    2. A working Amazon Product Link
    3. A direct high-quality Image URL
    4. Pinterest Title (Max 50 chars)
    5. Choose one board from: {BOARDS}
    
    Format: Name | Link | Title | Board | Image
    """
    
    try:
        response = model.generate_content(prompt)
        data = response.text.strip().split('|')
        
        if len(data) >= 5:
            p_name, p_link, p_title, p_board, p_image = [item.strip() for item in data[:5]]
            
            # ScraperAPI ব্যবহার করে লিঙ্কটি ভেরিফাই করা (আমাজন যাতে ব্লক না করে)
            scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={p_link}"
            print(f"প্রসেসিং রো {start_row}: {p_name}")

            # ৩. গুগল শিটে ডাটা আপডেট এবং নীল রঙের হাইপারলিঙ্ক তৈরি
            sheet.update_cell(start_row, 1, p_name) # Column A
            
            # লিঙ্ক নীল ও ক্লিকযোগ্য করা
            sheet.update_acell(f'C{start_row}', f'=HYPERLINK("{p_link}", "Check on Amazon")')
            sheet.update_acell(f'D{start_row}', f'=HYPERLINK("{p_image}", "View Image")')
            
            sheet.update_cell(start_row, 5, p_board) # Column E
            sheet.update_cell(start_row, 6, "Ready") # Column F
            sheet.update_cell(start_row, 9, p_title) # Column I

            print(f"সফলভাবে {start_row} নম্বর সারি পূরণ হয়েছে!")
        else:
            print("AI ডাটা ফরম্যাটে ভুল করেছে।")

    except Exception as e:
        print(f"ত্রুটি: {e}")

if __name__ == "__main__":
    run_automation()
