import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import re
from groq import Groq

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

# ২. Groq অটোমেশন (Llama 3 70B মডেল ব্যবহার করা হয়েছে)
try:
    # গিটহাবে GROQ_API_KEY নামে সিক্রেট অ্যাড করে নেবেন
    client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    existing_products = sheet.col_values(1)

    prompt = f"""
    Suggest 1 REAL trending Amazon product for Home/Kitchen organization. 
    Exclude: {existing_products[-10:]}.
    
    Pick 1 board:
    1. Modern Kitchen Gadgets & Smart Tools
    2. DIY Home Improvement & Life Hacks
    3. Smart Living Solutions & Home Tech
    4. Aesthetic Kitchen Decor & Interior Ideas
    5. Smart Home Organization & Storage Ideas

    Return ONLY a JSON object with a valid Amazon link and direct image URL:
    {{"full_name": "...", "short_title": "...", "link": "...", "image": "...", "board": "..."}}
    """
    
    chat_completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
    )
    
    response_text = chat_completion.choices[0].message.content
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    product = json.loads(match.group())
    
    # ৩. শিটে ডাটা বসানো
    row_num = len(existing_products) + 1
    sheet.update_cell(row_num, 1, product["full_name"])      # A
    sheet.update_cell(row_num, 3, product["link"])           # C
    sheet.update_cell(row_num, 4, product["image"])          # D
    sheet.update_cell(row_num, 5, product["board"])         # E
    sheet.update_cell(row_num, 6, "Ready")                  # F
    sheet.update_cell(row_num, 9, product["short_title"])   # I

    print(f"সফল! Groq দিয়ে নতুন প্রোডাক্ট যোগ হয়েছে।")

except Exception as e:
    print(f"Groq Error: {str(e)}")
