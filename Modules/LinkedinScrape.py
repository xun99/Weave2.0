import pandas as pd
import time
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time
import datetime

class scrapeLinkedin:
    """
    scrapes the Name, Education (Academic Institution, Degree),
    Experience (Job Title, Institution), and Connection Number from
    a Linkedin Profile. Requires log in to a Linkedin Account.
    Amount of profiles visited limited by Linkedin.
    Chrome driver should be installed in the path.
    """
    def __init__(self, driver, username, password):
        self.driver = webdriver.Chrome('./chromedriver')
        self.username
        self.password

    def access(self):
        """
        Logs into the Linkedin Account
        """
        self.driver.get('https://www.linkedin.com/login')
        self.driver.set_page_load_timeout(20)

        self.driver.get('https://www.linkedin.com/login')
        time.sleep(5)


        title = self.driver.title
        if 'Login' in title:
            print('Login page found')
        if 'Feed' in title:
            print('Feed page found')
        if 'Verification' in title:
            print('Verification page found')

        self.driver.current_url
        self.driver.find_element("id", "username").send_keys(self.username)
        self.driver.find_element("id", "password").send_keys(self.password)
        self.driver.find_element("xpath","//button[@type='submit']").click()
        print('complete')

        return self.driver

    def scrape(self, url, driver):
        """
        Loads the profile page, scrolls to the bottom to load all information
        scrapes relevant data from the html
        input =
        driver: returned by the access function
        url: link to profile
        returns array of name, education, experience, connection information.
        """
        try: 
            driver.get(url)
            start = time.time() 
            # will be used in the while loop
            initialScroll = 0
            finalScroll = 1000

            while True:
                driver.execute_script("window.scrollTo({}, {})".format(initialScroll, finalScroll))
                # this command scrolls the window starting from
                # the pixel value stored in the initialScroll
                # variable to the pixel value stored at the
                # finalScroll variable
                initialScroll = finalScroll
                finalScroll += 1000

                # we will stop the script for 3 seconds so that
                # the data can load
                time.sleep(3)
                # You can change it as per your needs and internet speed

                end = time.time()

                # We will scroll for 20 seconds.
                # You can change it as per your needs and internet speed
                if round(end - start) > 20:
                    break
            src = driver.page_source
            soup = bs(src, 'html.parser')
            temp = [url]
            name = soup.find('div', {"class": "pv-text-details__left-panel"}).find('h1',{"class": "text-heading-xlarge inline t-24 v-align-middle break-words"} ).get_text()
            temp.append(name)
            try:
                education = soup.find('div',{'id':'education'}).parent
                school = []
                degree = []
                for li in education.find('ul').find_all('li',recursive=False):
                    school.append(li.find('span',{'class':'mr1 hoverable-link-text t-bold'}).find('span',{'aria-hidden':'true'}).get_text().strip().replace(',',''))
                    try:
                        degree.append(li.find('span',{'class':'t-14 t-normal'}).find('span',{'aria-hidden':'true'}).get_text().strip().replace(',',''))
                    except:
                        degree.append("Not Available")
                temp.append(','.join(school))
                temp.append(','.join(degree))
            except:
                temp.append("Not Available")
                temp.append("Not Available")
            roles = []
            companies = []
            try:
                experience = soup.find('div',{'id':'experience'}).parent
                for li in experience.find('ul').find_all('li',recursive=False):
                    try:
                        companies.append(li.find('span',{'class':'mr1 t-bold'}).find('span',{'aria-hidden':'true'}).get_text().strip().replace(',',''))
                        subtitle = li.find('span',{'class':'t-14 t-normal'}).find('span',{'aria-hidden':'true'}).get_text().strip().split(' · ')
                        roles.append(subtitle[0])
                    except:
                        companies.append(li.find('span',{'class':'mr1 hoverable-link-text t-bold'}).find('span',{'aria-hidden':'true'}).get_text().strip().replace(',',''))
                        for li2 in li.find('ul',{'class':'pvs-list'}).find_all('li',recursive=False):
                            position = li2.find('span',{'class':'mr1 hoverable-link-text t-bold'}).find('span',{'aria-hidden':'true'}).get_text().strip().replace(',','')
                            roles.append(position)
                temp.append(','.join(roles))
                temp.append(','.join(companies))
            except:
                temp.append("Not Available")
                temp.append("Not Available")
            try:
                temp.append(soup.find("span", {"class" : "t-bold"}).get_text().replace(',',''))
            except:
                temp.append("Not Available")
        except:
            temp = ['Not Available']*7
        return temp
