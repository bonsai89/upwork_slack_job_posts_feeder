import undetected_chromedriver as uc
import time
import pickle
import os

# Setup Chrome with undetected-chromedriver using a specific user data directory
options = uc.ChromeOptions()
options.add_argument("user-data-dir=~/.config/google-chrome/") #use your google chrome config here
options.add_argument('--profile-directory=Profile 2') #use your profile name here

# Initialize Chrome with options
driver = uc.Chrome(options=options)

# Login to Upwork
driver.get("https://www.upwork.com/ab/account-security/login")
time.sleep(5)

print("Please log in manually within the browser window...")

# Wait for the user to log in manually
time.sleep(120)

# After logging in, save the cookies
cookies = driver.get_cookies()
with open("upwork_cookies.pkl", "wb") as file:
    pickle.dump(cookies, file)

print("Session cookies saved successfully!")

# Save the Chrome profile for future use
print("Profile saved successfully!")

# Close the browser
driver.quit()

