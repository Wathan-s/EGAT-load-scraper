import os
import re
import time
import requests
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_weather(api_key, city="Bangkok"):
    if not api_key:
        return "N/A", "No API Key"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},th&appid={api_key}&units=metric&lang=th"
    try:
        response = requests.get(url)
        data = response.json()
        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        return f"{temp} °C", weather_desc
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงสภาพอากาศ: {e}")
        return "N/A", "N/A"

def main():
    print("--- เริ่มต้นระบบบันทึกข้อมูล EGAT & Weather (โหมด Google Sheets) ---")
    weather_api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    
    os.makedirs("evidence", exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.sothailand.com/sysgen" 
        driver.get(url)
        print("กำลังโหลดหน้าเว็บ กฟผ...")
        
        page_text = ""
        for i in range(20):
            time.sleep(3)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "MW" in page_text: 
                print(f"✅ กราฟโหลดเสร็จแล้ว! ใช้เวลาไป { (i+1)*3 } วินาที")
                time.sleep(2)
                page_text = driver.find_element(By.TAG_NAME, "body").text 
                break
            print(f"กำลังรอหน้าเว็บโหลด... ({ (i+1)*3 } วินาที)")
            
        tz_th = timezone(timedelta(hours=7))
        now = datetime.now(tz_th)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        filename_time = now.strftime("%Y%m%d_%H%M%S")
        
        screenshot_name = f"evidence/egat_capture_{filename_time}.png"
        driver.save_screenshot(screenshot_name)
        print(f"บันทึกภาพสกรีนช็อตสำเร็จ: {screenshot_name}")
        
        try:
            match = re.search(r'ค่าปัจจุบัน\s*([\d,]+(?:\.\d+)?)\s*MW', page_text)
            if match:
                system_load = match.group(1).replace(",", "")
            else:
                system_load = "N/A"
        except Exception as ex:
            system_load = f"Error: {ex}"
            
        print("กำลังดึงข้อมูลสภาพอากาศ...")
        temp, weather_desc = get_weather(weather_api_key, "Bangkok")
        
        print("กำลังส่งข้อมูลเข้า Google Sheets...")
        # ========================================================
        # 🚨 เอาลิงก์ Web App URL ของคุณมาวางแทนที่ลิงก์ด้านล่างนี้ครับ 🚨
        sheet_url = "https://script.google.com/macros/s/xxxxxxxxx/exec" 
        # ========================================================
        
        payload = {
            "timestamp": timestamp,
            "system_load": system_load,
            "temp": temp,
            "weather": weather_desc,
            "image_ref": screenshot_name
        }
        
        response = requests.post(sheet_url, json=payload)
        if response.status_code == 200:
            print("✅ บันทึกข้อมูลลง Google Sheets สำเร็จ!")
        else:
            print(f"❌ ส่งข้อมูลไม่สำเร็จ: {response.text}")
            
    except Exception as e:
        print(f"เกิดข้อผิดพลาดหลัก: {e}")
    finally:
        driver.quit()
        print("--- สิ้นสุดการทำงาน ---")

if __name__ == "__main__":
    main()
