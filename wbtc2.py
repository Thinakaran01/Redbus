import sys
import os
import time
import gc  # Garbage Collector
import pymysql
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ✅ Database Configuration
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Thilakkumar123",
    "database": "redbus",
    "port": 3306
}

# ✅ Initialize Chrome Driver
options = uc.ChromeOptions()
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

service = Service(ChromeDriverManager().install())
driver = uc.Chrome(service=service, options=options, headless=False)

# ✅ Extract Bus Details
def extract_bus_details():
    bus_data = []
    MAX_RECORDS = 40

    try:
        print("Opening RedBus website...")
        driver.get("https://www.redbus.in/bus-tickets/kolkata-to-digha")
        driver.maximize_window()
        time.sleep(5)

        # ✅ Take screenshot for debugging
        driver.save_screenshot("redbus_page.png")
        print("Screenshot taken: redbus_page.png")

        print("Page title:", driver.title)

        # ✅ Scroll multiple times to load all buses
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # ✅ Extract bus details
        buses = driver.find_elements(By.XPATH, '//div[@class="clearfix bus-item-details"]')
        if not buses:
            print("No buses found!")
            return []

        for bus in buses[:MAX_RECORDS]:
            try:
                bus_name = bus.find_element(By.XPATH, ".//div[contains(@class,'travels')]").text
                bus_type = bus.find_element(By.XPATH, ".//div[contains(@class,'bus-type')]").text
                departing_time = bus.find_element(By.XPATH, ".//div[contains(@class,'dp-time')]").text
                duration = bus.find_element(By.XPATH, ".//div[contains(@class,'dur l-color lh-24')]").text
                reaching_time = bus.find_element(By.XPATH, ".//div[contains(@class,'bp-time')]").text
                star_rating = bus.find_element(By.XPATH, ".//div[contains(@class,'rating-sec')]").text
                price = bus.find_element(By.XPATH, ".//div[contains(@class,'fare d-block')]").text
                seat_availability = bus.find_element(By.XPATH, ".//div[contains(@class,'seat-left')]").text

                bus_data.append((bus_name, bus_type, departing_time, duration, reaching_time, star_rating, price, seat_availability))

            except Exception:
                continue

    except Exception as e:
        print(f"Error extracting bus details: {e}")

    return bus_data

# ✅ Store Data in Database
def store_data_in_db(bus_data):
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS wbtcinfo (
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
        INSERT INTO wbtcinfo (Bus_name, Bus_type, Departing_time, Duration, Reaching_time, Star_rating, Price, Seat_availability)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.executemany(insert_query, bus_data)

        conn.commit()
        cursor.close()
        conn.close()
        print(f"{len(bus_data)} bus records successfully stored in the database.")

    except pymysql.MySQLError as err:
        print(f"Database error: {err}")

# ✅ Interact with Webpage
def interact_with_webpage():
    try:
        print("Opening Google search...")
        driver.get("https://www.google.com")
        time.sleep(2)

        # ✅ Find search box and interact
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys("Selenium Python", Keys.RETURN)

        time.sleep(3)

    except Exception as e:
        print(f"Error interacting with webpage: {e}")

# ✅ Cleanup WebDriver Properly
def cleanup():
    global driver
    if driver:
        try:
            print("Closing WebDriver...")
            driver.quit()  # Quit WebDriver
            del driver  # Delete WebDriver object
            gc.collect()  # Force garbage collection
        except Exception as e:
            print(f"Error while closing WebDriver: {e}")
        finally:
            print("WebDriver closed successfully.")

# ✅ MAIN SCRIPT
if __name__ == "__main__":
    try:
        bus_data = extract_bus_details()
        if bus_data:
            store_data_in_db(bus_data)

        interact_with_webpage()

    finally:
        cleanup()  # Ensure WebDriver is closed properly
        os._exit(0)  # 🚀 Force clean exit (Prevents WinError 6)
