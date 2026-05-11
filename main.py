import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json

# ১. গুগল শিট কানেকশন সেটআপ (আইডি দিয়ে)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# আপনার শিটের আইডি এখানে বসান (এটি সব নামের সমস্যার সমাধান করবে)
SHEET_ID = "1HU9pEurbBvBfzPWmuRMkUtb0d6jpYKtnYY_YEAfkaF0ে" 
sheet = client.open_by_key(SHEET_ID).sheet1

# ২. জেমিনি এআই সেটআপ (আপনার দেওয়া হুবহু নাম অনুযায়ী)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-flash-lite-latest')

def process_data():
    data = sheet.get_all_values()
    
    # ৭ নম্বর সারি থেকে চেক করা শুরু
    for i, row in enumerate(data[6:], start=7): 
        # কলাম C-তে লিঙ্ক থাকতে হবে এবং কলাম A ফাঁকা থাকতে হবে
        if len(row) > 2 and row[2] and not row[0]:
            product_link = row[2]
            print(f"Processing row {i}...")
            
            try:
                # জেমিনিকে দিয়ে ডাটা প্রসেস করা
                prompt = f"From this link: {product_link}, provide: 1. Product Full Name, 2. Short Title (max 50 chars), 3. Pinterest Board. Format: Name | Title | Board"
                response = model.generate_content(prompt)
                
                result = response.text.split('|')
                if len(result) >= 3:
                    # শিটে ডাটা আপডেট (A, E, I, F কলাম)
                    sheet.update_cell(i, 1, result[0].strip()) # Product Name
                    sheet.update_cell(i, 5, result[2].strip()) # Board Name
                    sheet.update_cell(i, 9, result[1].strip()) # Short Title
                    sheet.update_cell(i, 6, "Ready")            # Post Status
                    print(f"Row {i} updated successfully!")
            except Exception as e:
                print(f"Error in row {i}: {e}")

if __name__ == "__main__":
    process_data()
