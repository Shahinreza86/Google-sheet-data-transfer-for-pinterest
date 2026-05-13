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
    # শিটের সব ডাটা রিড করা
    all_rows = sheet.get_all_values()
    print(f"Total rows found: {len(all_rows)}")

    # সারি নম্বর ২ থেকে শেষ পর্যন্ত লুপ চলবে
    for i, row in enumerate(all_rows[1:], start=2):
        # কলাম C (index 2) তে যদি আমাজন লিঙ্ক থাকে, তবেই কাজ করবে
        if len(row) > 2 and "amazon.com" in row[2].lower():
            product_link = row[2].strip()
            print(f"--- Processing Row {i}: {product_link} ---")
            
            try:
                # জেমিনিকে দিয়ে ডাটা তৈরি
                prompt = f"""
                Analyze this Amazon product: {product_link}
                Provide exactly in this format:
                Name: [Product Full Name]
                Title: [Short Title, max 50 chars]
                Image: [Main Product Image URL]
                Board: [Pick one from {BOARDS}]
                """
                
                response = model.generate_content(prompt)
                res_text = response.text
                
                # সহজভাবে ডাটা এক্সট্রাক্ট করা
                lines = res_text.split('\n')
                p_name = next((l.split('Name:')[1] for l in lines if 'Name:' in l), "N/A").strip()
                p_title = next((l.split('Title:')[1] for l in lines if 'Title:' in l), "N/A").strip()
                p_image = next((l.split('Image:')[1] for l in lines if 'Image:' in l), "N/A").strip()
                p_board = next((l.split('Board:')[1] for l in lines if 'Board:' in l), "N/A").strip()

                # সরাসরি শিট আপডেট (একদম নির্দিষ্ট কলামে)
                sheet.update_cell(i, 1, p_name)   # A: Product Name
                sheet.update_cell(i, 4, p_image)  # D: Image URL
                sheet.update_cell(i, 5, p_board)  # E: Board Name
                sheet.update_cell(i, 6, "Done")   # F: Post Status
                sheet.update_cell(i, 9, p_title)  # I: Short Title
                
                print(f"Row {i} successfully updated in Google Sheet!")
                time.sleep(2) # কোটা বাঁচানোর জন্য ছোট বিরতি
                
            except Exception as e:
                print(f"Error processing row {i}: {e}")
        else:
            print(f"Row {i} skipped: No valid Amazon link in Column C.")

if __name__ == "__main__":
    process_data()
