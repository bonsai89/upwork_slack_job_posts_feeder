import undetected_chromedriver as uc
import time
import pickle
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from slack_sdk import WebClient
import os
from slack_sdk.errors import SlackApiError

# Slack token and other configurations
slack_token = "slack token from slack channel for integration"
client = WebClient(token=slack_token)
file_name = './sent_entries.txt'

# Load sent entries from file
if os.path.exists(file_name):
    with open(file_name, 'r') as file:
        sent_entries = set(line.strip() for line in file)
else:
    sent_entries = set()

# Function to extract job type and budget from HTML soup
def extract_job_type_and_budget(soup):
    job_type = soup.find('strong', {'data-test': 'job-type'}).text.strip()
    budget_tag = soup.find('span', {'data-test': 'budget'})
    budget = budget_tag.text.strip() if budget_tag else 'Not specified'
    return job_type, budget

new_entries = []

# Load cookies from the saved file
with open("upwork_cookies.pkl", "rb") as file:
    cookies = pickle.load(file)

os.environ['DISPLAY'] = ':99'

# Setup Chrome options to run headless and with a separate profile
options = Options()
options.add_argument("user-data-dir=/home/username/chrome_profile")  # Profile location add your profile here
options.add_argument('--profile-directory=Profile 2') #add your profile name here
options.add_argument("--start-maximized")
options.headless = True  # Ensure the browser runs in headless mode
options.add_argument("--no-sandbox")  # Recommended for headless Chrome
options.add_argument("--disable-dev-shm-usage")  # Recommended for headless Chrome

# Initialize Chrome with options
driver = uc.Chrome(options=options)

# Function to log in to Upwork
def upwork_login(driver, username, password):
    try:
        driver.get("https://www.upwork.com/ab/account-security/login")
        time.sleep(5)
        driver.find_element(By.ID, "login_username").send_keys(username)
        driver.find_element(By.ID, "login_password_continue").click()
        time.sleep(5)
        driver.find_element(By.ID, "login_password").send_keys(password)
        driver.find_element(By.ID, "login_password").send_keys(Keys.RETURN)
        time.sleep(10)
        print("Login successful")
    except Exception as e:
        print(f"An error occurred during login: {e}")

# Function to handle login process
def login():
    try:
        driver.get("https://www.upwork.com")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.get("https://www.upwork.com/nx/find-work/")
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_containers = soup.find_all('section', {
            'class': 'air3-card-section air3-card-hover p-4 px-2x px-md-4x',
            'data-ev-opening_uid': True,
            'data-ev-position': True,
            'data-ev-feed_name': True,
            'data-ev-sublocation': True,
            'data-ev-label': True,
            'impression': True,
            'eh-i': True
        })
        if not job_containers:
            print("Login failed, trying to login again...")
            upwork_login(driver, 'email_address', 'password')
            time.sleep(10)
        return job_containers
    except Exception as e:
        print(f"Exception occurred during login: {str(e)}")
        time.sleep(10)
        login()

job_containers = login()

while True:
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            sent_entries = set(line.strip() for line in file)
    else:
        sent_entries = set()

    if not job_containers:
        job_containers = login()

    driver.get("https://www.upwork.com/nx/find-work/")
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    for job in job_containers:
        try:
            job_title = job.find('h3', class_='job-tile-title').get_text(strip=True)
            job_type, budget = extract_job_type_and_budget(job)
            job_url = "https://www.upwork.com" + job.find('h3', class_='job-tile-title').find('a')['href']
            entry = f"{job_title} - {job_url}"
            if entry not in sent_entries:
                print(entry)
                new_entries.append(entry)
                try:
                    message = f"*{job_title}*\n{job_type}: {budget}\n{job_url}" if 'Fixed' in job_type else f"*{job_title}*\n{job_type}\n{job_url}"
                    response = client.chat_postMessage(channel="slack_channel", text=message) #add your slack channel here
                    print(f"Message sent to Slack: {response['ts']}")
                except SlackApiError as e:
                    print(f"Error sending message to Slack: {e.response['error']}")
        except AttributeError:
            print("A job posting was skipped due to missing information.")
    if new_entries:
        with open(file_name, 'a') as file:
            for entry in new_entries:
                file.write(entry + '\n')
    else:
        print('No new jobs...')
    time.sleep(60)

driver.quit()
