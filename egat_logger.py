import os
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
    
    # 1. สร้างโฟลเดอร์สำหรับเก็บภาพสกรีนช็อต (ถ้ายังไม่มี)
    os.makedirs("evidence", exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.egat.co.th/home/power-status-realtime/" 
        driver.get(url)
        print("กำลังโหลดหน้าเว็บ กฟผ...")
        time.sleep(12) 
        
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        filename_time = now.strftime("%Y%m%d_%H%M%S")
        
        # 2. เซฟภาพสกรีนช็อทลงโฟลเดอร์ evidence โดยตรง
        screenshot_name = f"evidence/egat_capture_{filename_time}.png"
        driver.save_screenshot(screenshot_name)
        print(f"บันทึกภาพสกรีนช็อตสำเร็จ: {screenshot_name}")
        
        # 3. ดึงตัวเลขจากเว็บ (อย่าลืมตรวจสอบ XPath บนเว็บจริง)
        try:
            system_load = driver.find_element(By.XPATH, "//span[@id='sys-load']").text
            generation_mix = driver.find_element(By.XPATH, "//div[@id='gen-mix']").text
        except Exception:
            system_load = "N/A (ตรวจสอบ XPath)"
            generation_mix = "N/A"
            
        # 4. ดึงสภาพอากาศ
        print("กำลังดึงข้อมูลสภาพอากาศกรุงเทพฯ...")
        temp, weather_desc = get_weather(weather_api_key, "Bangkok")
        
        # 5. บันทึกข้อมูลต่อท้ายไฟล์ CSV
        csv_file = "dataset.csv"
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode="a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            # ถ้าไฟล์เพิ่งถูกสร้างครั้งแรก ให้เขียน Header ก่อน
            if not file_exists:
                writer.writerow(["วันเวลา", "System Load", "สัดส่วนพลังงาน", "อุณหภูมิ", "สภาพอากาศ", "ไฟล์อ้างอิง"])
            
            # เขียนข้อมูลของรอบนี้
            writer.writerow([timestamp, system_load, generation_mix, temp, weather_desc, screenshot_name])
            print("บันทึกข้อมูลลง dataset.csv สำเร็จ")
            
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
    finally:
        driver.quit()
        print("--- สิ้นสุดการทำงาน ---")

if __name__ == "__main__":
    main()
