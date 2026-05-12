import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json

# ১. গুগল শিট কানেকশন
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
    print(f"শিট কানেকশন এরর: {str(e)}")

# ২. জেমিনি ডাটা সংগ্রহ (আপনার স্ক্রিনশটের মডেল অনুযায়ী)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    
    # আপনার স্ক্রিনশট image_d35590.png থেকে নেওয়া সঠিক নাম
    model = genai.GenerativeModel('gemini-3.1-flash-lite') 
    
    prompt = "Find 1 REAL Amazon kitchen tool. Format: Product Name | Amazon Link | Pinterest Title | Board Name | Image URL"
    
    response = model.generate_content(prompt)
    print(f"AI Response: {response.text}")
    
    data = response.text.strip().split('|')
    
    if len(data) >= 5:
        col_a = sheet.col_values(1)
        row_num = len(col_a) + 1
        
        # শিটে ডাটা এন্ট্রি
        sheet.update_cell(row_num, 1, data[0].strip()) # Product Name
        sheet.update_acell(f'C{row_num}', f'=HYPERLINK("{data[1].strip()}", "Amazon Link")') 
        sheet.update_acell(f'D{row_num}', f'=HYPERLINK("{data[4].strip()}", "Image URL")') 
        sheet.update_cell(row_num, 5, data[3].strip()) # Board Name
        sheet.update_cell(row_num, 6, "Ready")         # Status
        sheet.update_cell(row_num, 9, data[2].strip()) # Short Title
        
        print(f"সফলভাবে {row_num} নম্বর সারিতে ডাটা যোগ হয়েছে!")
    else:
        print("AI ফরম্যাট ঠিকমতো দিতে পারেনি।")

except Exception as e:
    print(f"জেমিনি এরর: {str(e)}")
