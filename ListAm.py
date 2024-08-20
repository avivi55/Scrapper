from utils import extract_first_numbers, extract_numbers
from ListingScrapperBase import ListingScrapperBase

from datetime import datetime

from enum import Enum
from typing import Any, Iterable, Final, Optional, override

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup, NavigableString, ResultSet, Tag
from urllib import parse

import currency_coverter

LIST_AM_LINK: Final[str] = r"https://www.list.am/en/"


class ListAm(ListingScrapperBase):
    """The scrapper designed for list.am"""

    @override
    class Endpoints(Enum):

        APARTMENTS_RENTAL = "category/56"
        HOUSE_RENTAL = "category/63"

        APARTMENTS_SALE = "category/60"
        HOUSE_SALE = "category/62"

    @override
    class XPaths(Enum):

        YANDEX_MAP = r'//*[@id="abar"]/div[1]/a'
        YANDEX_LOGO = r'//*[@id="map"]/ymaps/ymaps/ymaps/ymaps[3]/ymaps/ymaps/ymaps[2]/ymaps/ymaps[2]/a'

    @override
    class SoupFinder:

        @staticmethod
        def address(soup: BeautifulSoup) -> Tag | NavigableString | None:
            return soup.find('a', href='#', onclick=True)

        @staticmethod
        def price(soup: BeautifulSoup) -> Tag | NavigableString | None:
            return soup.find('span', class_='price x')

        @staticmethod
        def currency(soup: BeautifulSoup) -> Tag | NavigableString | None:
            return soup.find('meta', itemprop='priceCurrency')

        @staticmethod
        def coordinates(soup: BeautifulSoup) -> Tag | NavigableString | None:
            return soup.find('a', class_='ymaps-2-1-79-copyright__logo ymaps-2-1-79-copyright__logo_lang_en')

        @staticmethod
        def listings_div(soup: BeautifulSoup) -> ResultSet[Tag]:
            return soup.find_all('div', class_='gl')

    @override
    class SoupExtractor:

        @staticmethod
        def price(soup: BeautifulSoup) -> Optional[str]:
            """Extracts the price from the soupified listing page.

            *If none are found it defaults to 0*

            :param soup: The soupified listing page
            :returns: The found string of the price in the soup
            """

            price: Tag | NavigableString | None = ListAm.SoupFinder.price(soup)

            if price is None:
                return None

            if isinstance(price, NavigableString):
                return str(price)

            if 'content' not in price.attrs.keys():
                return None

            return str(price.attrs['content'])

        @staticmethod
        def currency(soup: BeautifulSoup) -> Optional[str]:
            """Extracts the currency from the soupified listing page.

            :param soup: The soupified listing page
            :returns: The found string of the currency in the soup
            """
            currency: Tag | NavigableString | None = ListAm.SoupFinder.currency(soup)

            if currency is None:
                return None

            if type(currency) is NavigableString:
                return str(currency)

            if 'content' not in currency.attrs.keys():  # type: ignore
                return None

            return str(currency.attrs['content'])  # type: ignore

        @staticmethod
        def coordinates(soup: BeautifulSoup) -> Optional[str]:
            """Extracts the coordinates from the soupified listing page.

            :param soup: The soupified listing page
            :returns: The found string of the coordinates in the soup
            """

            coordinates: Optional[Tag | NavigableString] = ListAm.SoupFinder.coordinates(soup)

            if coordinates is None:
                return None

            if isinstance(coordinates, NavigableString):
                return str(coordinates)

            if 'href' not in coordinates.attrs.keys():
                return None

            url_params = dict(parse.parse_qsl(parse.urlsplit(coordinates.attrs['href']).query))

            if 'll' in url_params.keys():
                return url_params['ll']

            if 'amp;ll' in url_params.keys():
                return url_params['amp;ll']

            return None

        @staticmethod
        def address(soup: BeautifulSoup) -> Optional[str]:
            """Extracts the address from the soupified lexcept TimeoutException:isting page.

            :param soup: The soupified listing page
            :returns: The found string of the address in the soup
            """

            address: Tag | NavigableString | None = ListAm.SoupFinder.address(soup)

            if address is None:
                return None

            if type(address) is NavigableString:
                return str(address)

            return address.text

        @staticmethod
        def miscellaneous(soup: BeautifulSoup) -> dict[str, Any]:
            """Extracts the rest of the data on the page from the soupified listing page.

            Most of the data is organized in a weird way, scrapping it all was easier.

            :param soup: The soupified listing page
            :returns: The found string of the currency in the soup
            """

            categories: ResultSet[Tag] = soup.find_all('div', class_='attr g')

            miscellaneous: dict[str, str] = {}

            for category in categories:
                divs: ResultSet[Tag] = category.find_all('div', class_='c')

                for div in divs:
                    title: Tag | NavigableString | None = div.find('div', class_='t')
                    info: Tag | NavigableString | None = div.find('div', class_='i')

                    if title is None or info is None:
                        continue

                    miscellaneous[title.text] = info.text

            return ListAm.SoupExtractor._parse_miscellaneous_titles(miscellaneous)

        # @override
        @staticmethod
        def get_listing_data(html: str, url: str) -> dict[str, Any]:

            soup = BeautifulSoup(html, 'html.parser')

            x_coord: str = ""
            y_coord: str = ""

            coordinates: Optional[str] = ListAm.SoupExtractor.coordinates(soup)
            if coordinates is not None:
                splitted_coordinates: list[str] = coordinates.split(',')
                x_coord = splitted_coordinates[0]
                y_coord = splitted_coordinates[1]

            data: dict[str, Any] = {
                                       "id": extract_first_numbers(url),
                                       "links": url,
                                       "source": LIST_AM_LINK,
                                       "address": ListAm.SoupExtractor.address(soup),
                                       "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                       "SHAPE": {
                                           "x": x_coord,
                                           "y": y_coord,
                                           'spatialReference': {'wkid': 4326, 'latestWkid': 4326}
                                       },
                                   } | ListAm.SoupExtractor.miscellaneous(soup)

            price = ListAm.SoupExtractor.price(soup)

            if price:
                data["price"] = currency_coverter.convert(
                    float(price),
                    ListAm.SoupExtractor.currency(soup), 'USD')
            else:
                data["price"] = None

            if data['price'] and data['square_meters']:
                data['price_per_meter'] = data['price'] / float(data['square_meters'])
            else:
                data['price_per_meter'] = None

            return data

        @staticmethod
        def _parse_miscellaneous_titles(miscellaneous: dict[str, str]) -> dict[str, str | int | float | None]:
            keys: Iterable[str] = miscellaneous.keys()

            parsed: dict[str, Any] = {}

            if (k := 'floors in the Building') in keys:
                parsed['building_floors'] = extract_first_numbers(miscellaneous[k])
            else:
                parsed['building_floors'] = None

            if (k := 'floor') in keys:
                parsed[k] = extract_first_numbers(miscellaneous[k])
            else:
                parsed[k] = None

            if (k := 'furniture') in keys:
                parsed[k] = False if 'Not' in miscellaneous[k] else True
            else:
                parsed[k] = None

            if (k := 'Ceiling height') in keys:
                parsed['height'] = extract_first_numbers(miscellaneous[k])
            else:
                parsed['height'] = None

            if (k := 'renovation') in keys:
                parsed[k] = miscellaneous[k]
            else:
                parsed[k] = None

            if (k := 'Number of rooms') in keys:
                parsed['rooms'] = extract_first_numbers(miscellaneous[k])
            else:
                parsed['rooms'] = None

            if (k := 'Number of bathrooms') in keys:
                parsed['bathroom'] = extract_first_numbers(miscellaneous[k])
            else:
                parsed['bathroom'] = None

            if (k := 'House Area') in keys:
                parsed['square_meters'] = ''.join(extract_numbers(miscellaneous[k]))
            elif (k := 'floor Area') in keys:
                parsed['square_meters'] = ''.join(extract_numbers(miscellaneous[k]))
            else:
                parsed['square_meters'] = None

            return parsed

    def __init__(self, webdriver: WebDriver, limit_per_category: Optional[int] = None, processed: Optional[list[str]] = None):
        super().__init__(webdriver=webdriver, url=LIST_AM_LINK, limit_per_category=limit_per_category, processed=processed)

    @override
    def set_page(self, page: int) -> None:
        super().set_page(page)
        self.options = f"/{self.current_page}?gl=1"

    @override
    def open_map(self) -> bool:

        map_link: WebElement

        try:
            map_link = self.wait.until(ec.element_to_be_clickable((By.XPATH, self.XPaths.YANDEX_MAP.value)))
        except (TimeoutException, TimeoutError):
            return False

        map_link.click()

        yandex_logo: WebElement

        try:
            yandex_logo = self.wait.until(ec.element_to_be_clickable((By.XPATH, self.XPaths.YANDEX_LOGO.value)))
        except (TimeoutException, TimeoutError):
            return False

        ActionChains(self.webdriver) \
            .move_to_element(yandex_logo) \
            .perform()

        return True

    @override
    def get_listings_links_from_gallery(self, url: str) -> list[str]:

        self.webdriver.get(url)
        self.wait.until(ec.url_to_be(url))

        return super().get_listings_links_from_gallery(url)

