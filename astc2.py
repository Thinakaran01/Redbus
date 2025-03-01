from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment to run in headless mode if desired

# Initialize the WebDriver with the correct path and options
service = Service(ChromeDriverManager().install())

driver2 = webdriver.Chrome(service=service, options=chrome_options)
website2 = 'https://www.redbus.in/bus-tickets/tezpur-to-guwahati?fromCityId=90883&toCityId=74701&fromCityName=Tezpur&toCityName=Guwahati&busType=Any&onward=27-Nov-2024'
driver2.get(website2)
driver2.maximize_window()

# Initialize lists to store bus details
bus_name = []
bus_type = []
departing_time = []
duration = []
reaching_time = []
star_rating = []
price = []
seat_availability = []


# Function to extract bus details from the current page
def extract_bus_details():
    # Wait for the bus items container to load
    container2 = WebDriverWait(driver2, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'bus-items'))
    )

    # Extract bus details from the current page
    products2 = container2.find_elements(By.XPATH, './/div[@class="clearfix bus-item-details"]')

    for product2 in products2:
        try:
            # Extract each bus's details using relative XPath
            bus = product2.find_element(By.XPATH, ".//div[contains(@class,'travels')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'travels')]") else ''
            bus_type_val = product2.find_element(By.XPATH,
                                                 ".//div[contains(@class,'bus-type')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'bus-type')]") else ''
            depart_time = product2.find_element(By.XPATH,
                                                ".//div[contains(@class,'dp-time')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'dp-time')]") else ''
            duration_val = product2.find_element(By.XPATH,
                                                 ".//div[contains(@class,'dur l-color lh-24')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'dur l-color lh-24')]") else ''
            reach_time = product2.find_element(By.XPATH,
                                               ".//div[contains(@class,'bp-time')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'bp-time')]") else ''
            star_rate = product2.find_element(By.XPATH,
                                              ".//div[contains(@class,'rating-sec')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'rating-sec')]") else ''
            price_val = product2.find_element(By.XPATH,
                                              ".//div[contains(@class,'fare d-block')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'fare d-block')]") else ''
            seat_left = product2.find_element(By.XPATH,
                                              ".//div[contains(@class,'seat-left')]").text if product2.find_element(
                By.XPATH, ".//div[contains(@class,'seat-left')]") else ''

            # Only append non-empty rows
            if bus and bus_type_val and depart_time and duration_val and reach_time and star_rate and price_val and seat_left:
                bus_name.append(bus)
                bus_type.append(bus_type_val)
                departing_time.append(depart_time)
                duration.append(duration_val)
                reaching_time.append(reach_time)
                star_rating.append(star_rate)
                price.append(price_val)
                seat_availability.append(seat_left)
        except Exception as e:
            print(f"Error extracting bus info: {e}")


# Initial extraction from the first loaded page
extract_bus_details()

# Scroll the page until all buses are loaded, with faster scrolling
last_height = driver2.execute_script("return document.body.scrollHeight")
time.sleep(3)
def wait_for_new_buses():
    WebDriverWait(driver2, 10).until(
        EC.presence_of_all_elements_located((By.XPATH, './/div[@class="clearfix bus-item-details"]'))
    )

while True:
    # Scroll down to the bottom of the page (faster scroll)
    driver2.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait for the new buses to load after the scroll (shortened wait time)
     # Reduced the wait time to 1 second to speed up the process
    wait_for_new_buses()
    # Extract the newly loaded bus details
    extract_bus_details()

    # Get the new height of the page
    new_height = driver2.execute_script("return document.body.scrollHeight")

    # Break the loop if we have scrolled to the bottom of the page (no more new data)
    if new_height == last_height:
        break

    # Update the last height for the next iteration
    last_height = new_height

# Create a pandas DataFrame with the extracted data
if bus_name:
    df_routes1 = pd.DataFrame({
        'Bus_name': bus_name,
        'Bus_type': bus_type,
        'Departing_time': departing_time,
        'Duration': duration,
        'Reaching_time': reaching_time,
        'Star_rating': star_rating,
        'Price': price,
        'Seat_availability': seat_availability
    })

    # Remove duplicates based on bus_name and other columns to avoid repetitions
    df_routes1 = df_routes1.drop_duplicates()

    # Perform data cleaning (if necessary)
    # Example: Strip extra spaces from all columns
    # Strip spaces only from specific string columns
    df_routes1['Bus_name'] = df_routes1['Bus_name'].apply(lambda x: x.strip() if isinstance(x, str) else x)
    df_routes1['Bus_type'] = df_routes1['Bus_type'].apply(lambda x: x.strip() if isinstance(x, str) else x)
    # Repeat for other string columns as necessary

    # Drop rows with any empty (NaN or '') values
    df_routes1 = df_routes1.replace('', pd.NA).dropna(how='any')

    # Save the data to a CSV file
    df_routes1.to_csv('astcinfo.csv', index=False)
    print("Bus data has been saved to 'astcinfo.csv'.")
else:
    print("No bus information found.")

# Close the browser
driver2.quit()
