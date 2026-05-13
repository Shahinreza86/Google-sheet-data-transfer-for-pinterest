import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time

# ১. গুগল শিট কানেকশন সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# শিটের আইডি
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি এআই সেটআপ (আপনার রিকোয়েস্ট অনুযায়ী Lite মডেল)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

# আপনার নির্দিষ্ট বোর্ড লিস্ট
BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def process_data():
    # শিটের সব ডাটা রিড করা
    all_data = sheet.get_all_values()
    
    # ২ নম্বর সারি থেকে শেষ পর্যন্ত লুপ চালানো
    for i, row in enumerate(all_data[1:], start=2):
        # যদি কলাম C-তে লিঙ্ক থাকে এবং কলাম A ফাঁকা থাকে
        if len(row) > 2 and row[2].strip() and (len(row) < 1 or not row[0].strip()):
            product_link = row[2]
            print(f"সারি {i} প্রসেস করা হচ্ছে...")
            
            try:
                # জেমিনিকে দিয়ে ডাটা এবং ইমেজ লিঙ্ক বের করা
                prompt = f"""
                From this link: {product_link}, provide:
                1. Product Full Name
                2. Direct Product Image URL
                3. Short Title (max 50 chars)
                4. Select the best Board from this list only: {BOARDS}
                
                Format: Name | ImageURL | Title | Board
                """
                
                response = model.generate_content(prompt)
                result = response.text.split('|')
                
                if len(result) >= 4:
                    # কলাম অনুযায়ী ডাটা রাইট করা (আপনার শিট অনুযায়ী কলাম ম্যাপিং)
                    sheet.update_cell(i, 1, result[0].strip()) # A: Product Name
                    sheet.update_cell(i, 4, result[1].strip()) # D: Image URL
                    sheet.update_cell(i, 5, result[3].strip()) # E: Board Name
                    sheet.update_cell(i, 6, "Ready")           # F: Status
                    sheet.update_cell(i, 9, result[2].strip()) # I: Short Title
                    
                    print(f"সারি {i} সফলভাবে আপডেট হয়েছে!")
                    time.sleep(2) # কোটা সমস্যা এড়াতে বিরতি
                else:
                    print(f"সারি {i}-তে জেমিনি ডাটা দিতে পারেনি।")
            
            except Exception as e:
                print(f"Error in row {i}: {e}")

if __name__ == "__main__":
    process_data()
