from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time

# Set up Chrome options
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Uncomment to run in headless mode if desired

# Initialize the WebDriver with the correct path and options
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Go to the website
website = 'https://www.redbus.in/online-booking/hrtc/?utm_source=rtchometile'
driver.get(website)
driver.maximize_window()

# Initialize lists to store route titles and links
titles = []
links = []

# Set the number of pages you want to scrape (1 to 5)
pages_to_scrape = 4
current_page = 1

while current_page <= pages_to_scrape:
    try:
        # Wait for the main container to load (adjusted with WebDriverWait)
        container = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@class, "D117_main")]'))
        )

        # Extract all bus route products from the container
        products = container.find_elements(By.XPATH, './/div[contains(@class, "route_link")]')

        # Extract titles and links for each bus route
        for product in products:
            try:
                route_title = product.find_element(By.XPATH, './/a[contains(@class,"route")]').text
                route_link = product.find_element(By.XPATH,
                                                  ".//a[contains(@class,'route') and contains(@href, 'bus')]").get_attribute(
                    "href")
                titles.append(route_title)
                links.append(route_link)
            except Exception as e:
                print(f"Error extracting product info on page {current_page}: {e}")

        # Move to the next page (check for next page button and click)
        if current_page < pages_to_scrape:
            next_page = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[contains(@class,"DC_117_pageActive")]/following-sibling::div'))
            )

            # Ensure the element is in view and then click it using JavaScript
            driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
            time.sleep(1)  # Wait a bit to ensure it’s in view
            driver.execute_script("arguments[0].click();", next_page)

            time.sleep(3)  # Wait for the page to load before proceeding
        current_page += 1

    except Exception as e:
        print(f"Error scraping page {current_page}: {e}")
        break

# Save data to CSV if we have any routes
if titles and links:
    df_routes = pd.DataFrame({'bus_route': titles, 'bus_link': links})
    df_routes.to_csv('astc.csv', index=False)
    print("Data has been saved to 'astc.csv'.")
else:
    print("No data found.")


# Close the browser
driver.quit()



#website2='https://www.redbus.in/bus-tickets/tezpur-to-guwahati?fromCityId=90883&toCityId=74701&fromCityName=Tezpur&toCityName=Guwahati&busType=Any&onward=27-Nov-2024'