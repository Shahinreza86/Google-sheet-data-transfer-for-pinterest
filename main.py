import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import re
from groq import Groq

# ১. গুগল শিট কানেকশন সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    # গিটহাব সিক্রেটস থেকে ক্রেডেনশিয়াল নেওয়া
    creds_json = os.environ.get("GOOGLE_SERVICE_JSON")
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # আপনার শিট আইডি
    SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
    sheet = client.open_by_key(SHEET_ID).sheet1
except Exception as e:
    print(f"Sheet Connection Error: {str(e)}")

# ২. Groq AI অটোমেশন (Llama 3 70B মডেল)
try:
    # গিটহাব সিক্রেট থেকে GROQ_API_KEY নেওয়া
    client_groq = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # ডুপ্লিকেট এড়াতে শিটের প্রথম কলামের ডাটা নেওয়া
    existing_products = sheet.col_values(1)

    prompt = f"""
    Suggest 1 REAL trending Amazon product for "Home & Kitchen Organization" today.
    Make sure it is highly aesthetic and practical.
    
    Exclude these recent items: {existing_products[-10:]}

    Pick one of these Pinterest boards:
    - Modern Kitchen Gadgets & Smart Tools
    - DIY Home Improvement & Life Hacks
    - Smart Living Solutions & Home Tech
    - Aesthetic Kitchen Decor & Interior Ideas
    - Smart Home Organization & Storage Ideas

    Response must be ONLY JSON format:
    {{
      "full_name": "Product Full Title",
      "short_title": "Clean Short Name",
      "link": "Amazon Product URL",
      "image": "Direct Media-Amazon Image URL",
      "board": "Selected Board Name"
    }}
    """
    
    # এআই থেকে রেসপন্স জেনারেট করা
    chat_completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
        temperature=0.7
    )
    
    response_text = chat_completion.choices[0].message.content
    
    # JSON ডাটা ক্লিন করে বের করা
    match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if match:
        product = json.loads(match.group())
        
        # ৩. গুগল শিটে ডাটা আপডেট করা
        row_num = len(existing_products) + 1
        sheet.update_cell(row_num, 1, product["full_name"])      # কলাম A
        sheet.update_cell(row_num, 3, product["link"])           # কলাম C
        sheet.update_cell(row_num, 4, product["image"])          # কলাম D
        sheet.update_cell(row_num, 5, product["board"])         # কলাম E
        sheet.update_cell(row_num, 6, "Ready")                  # কলাম F
        sheet.update_cell(row_num, 9, product["short_title"])   # কলাম I

        print(f"সফল! রো নম্বর {row_num}-এ ডাটা সেভ হয়েছে।")
    else:
        print("AI থেকে সঠিক ফরম্যাটে ডাটা পাওয়া যায়নি।")

except Exception as e:
    print(f"Groq API Error: {str(e)}")
