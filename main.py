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

# আপনার শিটের নাম এখানে হুবহু পিন্টারেস্ট থেকে নেওয়া (স্পেসসহ)
sheet = client.open("Pinterest automatic pin post").sheet1

# ২. জেমিনি এআই সেটআপ (নতুন ভার্সন অনুযায়ী সংশোধিত)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash') # এখানে 'Model' এর বদলে 'GenerativeModel' হবে

def process_data():
    # শিটের ৭ নম্বর সারি থেকে ডাটা চেক করা
    data = sheet.get_all_values()
    
    # ৭ নম্বর সারি থেকে লুপ শুরু হচ্ছে
    for i, row in enumerate(data[6:], start=7): 
        # কলাম C (ইনডেক্স ২) তে লিঙ্ক থাকতে হবে এবং কলাম A (ইনডেক্স ০) ফাঁকা থাকতে হবে
        product_link = row[2] 
        
        if product_link and not row[0]:
            print(f"Processing row {i}...")
            
            # জেমিনিকে দিয়ে ডাটা প্রসেস করার প্রম্পট
            prompt = f"Extract product name from this link: {product_link}. Then provide: 1. Short Title, 2. Suitable Pinterest Board. Format: Name | Title | Board"
            
            response = model.generate_content(prompt)
            result = response.text.split('|')
            
            if len(result) >= 3:
                full_name = result[0].strip()
                short_title = result[1].strip()
                board_name = result[2].strip()

                # শিটে ডাটা আপডেট করা (কলাম A, E, I, J)
                sheet.update_cell(i, 1, full_name)   # কলাম A: Product Name
                sheet.update_cell(i, 5, board_name)  # কলাম E: Board Name
                sheet.update_cell(i, 9, short_title) # কলাম I: Short Title
                sheet.update_cell(i, 6, "Ready")      # কলাম F: Post Status
                
                print(f"Row {i} updated successfully!")

if __name__ == "__main__":
    process_data()
