import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json

# ১. গুগল শিট কানেকশন সেটআপ
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# আপনার শিটের আইডি
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0"
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি এআই সেটআপ (Gemini Flash Lite)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

# আপনার নির্ধারিত পিন্টারেস্ট বোর্ড লিস্ট
BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

def process_data():
    data = sheet.get_all_values()
    
    # ৭ নম্বর সারি থেকে চেক করা শুরু
    for i, row in enumerate(data[6:], start=7): 
        # কলাম C-তে লিঙ্ক থাকতে হবে এবং কলাম A ফাঁকা থাকতে হবে
        if len(row) > 2 and row[2] and not row[0]:
            product_link = row[2]
            print(f"Processing row {i}...")
            
            try:
                # জেমিনিকে দিয়ে ডাটা প্রসেস করা এবং নির্দিষ্ট বোর্ড থেকে বাছাই করা
                prompt = f"""
                Analyze the context of this product link: {product_link}
                1. Provide Product Full Name.
                2. Provide a Short Title (max 50 chars).
                3. Strictly pick the most relevant board from this list: {BOARDS}
                
                Format the output exactly like this: Name | Title | Board
                """
                
                response = model.generate_content(prompt)
                result = response.text.split('|')
                
                if len(result) >= 3:
                    # শিটে ডাটা আপডেট (A, E, I, F কলাম)
                    sheet.update_cell(i, 1, result[0].strip()) # A: Product Name
                    sheet.update_cell(i, 5, result[2].strip()) # E: Board Name (আপনার লিস্ট থেকে)
                    sheet.update_cell(i, 9, result[1].strip()) # I: Short Title
                    sheet.update_cell(i, 6, "Ready")           # F: Status
                    print(f"Row {i} updated with Board: {result[2].strip()}")
                
            except Exception as e:
                print(f"Error in row {i}: {e}")

if __name__ == "__main__":
    process_data()
