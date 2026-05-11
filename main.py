import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json

# ১. গুগল শিট কানেকশন
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_SERVICE_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Pinterest automatic pin post").sheet1 

# ২. জেমিনি সেটআপ
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.Model('gemini-pro')

def process_data():
    # শিটের সব ডাটা নেওয়া
    records = sheet.get_all_records()
    
    # ৭ নম্বর সারি থেকে চেক করা (ইনডেক্স অনুযায়ী)
    for i, row in enumerate(records[5:], start=7): 
        if not row['Product Name']: # যদি নাম ফাঁকা থাকে
            # এখানে আপনার অ্যামাজন স্ক্র্যাপিং বা ডাটা সোর্স বসবে
            # আপাতত জেমিনিকে দিয়ে ডেমো ডাটা প্রসেস করার লজিক:
            
            product_name = "Amazon Large Product Name Here" # এটি স্ক্র্যাপার থেকে আসবে
            
            # জেমিনি দিয়ে শর্ট টাইটেল ও বোর্ড তৈরি
            prompt = f"Product: {product_name}. Give me: 1. Short Title, 2. Suitable Pinterest Board Name. Format: Title | Board"
            response = model.generate_content(prompt)
            result = response.text.split('|')
            
            short_title = result[0].strip()
            board_name = result[1].strip()

            # শিটে ডাটা আপডেট করা
            sheet.update_cell(i, 1, product_name) # Column A
            sheet.update_cell(i, 5, board_name)   # Column E (Board)
            sheet.update_cell(i, 9, short_title)  # Column I (Short Title)
            sheet.update_cell(i, 10, "Ready")     # Column J (Status)

            print(f"Row {i} updated successfully!")

if __name__ == "__main__":
    process_data()
