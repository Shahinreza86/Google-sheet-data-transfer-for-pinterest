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

# আপনার শিট আইডি
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0" 
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি সেটআপ (সর্বোচ্চ শক্তির জন্য প্রো ভার্সন)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-pro')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def run_automation():
    print("Scanning for the first empty row...")
    # শিটের কলাম A চেক করে প্রথম ফাঁকা রো বের করা
    col_a = sheet.col_values(1)
    start_row = len(col_a) + 1
    
    print(f"Targeting Row {start_row}...")

    # ৩. জেমিনিকে দিয়ে রিয়েল ডাটা বের করার প্রম্পট
    prompt = f"""
    Act as an expert Amazon Product Researcher. 
    Find 1 trending and real Amazon product in the 'Smart Kitchen & Home Gadgets' niche.
    Requirement:
    1. Product Name: Clean and short.
    2. Amazon URL: A direct working product link.
    3. Pinterest Title: Catchy (max 50 chars).
    4. Board: Select the best one from {BOARDS}.
    5. Image URL: A direct high-quality image link of that product.

    Response Format (Strictly): 
    Name | Link | Title | Board | Image
    """
    
    try:
        response = model.generate_content(prompt)
        data = response.text.strip().split('|')
        
        if len(data) >= 5:
            p_name = data[0].strip()
            p_link = data[1].strip()
            p_title = data[2].strip()
            p_board = data[3].strip()
            p_image = data[4].strip()

            # ৪. গুগল শিটে ডাটা আপডেট (HYPERLINK সহ)
            # Column A: Name
            sheet.update_cell(start_row, 1, p_name)
            
            # Column C: Product Link (Blue & Clickable)
            sheet.update_acell(f'C{start_row}', f'=HYPERLINK("{p_link}", "Check Product")')
            
            # Column D: Image URL (Blue & Clickable)
            sheet.update_acell(f'D{start_row}', f'=HYPERLINK("{p_image}", "View Image")')
            
            # Column E: Board
            sheet.update_cell(start_row, 5, p_board)
            
            # Column F: Status
            sheet.update_cell(start_row, 6, "Ready")
            
            # Column I: Short Title
            sheet.update_cell(start_row, 9, p_title)

            print(f"Successfully updated Row {start_row}")
        else:
            print("AI response format error. Retrying...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_automation()
