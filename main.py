import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time

# ১. গুগল শিট কানেকশন সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# আপনার শিটের আইডি
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি এআই সেটআপ (সবচেয়ে শক্তিশালী মডেল ব্যবহার করছি)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# আপনার নির্ধারিত বোর্ড লিস্ট
BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def process_data():
    all_rows = sheet.get_all_values()
    
    # সারি নম্বর ২ থেকে শুরু (হেডার বাদ দিয়ে)
    for i, row in enumerate(all_rows[1:], start=2):
        # শর্ত: কলাম C (index 2)-তে লিঙ্ক আছে কিন্তু কলাম A (index 0) ফাঁকা
        if len(row) > 2 and row[2].strip() != "" and (len(row) == 0 or row[0].strip() == ""):
            product_link = row[2]
            print(f"--- জেমিনি এখন ডাটা খুঁজছে সারি {i}-এর জন্য ---")
            
            try:
                # জেমিনিকে কমান্ড দেওয়া আমাজন থেকে সব তথ্য আনার জন্য
                prompt = f"""
                Visit/Analyze this Amazon link: {product_link}
                Extract the following details precisely:
                1. Product Full Name (Long title).
                2. Product Image URL (The main high-quality image link).
                3. Short Title (Catchy, under 50 chars).
                4. Select the most relevant board from this list: {BOARDS}
                
                Format the answer exactly like this:
                NAME: [product name]
                IMAGE: [image url]
                TITLE: [short title]
                BOARD: [board name]
                """
                
                response = model.generate_content(prompt)
                text = response.text
                
                # ডাটা আলাদা করা
                p_name = text.split("NAME:")[1].split("IMAGE:")[0].strip()
                p_image = text.split("IMAGE:")[1].split("TITLE:")[0].strip()
                p_title = text.split("TITLE:")[1].split("BOARD:")[0].strip()
                p_board = text.split("BOARD:")[1].strip()

                # শিটে কলাম অনুযায়ী ডাটা পাঠানো (আপনার ইমেজ অনুযায়ী কলাম ম্যাপিং)
                sheet.update_cell(i, 1, p_name)  # A: Product Name
                sheet.update_cell(i, 4, p_image) # D: Image URL
                sheet.update_cell(i, 5, p_board) # E: Board Name
                sheet.update_cell(i, 9, p_title) # I: Short Title
                sheet.update_cell(i, 6, "Ready") # F: Post Status
                
                print(f"সফলভাবে সারি {i} আপডেট হয়েছে!")
                time.sleep(2) #API রক্ষা করতে বিরতি

            except Exception as e:
                print(f"সারি {i}-তে সমস্যা হয়েছে: {e}")

if __name__ == "__main__":
    process_data()
