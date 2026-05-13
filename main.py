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

# আপনার শিটের আইডি
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি এআই সেটআপ (আপনার পছন্দের Lite মডেল)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

# পিন্টারেস্ট বোর্ড লিস্ট
BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def process_data():
    all_rows = sheet.get_all_values()
    
    # ৭ নম্বর সারি থেকে চেক করা শুরু (আপনি চাইলে ২ নম্বর থেকেও করতে পারেন)
    for i, row in enumerate(all_rows[6:], start=7): 
        # কলাম C (index 2)-তে লিঙ্ক থাকলেই সে কাজ শুরু করবে
        if len(row) > 2 and row[2].strip():
            product_link = row[2]
            print(f"--- সারি {i} প্রসেস হচ্ছে ---")
            
            try:
                # জেমিনিকে দিয়ে বিস্তারিত তথ্য বের করা
                prompt = f"""
                Visit/Analyze this link: {product_link}
                Strictly provide:
                1. Product Full Name
                2. Direct Product Image URL
                3. Catchy Short Title (max 50 chars)
                4. Select ONE board from: {BOARDS}
                
                Format: Name | ImageURL | ShortTitle | Board
                """
                
                response = model.generate_content(prompt)
                parts = response.text.split('|')
                
                if len(parts) >= 4:
                    # শিট আপডেট (কলাম নম্বর আপনার স্ক্রিনশট অনুযায়ী)
                    sheet.update_cell(i, 1, parts[0].strip()) # A: Name
                    sheet.update_cell(i, 4, parts[1].strip()) # D: Image URL
                    sheet.update_cell(i, 5, parts[3].strip()) # E: Board
                    sheet.update_cell(i, 6, "Ready")           # F: Status
                    sheet.update_cell(i, 9, parts[2].strip()) # I: Short Title
                    
                    print(f"সফল! সারি {i} আপডেট হয়েছে।")
                    time.sleep(2) # API রেট লিমিট রক্ষা
                else:
                    print(f"সারি {i}: জেমিনি অসম্পূর্ণ ডাটা দিয়েছে।")
                    
            except Exception as e:
                print(f"সারি {i} এরর: {e}")

if __name__ == "__main__":
    process_data()
