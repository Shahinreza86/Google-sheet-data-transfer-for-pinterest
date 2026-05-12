import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json

# ১. গুগল শিট কানেকশন সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds_json = os.environ.get("GOOGLE_SERVICE_JSON")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
    sheet = client.open_by_key(SHEET_ID).sheet1
    print("গুগল শিট কানেকশন সফল!")
except Exception as e:
    print(f"Sheet Error: {str(e)}")

# ২. জেমিনি অটোমেশন (৫টি বোর্ড লজিকসহ)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # আপনার আগের স্ক্রিনশট অনুযায়ী সঠিক মডেল নাম ব্যবহার করা হলো
    model = genai.GenerativeModel('gemini-3.1-flash-lite') 

    prompt = """
    Task: Find 1 trending Amazon Home/Kitchen product.
    
    Choose the most relevant board from this list:
    1. Modern Kitchen Gadgets & Smart Tools
    2. DIY Home Improvement & Life Hacks
    3. Smart Living Solutions & Home Tech
    4. Aesthetic Kitchen Decor & Interior Ideas
    5. Smart Home Organization & Storage Ideas

    Respond ONLY with a JSON object. Format:
    {
      "full_name": "Full Amazon Product Name",
      "short_title": "Very short catchy title",
      "link": "Direct Amazon Product URL",
      "image": "Direct Image URL",
      "selected_board": "Exact board name from list"
    }
    """
    
    response = model.generate_content(prompt)
    
    # এরর সমাধান: ডাটা ক্লিন করার নতুন ও নিরাপদ পদ্ধতি
    raw_text = response.text.strip()
    if raw_text.startswith('```json'):
        raw_text = raw_text.split('
```json')[1].split('```')[0].strip()
    elif raw_text.startswith('```'):
        raw_text = raw_text.split('
```')[1].split('```')[0].strip()
    
    product = json.loads(raw_text)
    
    # পরবর্তী ফাঁকা সারি খুঁজে বের করা
    col_a = sheet.col_values(1)
    row_num = len(col_a) + 1

    # ৩. শিটে ডাটা এন্ট্রি (image_d2dd0e.png এরর ফিক্সড)
    sheet.update_cell(row_num, 1, product["full_name"])      # Column A
    sheet.update_acell(f'C{row_num}', f'=HYPERLINK("{product["link"]}", "Product Link")') # Column C
    sheet.update_acell(f'D{row_num}', f'=HYPERLINK("{product["image"]}", "Image URL")') # Column D
    sheet.update_cell(row_num, 5, product["selected_board"]) # Column E
    sheet.update_cell(row_num, 6, "Ready")                  # Column F
    sheet.update_cell(row_num, 9, product["short_title"])   # Column I

    print(f"সফলভাবে ডাটা যোগ হয়েছে রো নম্বর: {row_num}")

except Exception as e:
    print(f"Automation Error: {str(e)}")
