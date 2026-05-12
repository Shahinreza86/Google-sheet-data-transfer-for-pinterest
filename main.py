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

# ২. জেমিনি অটোমেশন (লেটেস্ট মডেল এবং গুগল সার্চ লজিক)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # স্ক্রিনশট image_d1fbb4.png অনুযায়ী লেটেস্ট মডেল নাম
    model = genai.GenerativeModel(
        model_name='gemini-3.1-flash-lite',
        tools=[{"google_search_retrieval": {}}]
    )

    # ডুপ্লিকেট চেক করতে শিট থেকে ডাটা নেওয়া
    existing_products = sheet.col_values(1)

    prompt = f"""
    Find 1 trending Amazon product for Home/Kitchen today using Google Search.
    Check if it matches these boards:
    - Modern Kitchen Gadgets & Smart Tools
    - DIY Home Improvement & Life Hacks
    - Smart Living Solutions & Home Tech
    - Aesthetic Kitchen Decor & Interior Ideas
    - Smart Home Organization & Storage Ideas

    Exclude: {existing_products[-15:]}.
    You MUST provide a working Amazon link and a direct image link from media-amazon.com.
    Return ONLY JSON:
    {{"full_name": "...", "short_title": "...", "link": "...", "image": "...", "board": "..."}}
    """
    
    response = model.generate_content(prompt)
    
    # এরর ফ্রি ডাটা এক্সট্রাকশন
    match = re.search(r'\{.*\}', response.text, re.DOTALL)
    product = json.loads(match.group())
    
    # ৩. শিটে ডাটা এন্ট্রি
    row_num = len(existing_products) + 1
    sheet.update_cell(row_num, 1, product["full_name"])      # A: Product Name
    sheet.update_cell(row_num, 3, product["link"])           # C: Product Link
    sheet.update_cell(row_num, 4, product["image"])          # D: Image URL
    sheet.update_cell(row_num, 5, product["board"])         # E: Board Name
    sheet.update_cell(row_num, 6, "Ready")                  # F: Status
    sheet.update_cell(row_num, 9, product["short_title"])   # I: Short Title

    print(f"সফলভাবে ডাটা যোগ হয়েছে রো নম্বর: {row_num}")

except Exception as e:
    print(f"Final Error: {str(e)}")
