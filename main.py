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
model = genai.GenerativeModel('gemini-1.5-flash-latest')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def run_automation():
    print("Finding the first empty row...")
    all_values = sheet.get_all_values()
    start_row = len(all_values) + 1 # প্রথম ফাঁকা সারি
    
    # জেমিনিকে দিয়ে ১টি রিয়েল প্রোডাক্ট ডাটা জেনারেট করা
    prompt = f"""
    Find 1 trending and real Amazon product for the niche: 'Smart Kitchen & Home Organization'.
    Rules:
    - Must be a real product sold on Amazon.
    - Provide a working Amazon search link for that specific product.
    - Select one board from: {BOARDS}
    - Provide a high-quality direct image URL (use Unsplash or verified product image hosts).
    
    Format EXACTLY like this: 
    ProductName | AmazonLink | PinterestTitle | BoardName | ImageURL
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

            print(f"Updating Row {start_row} with {p_name}...")

            # কলাম অনুযায়ী ডাটা বসানো এবং লিঙ্ককে ক্লিকযোগ্য (Blue) করা
            # A: Product Name, C: Product Link, D: Image URL, E: Board Name, F: Status, I: Title
            sheet.update_cell(start_row, 1, p_name)
            
            # লিঙ্ক নীল এবং ক্লিকযোগ্য করার জন্য HYPERLINK ফর্মুলা ব্যবহার
            sheet.update_acell(f'C{start_row}', f'=HYPERLINK("{p_link}", "Click to View")')
            sheet.update_acell(f'D{start_row}', f'=HYPERLINK("{p_image}", "View Image")')
            
            sheet.update_cell(start_row, 5, p_board)
            sheet.update_cell(start_row, 6, "Ready")
            sheet.update_cell(start_row, 9, p_title)

            print(f"Success! Row {start_row} is now filled.")
        else:
            print("Gemini provided incomplete data. Retrying...")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_automation()
