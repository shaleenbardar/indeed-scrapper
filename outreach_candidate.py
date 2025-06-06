import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
import pickle
import requests

# Configure Chrome (headless mode)
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-webgl")
chrome_options.add_argument("--disable-webrtc")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
)
chrome_options.add_argument("--disable-features=VizDisplayCompositor")

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",  # Updated locale
#     "Referer": "https://resumes.indeed.com/"
# }

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://resumes.indeed.com/"
}

driver = uc.Chrome(options=chrome_options)
driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})

# Path to store the cookies
cookie_file = "cookies.pkl"

def save_cookies():
    """ Save cookies to a file after manual login. """
    driver.get("https://resumes.indeed.com")  # Navigate to login page

    # Wait for manual login (you can adjust this time as needed)
    print("Please log in manually within 30 seconds...")
    time.sleep(90)  # Allow time for manual login

    # Save cookies to a file
    with open(cookie_file, "wb") as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies saved successfully!")

def load_cookies():
    """ Load saved cookies and access a protected page. """
    driver.get("https://resumes.indeed.com/")  # Open Indeed homepage

    # Load cookies from file
    with open(cookie_file, "rb") as file:
        cookies = pickle.load(file)
        for cookie in cookies:
            driver.add_cookie(cookie)
    print("Cookies loaded successfully!")

def send_message_to_candidates(candidate_data, message):
    """
    Sends a message to each candidate using their Indeed profile URL
    """
    load_cookies()
    try:
        driver.get('https://resumes.indeed.com/resume/7c35745bdd8f040a')

        # Wait for the "Get started" button and click it
        get_started_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//button[@class="css-l02nho e8ju0x50"]/span[text()="Get started"]'))
        )
        if get_started_button.is_displayed():
            get_started_button.click()
            time.sleep(2)

        # Wait for the message box to load
        message_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, '//textarea[contains(@data-cauto-id, "gpt_rich_text_editor")]'))
        )

        # Wait for the dropdown button to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'select-change-job-context-button'))
        )

        # Check if dropdown is empty
        job_button = driver.find_element(By.ID, "select-change-job-context-button")
        job_text = job_button.find_element(By.XPATH, './/span').text

        if "Select jobs on Indeed" in job_text:
            job_button.click()  # Open only if not pre-filled
            time.sleep(2)

            # Wait for the dropdown options to load
            # WebDriverWait(driver, 10).until(
            #     EC.presence_of_element_located((By.XPATH, '//div[@role="radio"]'))
            # )

            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[@class="css-1neskph e37uo190"]'))
            )

            # Find the job element by its text content
            # job_element = driver.find_element(By.XPATH, '//div[@role="radio"]//span[contains(text(), "Business Analyst")]')
            # job_element.click()  # Select the job
            # time.sleep(2)

            job_element = driver.find_element(By.XPATH, '//div[@class="css-1neskph e37uo190"]')
            job_element.click()  # Select the job
            time.sleep(2)

            # Find and click the "Done" button
            done_button = driver.find_element(By.XPATH, '//button[@class="css-kjgd5i e8ju0x50"]/span[text()="Done"]')
            done_button.click()
            time.sleep(2)

        # Wait for the message box to be interactable
        WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, '//textarea[contains(@data-cauto-id, "gpt_rich_text_editor")]'))
        )

        # Clear the message box (if needed)
        message_box.clear()

        # Enter the message using JavaScript (if send_keys doesn't work)
        driver.execute_script("arguments[0].value = arguments[1];", message_box, message)

        # Alternatively, use send_keys (if JavaScript is not required)
        # message_box.send_keys(message)

        # Find the send button and click it
        send_button = driver.find_element(By.XPATH, '//button[@data-cauto-id="cf_submit_button"]')
        send_button.click()
        time.sleep(2)  # Wait for 2 seconds before sending the next message
    except Exception as e:
        print(f"Error sending message: {e}")

def main():
    # Load candidate data from CSV
    candidate_data = pd.read_csv("data_analysis.csv").to_dict(orient='records')

    save_cookies()

    # Define the message to send
    message = "Hello, I came across your profile and I am interested in discussing a potential opportunity with you. Please let me know if you are available for a chat. Thank you!"

    # Send messages to candidates
    send_message_to_candidates(candidate_data, message)

    driver.quit()

if __name__ == "__main__":
    main()