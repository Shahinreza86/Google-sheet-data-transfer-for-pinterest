import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ১. গুগল শিট ও জেমিনি সেটআপ
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

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash') # ফ্ল্যাশ মডেল ব্যবহার করা হয়েছে দ্রুত রেজাল্টের জন্য

BOARDS = [
    "Modern Kitchen Gadgets & Smart Tools",
    "DIY Home Improvement & Life Hacks",
    "Smart Living Solutions & Home Tech",
    "Aesthetic Kitchen Decor & Interior Ideas",
    "Smart Home Organization & Storage Ideas"
]

# ২. সেলেনিয়াম ব্রাউজার সেটআপ (Headless Mode)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=chrome_options)

def get_amazon_image(url):
    try:
        driver.get(url)
        time.sleep(3) # পেজ লোড হতে সময় দিন
        # অ্যামাজনের ছবির মূল সোর্স আইডি 'landingImage' অথবা 'main-image' থাকে
        img_element = driver.find_element(By.ID, "landingImage")
        return img_element.get_attribute("src")
    except:
        return "N/A"

def process_data():
    all_rows = sheet.get_all_values()
    
    for i, row in enumerate(all_rows[1:], start=2):
        # কলাম C-তে লিঙ্ক আছে কিনা এবং কলাম A ফাঁকা কিনা চেক করবে
        if len(row) > 2 and "amazon.com" in row[2].lower():
            if len(row) < 1 or not row[0].strip():
                product_link = row[2].strip()
                print(f"--- সারি {i} প্রসেস হচ্ছে ---")
                
                # ক. সেলেনিয়াম দিয়ে ইমেজ লিঙ্ক সংগ্রহ
                actual_image_url = get_amazon_image(product_link)
                
                # খ. জেমিনি দিয়ে ডাটা এনালাইসিস
                try:
                    prompt = f"""
                    Analyze this Amazon product link: {product_link}
                    Provide information for my Pinterest automation.
                    
                    Select ONE board from this list: {BOARDS}
                    
                    Format your response exactly like this:
                    NAME: [Full Detailed Product Name]
                    TITLE: [Short Catchy Title for Pinterest]
                    BOARD: [The selected board name]
                    """
                    
                    response = model.generate_content(prompt)
                    lines = response.text.split('\n')
                    
                    p_name = next((l.split('NAME:')[1] for l in lines if 'NAME:' in l), "N/A").strip()
                    p_title = next((l.split('TITLE:')[1] for l in lines if 'TITLE:' in l), "N/A").strip()
                    p_board = next((l.split('BOARD:')[1] for l in lines if 'BOARD:' in l), "N/A").strip()

                    # গ. গুগল শিট আপডেট (আপনার স্ক্রিনশট কলাম অনুযায়ী)
                    updates = [
                        {'range': f'A{i}', 'values': [[p_name]]},    # Product Name
                        {'range': f'D{i}', 'values': [[actual_image_url]]}, # Image URL
                        {'range': f'E{i}', 'values': [[p_board]]},   # Board Name
                        {'range': f'F{i}', 'values': [["Ready"]]},   # Post Status
                        {'range': f'I{i}', 'values': [[p_title]]}    # Short Title
                    ]
                    
                    for update in updates:
                        sheet.update(update['range'], update['values'])
                    
                    print(f"সারি {i} সফলভাবে সম্পন্ন হয়েছে।")
                    time.sleep(1) # API রেট লিমিট এড়াতে

                except Exception as e:
                    print(f"সারি {i} এ সমস্যা হয়েছে: {e}")

    driver.quit()

if __name__ == "__main__":
    process_data()
