import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
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

def process_automation():
    print("Generating trending product data using Gemini...")
    
    # জেমিনিকে বলা হচ্ছে ৫টি প্রোডাক্টের ডাটা তৈরি করতে
    prompt = f"""
    Generate 5 trending Amazon products for the niche: 'Smart Living & Kitchen Organization'.
    For each product, provide:
    1. Product Name
    2. A search link for Amazon (e.g., https://www.amazon.com/s?k=product+name)
    3. A Pinterest Title (Max 50 chars)
    4. One board from this list: {BOARDS}
    5. A placeholder image URL from Unsplash related to kitchen/home.
    
    Format: Name | SearchLink | Title | Board | Image
    Separate each product with a new line.
    """
    
    try:
        response = model.generate_content(prompt)
        product_list = response.text.strip().split('\n')
        
        row_to_fill = 8 # ৮ নম্বর সারি থেকে শুরু
        
        for item in product_list:
            res = item.split('|')
            if len(res) >= 5:
                # শিটে ডাটা ইনপুট দেওয়া (A, C, D, E, F, I কলাম)
                sheet.update_cell(row_to_fill, 1, res[0].strip()) # A: Product Name
                sheet.update_cell(row_to_fill, 3, res[1].strip()) # C: Product Link (Search Link)
                sheet.update_cell(row_to_fill, 4, res[4].strip()) # D: Image URL
                sheet.update_cell(row_to_fill, 5, res[3].strip()) # E: Board Name
                sheet.update_cell(row_to_fill, 6, "Ready")        # F: Post Status
                sheet.update_cell(row_to_fill, 9, res[2].strip()) # I: Short Title
                
                print(f"Row {row_to_fill} updated with: {res[0].strip()}")
                row_to_fill += 1
                time.sleep(2) # API লিমিট এড়াতে
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    process_automation()
