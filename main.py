import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import requests
import time

# ১. কানেকশন ও শিট সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

try:
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    print("গুগল শিট কানেকশন সফল!")
except Exception as e:
    print(f"Auth Error: {e}")

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি ও স্ক্র্যাপার এপিআই সেটআপ (আপনার পছন্দের মডেলসহ)
SCRAPER_API_KEY = "6542b854201e09b17f31764b626395e4"
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# আপনার স্ক্রিনশট অনুযায়ী মডেলের নাম সেট করা হয়েছে
model = genai.GenerativeModel('gemini-1.5-flash-latest') 

def run_automation():
    try:
        print("শিট চেক করছি...")
        col_a = sheet.col_values(1)
        start_row = len(col_a) + 1
        print(f"টার্গেট রো: {start_row}")

        prompt = "Find 1 REAL Amazon kitchen tool. Format: Name | Link | Title | Board | Image"
        
        # জেমিনি থেকে ডাটা জেনারেট
        response = model.generate_content(prompt)
        raw_data = response.text.strip().split('|')

        if len(raw_data) >= 5:
            p_name, p_link, p_title, p_board, p_image = [i.strip() for i in raw_data[:5]]
            
            print(f"তথ্য পাওয়া গেছে: {p_name}")

            # ৩. গুগল শিটে ডাটা পাঠানো (হাইপারলিঙ্কসহ)
            sheet.update_cell(start_row, 1, p_name)
            sheet.update_acell(f'C{start_row}', f'=HYPERLINK("{p_link}", "Check Product")')
            sheet.update_acell(f'D{start_row}', f'=HYPERLINK("{p_image}", "View Image")')
            sheet.update_cell(start_row, 5, p_board)
            sheet.update_cell(start_row, 6, "Ready")
            sheet.update_cell(start_row, 9, p_title)

            print(f"অভিনন্দন! {start_row} নম্বর সারিতে ডাটা সফলভাবে যোগ হয়েছে।")
        else:
            print("জেমিনি থেকে আসা তথ্যের ফরম্যাট ঠিক নেই।")

    except Exception as e:
        print(f"কাজে বাধা এসেছে: {e}")

if __name__ == "__main__":
    run_automation()
