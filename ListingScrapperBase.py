from enum import Enum
from typing import Any, Protocol, Optional

import selenium
import urllib3
from alive_progress import alive_it
from bs4 import BeautifulSoup, ResultSet, Tag
from pandas import DataFrame

from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


class ListingScrapperBase(Protocol):
    """This is the base class upon which all scrapers will inherit from.

    :param webdriver: The webdriver to use.
    :param url: the base url of the webpage.
    :param timeout_limit: The maximum number of seconds to wait for when loading something on the page.
    :param limit_per_category: An optional parameter to limit the number of listings per category for testing purposes.
    :param processed: An optional parameter that defines the links of the listings you consider already processed and don't want to consider when getting endpoints.
    """
    url: str
    webdriver: WebDriver
    wait: WebDriverWait
    options: str
    current_page: int
    limit_per_category: Optional[int]
    processed_links: Optional[list[str]]

    class Endpoints(Enum):
        """Commonly used endpoints for categories in the website."""

        APARTMENTS_RENTAL = ""
        HOUSE_RENTAL = ""

        APARTMENTS_SALE = ""
        HOUSE_SALE = ""

    class XPaths(Enum):
        """Commonly used html xpaths to find specific elements in the page."""
        ...

    class SoupFinder:
        """This is a helper class to find the elements in the page used by the SoupExtractor class.

            It uses BeautifulSoup to find the wanted element.
        """

        @staticmethod
        def listings_div(soup: BeautifulSoup) -> ResultSet[Tag]:
            """The function to find listings divs on the gallery.

            :param soup: The soupified html of the page.
            :return: The results of the find_all.
            """
            ...

    class SoupExtractor:
        """The helper class to extract data from a listing"""

        @staticmethod
        def get_listing_data(page_source: str, url: str, rent_or_sale: Optional[str] = None) -> dict[str, Any]:
            """The final function that is called by the outer class to extract the data.

            :param page_source: The html string of the listing.
            :param url: The url of the listing page.
            :return: A dictionary of the extracted data.
            """
            ...

    def __init__(self, webdriver: WebDriver,
                 url: str,
                 timeout_limit: int = 20,
                 limit_per_category: Optional[int] = None,
                 processed: Optional[list[str]] = None) -> None:

        self.url = url
        self.webdriver = webdriver
        self.wait = WebDriverWait(webdriver, timeout_limit)
        self.current_page = 0
        self.options = ""
        self.reset_page()
        self.limit_per_category = limit_per_category
        self.processed_links = processed or []

    def get_data_from_listings_of_category(self, category: Endpoints) -> list[dict[str, Any]]:
        """Gathers the data of all the listings of a given category.

        :param category: The category to look into
        :returns: The list of the data collected
        """
        listings_data: list[dict[str, Any]] = []

        try:
            if (category is self.Endpoints.APARTMENTS_RENTAL
                    or category is self.Endpoints.HOUSE_RENTAL):
                rent_or_sale = 'rent'
            else:
                rent_or_sale = 'sale'

            if (category is self.Endpoints.APARTMENTS_RENTAL
                    or category is self.Endpoints.APARTMENTS_SALE):
                listing_type = 'appartments' # for backwards comp
            else:
                listing_type = 'houses'

            listings_endpoints: list[str] = self.get_all_listings(category)

            for endpoint in alive_it(listings_endpoints,
                                     title=f'Getting data from {category.name}',
                                     bar='solid',
                                     max_cols=300,
                                     spinner='classic',
                                     calibrate=10,
                                     force_tty=True):

                url: str = f"{self.url}{endpoint}"

                try:
                    self.webdriver.get(url)
                    self.wait.until(ec.url_to_be(url))
                except TimeoutException:
                    print("Couldn't load page!")
                    continue

                if not self.open_map():
                    continue

                listings_data.append(
                    {
                        "type": listing_type,
                        "rent_or_Sale": rent_or_sale,
                    } | self.SoupExtractor.get_listing_data(self.webdriver.page_source, url)
                )

            return listings_data

        except (KeyboardInterrupt, selenium.common.exceptions.WebDriverException, urllib3.exceptions.MaxRetryError):
            return listings_data

    def get_all_listings(self, category: Endpoints) -> list[str]:
        """Gets all listings from a given category.

        :param category: The endpoint to look into
        :return: The list of all listings endpoints contained in the category
        """

        print(f"Getting links for {category.name} ...")

        endpoints: list[str] = []

        while True:
            url: str = f"{self.url}{category.value}{self.options}"

            try:
                endpoints += self.get_listings_links_from_gallery(url)
            except (TimeoutException, TimeoutError):
                break

            if self.limit_per_category and len(endpoints) >= self.limit_per_category:
                break

            self.next_page()

        print(f"Got {len(endpoints)} listings from {self.current_page + 1} pages.")

        self.reset_page()

        return endpoints

    def get_listings_links_from_gallery(self, url: str) -> list[str]:
        """The method that extracts the links from a gallery page of listings fo a given url.

        :param url: The url of the gallery page.
        :return: The list of links found on the page.
        """

        soup = BeautifulSoup(self.webdriver.page_source, 'html.parser')

        listings_divs: ResultSet[Tag] = self.SoupFinder.listings_div(soup)

        endpoints: list[str] = []

        for div in listings_divs:
            listings_links: ResultSet[Tag] = div.find_all('a')

            for links in listings_links:
                if f"{self.url}{links['href'][4:]}" in self.processed_links:
                    continue
                endpoints.append(f"{links['href']}"[4:])  # we take out the `/en/`
                self.processed_links.append(f"{self.url}{links['href']}"[4:])

                if self.limit_per_category and len(endpoints) >= self.limit_per_category:
                    return endpoints

        return endpoints

    def set_page(self, page: int) -> None:
        """Sets page number of the listings' gallery.

        :param page: The page number.
        """
        self.current_page = page

    def next_page(self) -> None:
        """Adds one to the current page."""
        self.set_page(self.current_page + 1)

    def reset_page(self) -> None:
        """Resets the current page."""
        self.set_page(0)

    def open_map(self) -> bool:
        """A method to handle the location of the url from the yandex map."""
        ...

    def get_data_of_apartments_for_rent(self) -> list[dict[str, Any]]:
        return self.get_data_from_listings_of_category(self.Endpoints.APARTMENTS_RENTAL)

    def get_data_of_apartments_for_sale(self) -> list[dict[str, Any]]:
        return self.get_data_from_listings_of_category(self.Endpoints.APARTMENTS_SALE)

    def get_data_of_houses_for_rent(self) -> list[dict[str, Any]]:
        return self.get_data_from_listings_of_category(self.Endpoints.HOUSE_RENTAL)

    def get_data_of_houses_for_sale(self) -> list[dict[str, Any]]:
        return self.get_data_from_listings_of_category(self.Endpoints.HOUSE_SALE)

    def get_listings_data(self) -> list[dict[str, Any]]:
        return self.get_data_of_houses_for_sale() \
            + self.get_data_of_houses_for_rent() \
            + self.get_data_of_apartments_for_rent() \
            + self.get_data_of_apartments_for_sale()

    def to_data_frame(self) -> DataFrame:
        """Transforms the gathered data into a pandas :class:`DataFrame`.

        :returns: The :class:`DataFrame`
        """
        pre_data_frame: dict[str, list[Any]] = {
            'id': [],
            'price': [],
            'rooms': [],
            'square_meters': [],
            'address': [],
            'date': [],
            'source': [],
            'furniture': [],
            'renovation': [],
            'price_per_meter': [],
            'floor': [],
            'building_floors': [],
            'height': [],
            'bathroom': [],
            'rent_or_sale': [],
            'links': [],
            'SHAPE': [],

            # 'Currency': [],
            'type': []
        }

        infos: list[dict[str, Any]] = self.get_listings_data()

        for info in infos:
            if pre_data_frame.keys() != info.keys():
                print(list(pre_data_frame.keys()), list(info.keys()))
                raise KeyError("data improperly parsed !")

            for k, v in info.items():
                pre_data_frame[k].append(v)

        return DataFrame(pre_data_frame)

    def save_data_to_tsv(self, path: str) -> None:
        self.to_data_frame().to_csv(path, sep='\t', index=False)
