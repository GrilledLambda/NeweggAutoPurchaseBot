import time, platform, sys, subprocess, os, requests, selenium, random, lxml, asyncio
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from BotSettings import settings, xPaths
from lxml import html, etree


#Driver Initialize------------------------------------
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
linkFile = settings["LINKS"]
driver = webdriver.Chrome(options=chrome_options, executable_path=settings["DRIVER"])

action = ActionChains(driver)

waitFor = WebDriverWait(driver, 300) #Max time the driver will wait for you to sign in
waitCVV = WebDriverWait(driver, 20)

with open(linkFile) as linkReader:
    productLinks = [link.replace("\n", "") for link in linkReader]
    linkReader.close()

#----------------------Web bot Class------------------------------

class WebBot:

    def __init__(self):
        self.refreshing = False

    #Itterates through links and sends HTTP requests to see if each product link is available.
    #It will return True if a product is in stock. This will send Selenium to the product link that is in stock.
    async def checkLinks(self):
        
        headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0", "Accept-Encoding":"gzip, deflate", "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "DNT":"1","Connection":"close", "Upgrade-Insecure-Requests":"1"}
        for link in productLinks:
            try:
                response = requests.get(link, headers=headers, timeout=10)
                root = lxml.html.fromstring(response.content)
                button = root.xpath(xPaths["addToCart"])
                if len(button) > 0:
                    print("Item Found. IN STOCK")
                    return link
                else:
                    print("Not Available")
                    await asyncio.sleep(random.randint(settings["RTIME"], 3))
            except:
                pass
        return False

    #adds the found item to cart and will dismiss additional offerings.
    def addToCart(self, link):
        driver.get(link)
        driver.find_element_by_xpath(xPaths["addToCart"]).click()
        time.sleep(1)

        try:
            driver.find_element_by_xpath(xPaths["noThanks"]).click()
            time.sleep(.5)# takes in account for CSS animation
            driver.find_element_by_xpath(xPaths["checkout"]).click()
        except:
            pass

        self.checkForOffer()
        driver.find_element_by_xpath(xPaths["secureCheckout"]).click()
        try:
            self.buyItem()
        except:
            print(f"There was an issue trying to purchase an item.\n{link}")

    def checkForOffer(self):
        time.sleep(.5)
        try:
            driver.find_element_by_xpath(xPaths["notInterested"]).click()
        except:
            pass

    def buyItem(self):
        cvv = settings["CVV"]
        foundCVV = waitCVV.until(EC.url_contains("/shop/checkout"))
        cvvField = driver.find_element_by_xpath(xPaths["cVV"])
        cvvField.click()
        cvvField.send_keys(cvv)
        time.sleep(.1)
        action.key_up(cvvField)
        time.sleep(.1)
        driver.find_element_by_xpath(xPaths["place"]).click()
        time.sleep(10)


    #logs in and keeps session open by refreshing every 5 seconds.
    def startSession(self):

        if settings["SKIPSIGNIN"]:
            return True

        driver.find_element_by_xpath(xPaths["signIn"]).click()
        loggedIn = waitFor.until(EC.title_contains("Computer Parts, PC Components, Laptop Computers, LED LCD TV, Digital Cameras and more - Newegg.com"))

        if loggedIn:
            return True
        else:
            return False
    
    #keeps the session active by refreshing the page at random intervals
    async def refreshSession(self):
        print("Refresh was called.")
        self.refreshing = True
        await asyncio.sleep(random.randint(1,200))
        driver.refresh()
        print("refreshed")
        self.refreshing = False

    #calls all methods in correct order
    async def startBot(self):
        driver.get("https://www.newegg.com/")
        session = self.startSession()
        if session:
            while True: #while items not in stock
                
                #coroutines
                if self.refreshing == False: #if not currently refreshing
                    refreshTask = asyncio.create_task(self.refreshSession())
                    refresh = refreshTask #no return value there for no await

                linkTask = asyncio.create_task(self.checkLinks())
                
                link = await linkTask
                
                if link:
                    self.addToCart(link)
                    
        else:
            print("Unable to start session.")

eggBot = WebBot()
asyncio.run(eggBot.startBot())





