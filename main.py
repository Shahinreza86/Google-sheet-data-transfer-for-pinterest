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
except Exception as e:
    print(f"Sheet Connection Error: {str(e)}")

# ২. জেমিনি অটোমেশন (৫টি বোর্ড লজিকসহ)
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
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
      "short_title": "Very short catchy title (max 5-7 words)",
      "link": "Direct Amazon Product URL",
      "image": "Direct Image URL from media-amazon.com",
      "selected_board": "The exact name of the board from the list above"
    }
    """
    
    response = model.generate_content(prompt)
    # ক্লিন ডাটা এক্সট্রাক্ট করা
    clean_text = response.text.replace('```json', '').replace('
```', '').strip()
    product = json.loads(clean_text)
    
    # পরবর্তী ফাঁকা সারি খুঁজে বের করা
    col_a = sheet.col_values(1)
    row_num = len(col_a) + 1

    # ৩. শিটে ডাটা বসানো (আপনার স্ক্রিনশট image_d2ef1c.png অনুযায়ী)
    sheet.update_cell(row_num, 1, product["full_name"])      # Column A: Product Name
    sheet.update_acell(f'C{row_num}', f'=HYPERLINK("{product["link"]}", "Product Link")') # Column C: Link
    sheet.update_acell(f'D{row_num}', f'=HYPERLINK("{product["image"]}", "Image URL")') # Column D: Image URL
    sheet.update_cell(row_num, 5, product["selected_board"]) # Column E: Board Name (Auto-selected)
    sheet.update_cell(row_num, 6, "Ready")                  # Column F: Status
    sheet.update_cell(row_num, 9, product["short_title"])   # Column I: Short Title

    print(f"সাকসেস! বোর্ড '{product['selected_board']}' এর জন্য ডাটা সেভ হয়েছে।")

except Exception as e:
    print(f"Error: {str(e)}")
