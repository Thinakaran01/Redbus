import chromedriver_autoinstaller
import os
import time
import gc
import csv
import pymysql
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

chromedriver_autoinstaller.install()

# ✅ Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Thilakkumar123",
    "database": "redbus",
    "port": 3306
}

# ✅ Initialize ChromeDriver
def get_driver():
    options = uc.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = uc.Chrome(service=service, options=options, headless=False)
    return driver

# ✅ Extract Bus Details from RedBus
def extract_bus_details(driver):
    bus_data = []
    MAX_RECORDS = 40
    URL = "https://www.redbus.in/bus-tickets/hyderabad-to-vijayawada?fromCityId=124&toCityId=134&fromCityName=Hyderabad&toCityName=Vijayawada&busType=Any&onward=20-Feb-2025"

    try:
        print("Opening RedBus website...")
        driver.get(URL)
        driver.maximize_window()
        time.sleep(6)  # Initial wait to load the page

        # ✅ Slower Scrolling to Ensure Data Loads
        for _ in range(10):  
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # ✅ Extract bus details
        buses = driver.find_elements(By.XPATH, '//div[@class="clearfix bus-item-details"]')
        if not buses:
            print("No buses found!")
            return []

        print(f"Found {len(buses)} buses.")

        for bus in buses[:MAX_RECORDS]:
            try:
                bus_name = bus.find_element(By.XPATH, ".//div[contains(@class,'travels')]").text
                bus_type = bus.find_element(By.XPATH, ".//div[contains(@class,'bus-type')]").text
                departing_time = bus.find_element(By.XPATH, ".//div[contains(@class,'dp-time')]").text
                duration = bus.find_element(By.XPATH, ".//div[contains(@class,'dur l-color lh-24')]").text
                reaching_time = bus.find_element(By.XPATH, ".//div[contains(@class,'bp-time')]").text
                star_rating = bus.find_element(By.XPATH, ".//div[contains(@class,'rating-sec')]").text or "N/A"
                price = bus.find_element(By.XPATH, ".//div[contains(@class,'fare d-block')]").text.replace("₹", "").strip()
                seat_availability = bus.find_element(By.XPATH, ".//div[contains(@class,'seat-left')]").text or "N/A"

                bus_data.append((bus_name, bus_type, departing_time, duration, reaching_time, star_rating, price, seat_availability))
                time.sleep(1)  # Small delay to prevent detection

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting bus details: {e}")

    return bus_data

# ✅ Save Data to CSV
def save_to_csv(bus_data):
    filename = "apsrtc2.csv"
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Bus Name", "Bus Type", "Departing Time", "Duration", "Reaching Time", "Star Rating", "Price", "Seat Availability"])
            writer.writerows(bus_data)

        print(f"Data saved to {filename}")

    except Exception as e:
        print(f"Error saving CSV file: {e}")

# ✅ Store Data in Database
def store_data_in_db(bus_data):
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS apsrtcinfo (
            id INT AUTO_INCREMENT PRIMARY KEY,
            Bus_name VARCHAR(255),
            Bus_type VARCHAR(255),
            Departing_time VARCHAR(50),
            Duration VARCHAR(50),
            Reaching_time VARCHAR(50),
            Star_rating VARCHAR(10),
            Price VARCHAR(50),
            Seat_availability VARCHAR(50)
        );
        """
        cursor.execute(create_table_query)

        insert_query = """
        INSERT INTO apsrtcinfo (Bus_name, Bus_type, Departing_time, Duration, Reaching_time, Star_rating, Price, Seat_availability)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.executemany(insert_query, bus_data)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"{len(bus_data)} bus records successfully stored in the database.")

    except pymysql.MySQLError as err:
        print(f"Database error: {err}")

# ✅ Cleanup WebDriver Properly
def cleanup(driver):
    if driver is not None:
        try:
            print("Closing WebDriver...")
            driver.quit()
        except Exception as e:
            print(f"Error while closing WebDriver: {e}")
        finally:
            gc.collect()
            print("WebDriver closed successfully.")

# ✅ MAIN SCRIPT
if __name__ == "__main__":
    driver = None
    try:
        driver = get_driver()  # Initialize WebDriver
        bus_data = extract_bus_details(driver)
        if bus_data:
            save_to_csv(bus_data)
            store_data_in_db(bus_data)
    finally:
        cleanup(driver)  # Ensure WebDriver is closed properly
        os._exit(0)  # 🚀 Force clean exit
