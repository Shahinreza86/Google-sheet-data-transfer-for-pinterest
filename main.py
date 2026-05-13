import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time

# ১. গুগল শিট কানেকশন সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    print(f"Credentials Error: {e}")
    exit()

SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি এআই সেটআপ
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def process_data():
    all_rows = sheet.get_all_values()
    
    # ২ নম্বর সারি থেকে শুরু
    for i, row in enumerate(all_rows[1:], start=2):
        # কলাম C (index 2)-তে লিঙ্ক থাকলে কাজ করবে
        if len(row) > 2 and "amazon.com" in row[2].lower():
            # চেক করবে কলাম A (index 0) কি ফাঁকা? তাহলেই শুধু প্রসেস করবে
            if len(row) < 1 or not row[0].strip():
                product_link = row[2].strip()
                print(f"--- সারি {i} প্রসেস হচ্ছে ---")
                
                try:
                    # জেমিনিকে ইমেজ লিঙ্কের ব্যাপারে কড়া নির্দেশ দেওয়া
                    prompt = f"""
                    Analyze this link: {product_link}
                    I need four specific things. Ensure the IMAGE URL is a direct link to the actual product picture (not a 'Not Found' page).
                    
                    Format your response exactly like this:
                    NAME: [Product Full Name]
                    TITLE: [Short Catchy Title]
                    IMAGE: [Direct Image URL starting with https://m.media-amazon.com/images/I/...]
                    BOARD: [Select one from {BOARDS}]
                    """
                    
                    response = model.generate_content(prompt)
                    lines = response.text.split('\n')
                    
                    p_name = next((l.split('NAME:')[1] for l in lines if 'NAME:' in l), "N/A").strip()
                    p_title = next((l.split('TITLE:')[1] for l in lines if 'TITLE:' in l), "N/A").strip()
                    p_image = next((l.split('IMAGE:')[1] for l in lines if 'IMAGE:' in l), "N/A").strip()
                    p_board = next((l.split('BOARD:')[1] for l in lines if 'BOARD:' in l), "N/A").strip()

                    # কলাম অনুযায়ী ডাটা রাইট করা
                    sheet.update_cell(i, 1, p_name)   # A: Name
                    sheet.update_cell(i, 4, p_image)  # D: Image URL
                    sheet.update_cell(i, 5, p_board)  # E: Board
                    sheet.update_cell(i, 6, "Ready")  # F: Post Status (এখন "Ready" আসবে)
                    sheet.update_cell(i, 9, p_title)  # I: Short Title
                    
                    print(f"সারি {i} সফলভাবে আপডেট হয়েছে (Status: Ready)")
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"সারি {i} এরর: {e}")

if __name__ == "__main__":
    process_data()
