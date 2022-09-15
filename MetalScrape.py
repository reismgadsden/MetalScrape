"""
metal-archive.com scraper.

This program will scrape a given number of bands, starting with a certain letter,
for their information. This information includes:
    1. URL
    2. Country of origin
    3. Location
    4. Status
    5. Year formed
    6. Years active
    7. Genre
    8. Lyrical themes
    9. Current/Last label
    10. Discography
        a. Project name
        b. Type of project
        c. Year released

author: Reis Gadsden 2022-08-30
class: CS-5245 @ Appalachian State University
"""
# needed imports
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

"""
Class that handles the scrapping and compilation of data.
"""
class MetalScrape:
    # the base link of the site
    _base = "https://www.metal-archives.com/"

    # the url of alphabetical list we pull from
    _list_base = ""

    # value to hold the selenium driver
    _driver = ""

    # value that holds our main window
    _main_window = ""

    # value that holds all our band data
    _bands = dict()

    # value that holds the number of bands to gather
    _num_bands = 0

    """
    Initialization method.
    This method will set our class variables as well as make calls to other methods.
    
    param:
        letter - What letter the bands we pull will begin with
        num_bands - the number of bands to call
    """
    def __init__(self, letter, num_bands):
        # set our url and num_bands values
        self._list_base = self._base + "lists/" + letter.upper()
        self._num_bands = num_bands

        # set our firefox profile and open the root page
        profile = webdriver.FirefoxProfile()
        profile.set_preference("dom.disable_open_during_load", False)
        self._driver =webdriver.Firefox(firefox_profile=profile)

        # access the list page
        self._driver.get(self._list_base)

        # get main window object
        self._main_window = self._driver.current_window_handle

        # gathers the urls for the specifed amount of bands
        self.get_bands()

        # save our data to a json file
        self.save_to_json(letter)

        # close the web driver
        self._driver.close()

    """
    This method gets the urls for the number of bands specified by the _num_bands value.
    """
    def get_bands(self):
        # list to hold urls
        urls = []

        # loop over the page until we have collected the specified number of urls
        while len(urls) < self._num_bands:

            # wait until the elements that hold the urls load
            WebDriverWait(self._driver, 30).until(
                ec.presence_of_all_elements_located((By.CSS_SELECTOR, "td.sorting_1 a"))
            )

            # find the number of links on the page and loop over using range to access each
            # element individually. THIS WAS USED TO REMEDY STALEELEMENT ERRORS.
            band_links = len(self._driver.find_elements(By.CSS_SELECTOR, "td.sorting_1 a"))
            for i in range(band_links):
                element = self._driver.find_elements(By.CSS_SELECTOR, "td.sorting_1 a")[i]

                # scroll into view to make sure element is loaded
                self._driver.execute_script("arguments[0].scrollIntoView(true);", element)

                # append href to urls list
                urls.append(element.get_attribute("href"))

                # check if we have enough urls
                if len(urls) > self._num_bands:
                    break

                # sleep to allow elements to update
                # helps avoid staleelement errors
                time.sleep(0.5)

            # if we are on the last page we stop trying to collect urls
            if len(self._driver.find_elements(By.CSS_SELECTOR, "a#bandListAlpha_next.next.paginate_button.paginate_button_disabled")) != 0:
                break

            # click the next button
            next_button = list(self._driver.find_elements(By.CSS_SELECTOR, "a.next.paginate_button"))[-1]

            # scroll next button into view and click it
            self._driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
            next_button.click()

        # loop over the urls and pass them to the get_band function
        for url in urls:
            self.get_band(url)

    """
    This method gets the information for each band by going to its band page and
    scraping the information from there.
    
    params:
        url - page to scrape
    """
    def get_band(self, url):

        # create a new dictionary that will hold the information
        band_info = dict()

        # take the driver to the new page
        self._driver.get(url)

        # wait until discography table (this element takes the longest to load)
        WebDriverWait(self._driver, 30).until(
            ec.presence_of_all_elements_located((By.CSS_SELECTOR, "table.display.discog"))
        )

        # get the name of the band and it to our dictionary
        band_name = self._driver.find_element(By.CSS_SELECTOR, "h1.band_name").get_attribute("innerText")
        band_info["Band name"] = band_name

        # get the information that is held in the dl.float_left dd css paths
        # this path is consistent on all pages and contains the following info:
        # Country of origin, Location, Status, and [Year] Formed In
        info_left = self._driver.find_elements(By.CSS_SELECTOR, "dl.float_left dd")
        band_info["Country of origin"] = info_left[0].get_attribute("innerText")
        band_info["Location"] = info_left[1].get_attribute("innerText")
        band_info["Status"] = info_left[2].get_attribute("innerText")
        band_info["Formed in"] = info_left[3].get_attribute("innerText")

        # get the years active information
        years_active = self._driver.find_element(By.CSS_SELECTOR, "dl.clear dd")
        band_info["Years active"] = years_active.get_attribute("innerText")

        # get the information stored in the dl.float_right dd css paths
        # this path is consistent on all pages and contains the following information:
        # Genre, Lyrical themes, Current/Last label
        info_right = self._driver.find_elements(By.CSS_SELECTOR, "dl.float_right dd")
        band_info["Genre"] = info_right[0].get_attribute("innerText")
        band_info["Lyrical themes"] = info_right[1].get_attribute("innerText")
        band_info["Current/Last label"] = info_right[2].get_attribute("innerText")

        # list to hold all discography projects
        disco = []

        # all the discography information is contained in table rows so we loop over all the table rows
        discog_table = self._driver.find_elements(By.CSS_SELECTOR, "table.display.discog tbody tr")
        for entry in discog_table:

            # dictionary to hold information on each release
            release_dict = dict()

            # grab each td in the row
            data = entry.find_elements(By.TAG_NAME, "td")

            # whenever there is no projects in the discography there is a placeholder tr and td
            # if there is less then  three tds in the first row it means the discography is empty
            if len(data) <= 2:
                break

            # we can access the tds directly as there will always be four tds in a row
            # as long as there is a project in their discography
            release_dict["Name"] = data[0].get_attribute("innerText")
            release_dict["Type"] = data[1].get_attribute("innerText")
            release_dict["Year"] = data[2].get_attribute("innerText")

            # append the project info to the array
            disco.append(release_dict)

        # add the discography list to our dictionary
        band_info["Discography"] = disco

        # add all the bands info to the class dictionary
        # decided to key on the url as keying by name can run into collisions as bands
        # sometimes have the same name, but each url is unique
        self._bands[url] = band_info

    """
    This method will dump our class dictionary into a formatted json file.
    
    params:
        letter - the letter that was chosen, we add this to the file name for clarity
    """
    def save_to_json(self, letter):
        with open("./metal-scrape-reis-gadsden_by_"+ letter +".json", "w+") as outfile:
            json.dump(self._bands, outfile, indent=2)


"""
main method to kick it all off.
"""
if __name__ == "__main__":

    # the letter that all band names will begin with
    LETTER = "R"

    # the maximum number of bands to collect
    # if this number is bigger then the total number of bands, only the total will be collected
    NUM_BANDS = 2000

    # initialize our MetalSrape
    metal = MetalScrape(LETTER, NUM_BANDS)
