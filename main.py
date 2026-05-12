import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import re

# ১. গুগল শিট কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds_json = os.environ.get("GOOGLE_SERVICE_JSON")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    print(f"Sheet Error: {str(e)}")

# ২. জেমিনি অটোমেশন (ডুপ্লিকেট চেকসহ)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-3.1-flash-lite') 

    # শিট থেকে আগের সব প্রোডাক্টের নাম নেওয়া
    existing_products = sheet.col_values(1)

    prompt = f"""
    Find 1 NEW trending Amazon product for Home/Kitchen. 
    Exclude these products: {existing_products[-10:]} (Do not pick these).
    
    Choose exactly 1 board from:
    1. Modern Kitchen Gadgets & Smart Tools
    2. DIY Home Improvement & Life Hacks
    3. Smart Living Solutions & Home Tech
    4. Aesthetic Kitchen Decor & Interior Ideas
    5. Smart Home Organization & Storage Ideas

    Important: Provide a high-quality direct .jpg image URL from Amazon.
    Return ONLY a JSON object:
    {{"full_name": "...", "short_title": "...", "link": "...", "image": "...", "board": "..."}}
    """
    
    response = model.generate_content(prompt)
    match = re.search(r'\{.*\}', response.text, re.DOTALL)
    product = json.loads(match.group())
    
    row_num = len(existing_products) + 1

    # ৩. শিটে ডাটা এন্ট্রি (লিংক এবং ইমেজ ফিক্সসহ)
    sheet.update_cell(row_num, 1, product["full_name"])      # Column A
    sheet.update_cell(row_num, 3, product["link"])           # Column C (Direct Link)
    sheet.update_cell(row_num, 4, product["image"])          # Column D (Direct Image URL)
    sheet.update_cell(row_num, 5, product["board"])         # Column E
    sheet.update_cell(row_num, 6, "Ready")                  # Column F
    sheet.update_cell(row_num, 9, product["short_title"])   # Column I

    print(f"সফলভাবে নতুন প্রোডাক্ট '{product['full_name']}' যোগ হয়েছে।")

except Exception as e:
    print(f"Error: {str(e)}")
