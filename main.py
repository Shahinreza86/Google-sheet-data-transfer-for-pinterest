import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time

# ১. গুগল শিট কানেকশন
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

# ২. জেমিনি সেটআপ (Gemini 1.5 Flash ব্যবহার করা হয়েছে)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

def run_automation():
    try:
        # পরবর্তী ফাঁকা সারি খুঁজে বের করা
        col_a = sheet.col_values(1)
        start_row = len(col_a) + 1
        print(f"টার্গেট রো: {start_row}")

        # প্রম্পটটি আরও পরিষ্কার করা হয়েছে
        prompt = "Find 1 REAL Amazon kitchen tool. Respond ONLY in this format: Product Name | Amazon Link | Pinterest Title | Board Name | Image URL"
        
        response = model.generate_content(prompt)
        text_response = response.text.strip()
        print(f"AI Response: {text_response}") # এটি গিটহাব লগে দেখতে পাবেন

        raw_data = text_response.split('|')

        if len(raw_data) >= 5:
            p_name = raw_data[0].strip()
            p_link = raw_data[1].strip()
            p_title = raw_data[2].strip()
            p_board = raw_data[3].strip()
            p_image = raw_data[4].strip()
            
            # ৩. গুগল শিটে ডাটা পাঠানো
            # Column A: Product Name
            sheet.update_cell(start_row, 1, p_name)
            # Column C: Product Link (Hyperlink)
            sheet.update_acell(f'C{start_row}', f'=HYPERLINK("{p_link}", "Check Product")')
            # Column D: Image URL (Hyperlink)
            sheet.update_acell(f'D{start_row}', f'=HYPERLINK("{p_image}", "View Image")')
            # Column E: Board Name
            sheet.update_cell(start_row, 5, p_board)
            # Column F: Status
            sheet.update_cell(start_row, 6, "Ready")
            # Column I: Short Title
            sheet.update_cell(start_row, 9, p_title)

            print(f"সফলভাবে {start_row} নম্বর সারিতে ডাটা যোগ হয়েছে!")
        else:
            print("AI থেকে সঠিক ফরম্যাটে তথ্য আসেনি। আবার চেষ্টা করুন।")

    except Exception as e:
        print(f"Runtime Error: {e}")

if __name__ == "__main__":
    run_automation()
