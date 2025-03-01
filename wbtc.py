import os 
import gc
import subprocess
import time
import atexit
import pymysql
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set environment variables
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_LITE_DISABLE_XNNPACK"] = "1"

gc.collect()

def kill_chromedriver():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Terminated existing ChromeDriver & Chrome processes.")
    except subprocess.CalledProcessError:
        print("No existing ChromeDriver/Chrome processes found.")

kill_chromedriver()

chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

try:
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
except Exception as e:
    print(f"Error initializing WebDriver: {e}")
    exit(1)

def close_driver():
    global driver
    if 'driver' in globals():
        driver.quit()
        print("WebDriver closed.")
        del driver
        gc.collect()

atexit.register(close_driver)

def scrape_bus_routes():
    website = 'https://www.redbus.in/online-booking/wbtc-ctc/?utm_source=rtchometile'
    driver.get(website)
    driver.maximize_window()
    WebDriverWait(driver, 30).until(lambda driver: driver.execute_script("return document.readyState") == "complete")
    time.sleep(10)

    titles, links = [], []
    pages_to_scrape = 2  
    current_page = 1

    while current_page <= pages_to_scrape:
        try:
            container = WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "D117_main")]'))
            )
            print("Main container found!")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)
        except Exception as e:
            print(f"Error finding main container on page {current_page}: {e}")
            driver.quit()
            exit(1)

        products = container.find_elements(By.XPATH, './/div[contains(@class, "route_link")]')
        for product in products:
            try:
                route_title = product.find_element(By.XPATH, './/a[contains(@class,"route")]').text
                route_link = product.find_element(By.XPATH, ".//a[contains(@class,'route') and contains(@href, 'bus')]").get_attribute("href")
                titles.append(route_title)
                links.append(route_link)
            except Exception as e:
                print(f"Error extracting bus info on page {current_page}: {e}")
        
        del products  
        del container  

        if current_page < pages_to_scrape:
            try:
                next_page = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[contains(@class,"DC_117_pageActive")]/following-sibling::div'))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
                time.sleep(1)
                next_page.click()
                time.sleep(3)
            except Exception as e:
                print(f"Error navigating to next page: {e}")

        current_page += 1

    if titles and links:
        df_routes = pd.DataFrame({'bus_route': titles, 'bus_link': links})
        df_routes.to_csv('wbtc.csv', index=False)
        print("Data has been saved to 'wbtc.csv'.")
    else:
        print("No data found.")
    
    return 'wbtc.csv'

def insert_data_to_mysql(csv_file):
    try:
        df = pd.read_csv(csv_file)
        conn = pymysql.connect(host="localhost", user="root", password="Thilakkumar123", port=3306)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS redbus;")
        conn.commit()
        conn.select_db("redbus")
        print("Connected to MySQL successfully.")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wbtc (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bus_route VARCHAR(255),
            bus_link TEXT
        )
        """)
        insert_query = "INSERT INTO wbtc (bus_route, bus_link) VALUES (%s, %s)"
        cursor.executemany(insert_query, df.itertuples(index=False, name=None))
        conn.commit()
        print("Data successfully inserted into the 'wbtc' table.")
    except pymysql.MySQLError as e:
        print(f"MySQL Error: {e}")
    except Exception as e:
        print(f"Unexpected Error: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            cursor.close()
            conn.close()
            print("MySQL connection closed.")

csv_file = scrape_bus_routes()
insert_data_to_mysql(csv_file)
driver.quit()
gc.collect()
print("Script execution completed.")
