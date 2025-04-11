import undetected_chromedriver as uc
import time
import pickle
import urllib.parse

from selenium.common import ElementClickInterceptedException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from slack_sdk import WebClient
import os

from slack_sdk.errors import SlackApiError

# Your Slack API token
slack_token = "slack API token"

# Initialize the Slack API client
client = WebClient(token=slack_token)

# Define the file to store sent entries
file_name = '/home/username/PycharmProjects/slack_rss/sent_entries.txt'

# Load sent entries from file
if os.path.exists(file_name):
    with open(file_name, 'r') as file:
        sent_entries = set(line.strip() for line in file)
else:
    sent_entries = set()


def extract_job_type_and_budget(soup):
    # Extract job type
    job_type = soup.find('div', class_='d-flex text-body-sm').get_text(strip=True)


    return job_type


new_entries = []

# # # Load cookies from the saved file
# with open("upwork_cookies.pkl", "rb") as file:
#     cookies = pickle.load(file)

#os.environ['DISPLAY'] = ':99'

# Set up Chrome options with the specified user data directory
options = Options()
options.add_argument("user-data-dir=/home/username/.config/google_chrome")
options.add_argument('--profile-directory=Profile 2')
options.headless = False
options.add_argument("--start-maximized")

# Initialize Chrome with options
driver = uc.Chrome(driver_executable_path=ChromeDriverManager().install())
driver = uc.Chrome(options=options)


def upwork_login(driver, username, password):
    """
    Function to log in to Upwork using Selenium and the provided WebDriver.

    :param driver: The Selenium WebDriver object.
    :param username: The Upwork username (email).
    :param password: The Upwork password.
    """
    try:
	#driver.get("http://www.google.com")
	#cookies = pickle.load(open("upwork_cookies.pkl", "rb"))
	#for cookie in cookies:
    	#	driver.add_cookie(cookie)
        # Open Upwork login page
        driver.get("https://www.upwork.com/ab/account-security/login")

        # Wait for the page to load
        time.sleep(5)

        # Find the username input field and enter your username/email
        username_field = driver.find_element(By.ID, "login_username")
        username_field.send_keys(username)

        # Click on "Continue" to proceed to password entry
        continue_button = driver.find_element(By.ID, "login_password_continue")
        continue_button.click()

        # Wait for the password field to become visible
        time.sleep(5)

        # Find the password input field and enter your password
        password_field = driver.find_element(By.ID, "login_password")
        password_field.send_keys(password)

        # Submit the form (simulate pressing the Enter key)
        password_field.send_keys(Keys.RETURN)

        # Wait for the login process to complete (you can add specific checks here)
        time.sleep(10)

        print("Login successful")

    except Exception as e:
        print(f"An error occurred during login: {e}")


def login():
    """Attempt to log in to Upwork using cookies and handle failures."""
    try:
        # Open Upwork and add cookies
        driver.get("https://www.upwork.com")
        driver.save_screenshot('/home/username/Downloads/slack_rss/debug.png')

        # # Add cookies to the browser session
        # for cookie in cookies:
        #     if 'domain' not in cookie:
        #         cookie['domain'] = '.upwork.com'  # Set domain if not present
        #     driver.add_cookie(cookie)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Check if login is successful by refreshing the page
        driver.get("https://www.upwork.com/nx/find-work/")
        driver.refresh()
        time.sleep(5)

        # Verify login success by checking if job containers are present
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Find the toggle button using BeautifulSoup
        list_view_toggle_bs = soup.find("label", {"id": "listViewToggle"})

        if list_view_toggle_bs:
            try:
                # Locate the element in Selenium
                list_view_toggle = driver.find_element(By.ID, "listViewToggle")

                # Scroll to the element (if necessary)
                driver.execute_script("arguments[0].scrollIntoView();", list_view_toggle)

                # Click the button using Selenium
                list_view_toggle.click()
                print("Successfully toggled list view!")

            except Exception as e:
                print("Error interacting with the toggle button:", e)
        else:
            print("Toggle button not found in BeautifulSoup parsing!")

        driver.get("https://www.upwork.com/nx/find-work/")
        driver.refresh()
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_containers = soup.find_all('div', class_='air3-card-section')

        if not job_containers:
            print("Login failed, trying to login again...")
            # If login fails, attempt manual login again (you can add manual login logic here if needed)
            upwork_login(driver, 'email_address', 'password')
            time.sleep(10)  # Give time for user to log in manually
        return job_containers

    except (ElementClickInterceptedException, NoSuchElementException) as e:
        print(f"Exception occurred during login: {str(e)}")
        print("Retrying login after pause 10secs...")
        time.sleep(10)
        login()  # Retry login in case of failure


# Call login function before starting the loop
job_containers = login()

while True:
    # Recheck the sent entries file each time
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            sent_entries = set(line.strip() for line in file)
    else:
        sent_entries = set()

    # If job containers are empty, retry login
    if not job_containers:
        job_containers = login()

    driver.get("https://www.upwork.com/nx/find-work/")
    # Scroll the page to load more job posts
    scroll_pause_time = 2  # Pause time between scrolls (adjust if necessary)
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait to load the page
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Scroll back to the top of the page in three steps
    for i in range(3):
        # Calculate the position to scroll up in steps
        scroll_position = last_height * (2 - i) / 3  # Divide the height into 3 parts
        driver.execute_script(f"window.scrollTo(0, {scroll_position});")
        time.sleep(scroll_pause_time)

    # Ensure we're fully at the top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(5)

    driver.save_screenshot('/home/username/Downloads/slack_rss/debug2.png')

    # Scrape job posts as needed
    soup = BeautifulSoup(driver.page_source, "html.parser")
    job_containers = soup.find_all('div', class_='air3-card-section')

    if not job_containers:
        print("Login failed, trying to login again...")
        # If login fails, attempt manual login again (you can add manual login logic here if needed)
        upwork_login(driver, 'email_address', 'password')
        time.sleep(10)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        job_containers = soup.find_all('div', class_='air3-card-section')
    filtered_jobs = [
        job for job in job_containers if job.has_attr('data-ev-opening_uid')
    ]
        # Iterate through each job container to extract details
    for job in filtered_jobs:
        try:
            # Extract the job title
            job_title = job.find('span', class_='job-tile-title').get_text(strip=True)
            job_title_url = job_title.replace(" ", "-") + "_~02"
            url = job.get('data-ev-opening_uid')
            job_type = extract_job_type_and_budget(job)
            job_url = f"https://www.upwork.com/jobs/{job_title_url}{url}"
            entry = f"{job_title} - {job_url}"

            if entry not in sent_entries:
                print(entry)
                new_entries.append(entry)
                encoded_url = urllib.parse.quote(job_url, safe=':/')
                try:
                    # Post the message to Slack
                    message = f"*{job_title}*\n{job_type}: <{encoded_url}>" if 'Fixed' in job_type else f"*{job_title}*\n{job_type}\n<{encoded_url}>"
                    response = client.chat_postMessage(channel="channel_id", text=message) #add your slack channel id here
                    print(f"Message sent to Slack: {response['ts']}")

                except SlackApiError as e:
                    print(f"Error sending message to Slack: {e.response['error']}")

        except AttributeError:
            print("A job posting was skipped due to missing information.")
            print("-" * 40)

    # Save the new entries to the file
    if new_entries:
        with open(file_name, 'a') as file:
            for entry in new_entries:
                file.write(entry + '\n')
    else:
        print('No new jobs...')

    print('Sleeping...')
    time.sleep(180)

# Close the browser
driver.quit()
