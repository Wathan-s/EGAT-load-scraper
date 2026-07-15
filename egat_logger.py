import os
import re
import csv
import time
import requests
from datetime import datetime
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
    print("--- เริ่มต้นระบบบันทึกข้อมูล EGAT & Weather (โหมด CSV) ---")
    weather_api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    
    # 1. สร้างโฟลเดอร์สำหรับเก็บภาพสกรีนช็อต
    os.makedirs("evidence", exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu") # แก้ปัญหาจอดำ/จอโหลดบนเซิร์ฟเวอร์
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- ส่วนพรางตัวหลบ Firewall ---
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
        
        # --- ระบบรอแบบฉลาด (Smart Wait) ---
        page_text = ""
        for i in range(20): # วนลูปเช็คหน้าจอทุก 3 วินาที (สูงสุด 60 วินาที)
            time.sleep(3)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "MW" in page_text: 
                print(f"✅ กราฟโหลดเสร็จแล้ว! ใช้เวลาไป { (i+1)*3 } วินาที")
                time.sleep(2) # รอให้ตัวเลขนิ่ง
                # อัปเดตข้อความบนจออีกครั้งก่อนดึงข้อมูล
                page_text = driver.find_element(By.TAG_NAME, "body").text 
                break
            print(f"กำลังรอหน้าเว็บโหลด... ({ (i+1)*3 } วินาที)")
            
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        filename_time = now.strftime("%Y%m%d_%H%M%S")
        
        # 2. เซฟภาพสกรีนช็อท
        screenshot_name = f"evidence/egat_capture_{filename_time}.png"
        driver.save_screenshot(screenshot_name)
        print(f"บันทึกภาพสกรีนช็อตสำเร็จ: {screenshot_name}")
        
        # 3. ใช้ Regex หาตัวเลข (ล็อกเป้าหมายเฉพาะค่าปัจจุบัน)
        try:
            print("--- ข้อความที่บอทอ่านได้บนจอ ---")
            print(page_text) 
            print("------------------------------")

            # ล็อกเป้าหมาย: หาตัวเลขที่อยู่ติดกับคำว่า "ค่าปัจจุบัน" เท่านั้น
            match = re.search(r'ค่าปัจจุบัน\s*([\d,]+(?:\.\d+)?)\s*MW', page_text)
            
            if match:
                system_load = match.group(1) # ดึงตัวเลขที่อยู่ในวงเล็บของ Regex มาใช้
            else:
                system_load = "N/A (หาตัวเลขไม่เจอ)"
                
            generation_mix = "N/A" 
            
        except Exception as ex:
            system_load = f"Error: {ex}"
            generation_mix = "N/A"
            
        # 4. ดึงสภาพอากาศ
        print("กำลังดึงข้อมูลสภาพอากาศกรุงเทพฯ...")
        temp, weather_desc = get_weather(weather_api_key, "Bangkok")
        
        # 5. บันทึกข้อมูล
        csv_file = "dataset.csv"
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["วันเวลา", "System Load", "สัดส่วนพลังงาน", "อุณหภูมิ", "สภาพอากาศ", "ไฟล์อ้างอิง"])
            
            writer.writerow([timestamp, system_load, generation_mix, temp, weather_desc, screenshot_name])
            print("บันทึกข้อมูลลง dataset.csv สำเร็จ")
            
    except Exception as e:
        print(f"เกิดข้อผิดพลาดหลัก: {e}")
    finally:
        driver.quit()
        print("--- สิ้นสุดการทำงาน ---")

if __name__ == "__main__":
    main()
