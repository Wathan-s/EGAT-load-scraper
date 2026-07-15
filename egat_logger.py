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
        return "N/A", "N/A", "N/A", "No API Key"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},th&appid={api_key}&units=metric&lang=th"
    try:
        response = requests.get(url)
        data = response.json()
        temp = f'{data["main"]["temp"]} °C'
        humidity = f'{data["main"]["humidity"]} %'
        weather_desc = data["weather"][0]["description"]
        clouds = f'{data.get("clouds", {}).get("all", 0)} %' # ดึงค่าปริมาณเมฆ
        return temp, humidity, weather_desc, clouds
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงสภาพอากาศ: {e}")
        return "N/A", "N/A", "N/A", "N/A"

def main():
    print("--- เริ่มต้นระบบบันทึกข้อมูล EGAT & Weather ---")
    weather_api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    os.makedirs("evidence", exist_ok=True)
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = "https://www.sothailand.com/sysgen" 
        driver.get(url)
        
        page_text = ""
        for i in range(20):
            time.sleep(3)
            page_text = driver.find_element(By.TAG_NAME, "body").text
            if "MW" in page_text: 
                time.sleep(2)
                page_text = driver.find_element(By.TAG_NAME, "body").text 
                break
            
        tz_th = timezone(timedelta(hours=7))
        now = datetime.now(tz_th)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        filename_time = now.strftime("%Y%m%d_%H%M%S")
        
        # หาวันในสัปดาห์
        days_th = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
        day_of_week = days_th[now.weekday()]
        
        screenshot_name = f"evidence/egat_capture_{filename_time}.png"
        driver.save_screenshot(screenshot_name)
        
        # ดึงค่า System Load
        try:
            match = re.search(r'ค่าปัจจุบัน\s*([\d,]+(?:\.\d+)?)\s*MW', page_text)
            system_load = match.group(1).replace(",", "") if match else "N/A"
        except:
            system_load = "N/A"
            
        # ดึงสภาพอากาศ + ความชื้น + ปริมาณเมฆ
        temp, humidity, weather_desc, clouds = get_weather(weather_api_key, "Bangkok")
        
        # ========================================================
        sheet_url = "https://script.google.com/macros/s/AKfycbx4ujG3LIxvCYmAx783hNLAERGR1MVpQNkNVzvUTvPLYVvJn2gF5uQp2oBGDOAFAbE/exec" # ใส่ลิงก์ของคุณที่นี่
        # ========================================================
        
        payload = {
            "timestamp": timestamp,
            "day_of_week": day_of_week,
            "system_load": system_load,
            "temp": temp,
            "humidity": humidity,
            "weather": weather_desc,
            "clouds": clouds,
            "image_ref": screenshot_name
        }
        
        requests.post(sheet_url, json=payload)
        print("✅ ส่งข้อมูลเข้า Google Sheets สำเร็จ!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
