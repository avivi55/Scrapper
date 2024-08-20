import currency_coverter
from utils import extract_first_numbers, extract_numbers
from ListingScrapperBase import ListingScrapperBase

from datetime import datetime

from enum import Enum
from typing import Any, Optional, override

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from bs4 import BeautifulSoup, NavigableString, ResultSet, Tag
from urllib import parse

from rich import print

ESTATE_AM = r"https://www.estate.am/en/"


class EstateAm(ListingScrapperBase):
    """The scrapper designed for estate.am"""

    @override
    class Endpoints(Enum):

        APARTMENTS_RENTAL = "apartments-rentals-s556"
        HOUSE_RENTAL = "houses-and-villas-rentals-s649"

        APARTMENTS_SALE = "apartments-for-sale-s259"
        HOUSE_SALE = "houses-and-villas-for-sale-s122"

    @override
    class XPaths(Enum):

        FIRST_LISTING_OF_PAGE = '//*[@id="listing"]/div[2]/div[1]'

    @override
    class SoupFinder:

        @staticmethod
        def address(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('strong', class_='addr')

        @staticmethod
        def price(soup: BeautifulSoup) -> ResultSet:
            return soup.find_all('div', class_='price-w')

        @staticmethod
        def area(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('span', class_='ruler')

        @staticmethod
        def floors(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('span', class_='floor')

        @staticmethod
        def bathrooms(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            elements = soup.find_all('li', class_='active')

            for el in elements:
                if 'bathrooms' in el.text:
                    return el

            return None

        @staticmethod
        def rooms(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('span', class_='rooms')

        @staticmethod
        def description(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('p', string=True)

        @staticmethod
        def renovation(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            elements = soup.find_all('li', class_='active')

            for el in elements:
                if 'Repairment:' in el.text:
                    return el

            return None

        @staticmethod
        def coordinates(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            scripts = soup.find_all('script', charset="utf-8", src=True)
            for script in scripts:
                if 'https://api-maps.yandex.ru/services/coverage/v2/' not in script['src']:
                    continue

                return script

            raise AssertionError("Shouldn't be reachable! (could not find map element on page)")

        @staticmethod
        def listings_div(soup: BeautifulSoup) -> ResultSet:
            return soup.find_all('a', class_='img', target='_blank', href=True)

    @override
    class SoupExtractor:

        @staticmethod
        def price(soup: BeautifulSoup, rent_or_sale: str) -> str:

            prices: ResultSet = EstateAm.SoupFinder.price(soup)

            for price in prices:
                label = price.find('span')

                if label is None or isinstance(label, NavigableString):
                    continue

                if 'Sale' in label.text and rent_or_sale == 'sale':
                    return ''.join(extract_numbers(price.text))

                if 'Rent' in label.text and rent_or_sale == 'rent':
                    return ''.join(extract_numbers(price.text))

            return ''

        @staticmethod
        def currency(soup: BeautifulSoup, rent_or_sale: str) -> str:

            prices: ResultSet = EstateAm.SoupFinder.price(soup)

            for price in prices:
                label = price.find('span')

                if label is None or isinstance(label, NavigableString):
                    continue

                if 'Sale' in label.text and rent_or_sale == 'sale':
                    if 'Դ' in price.text:
                        return 'AMD'

                    if '$' in price.text:
                        return 'USD'

                if 'Rent' in label.text and rent_or_sale == 'rent':
                    if 'Դ' in price.text:
                        return 'AMD'

                    if '$' in price.text:
                        return 'USD'

            return ''

        @staticmethod
        def coordinates(soup: BeautifulSoup) -> Optional[str]:

            try:
                coordinates: Optional[Tag | NavigableString] = EstateAm.SoupFinder.coordinates(soup)
            except AssertionError:
                return None

            if coordinates is None:
                return None

            if isinstance(coordinates, NavigableString):
                return str(coordinates)

            if 'src' not in coordinates.attrs.keys():
                return None

            url_params = dict(parse.parse_qsl(parse.urlsplit(coordinates.attrs['src']).query))

            if 'll' in url_params.keys():
                return url_params['ll']

            if 'amp;ll' in url_params.keys():
                return url_params['amp;ll']

            return None

        @staticmethod
        def address(soup: BeautifulSoup) -> Optional[str]:

            address: Optional[Tag | NavigableString] = EstateAm.SoupFinder.address(soup)

            if address is None:
                return None

            if isinstance(address, NavigableString):
                return str(address)

            return address.text

        @staticmethod
        def area(soup: BeautifulSoup) -> Optional[float | str]:

            area: Optional[Tag | NavigableString] = EstateAm.SoupFinder.area(soup)

            if area is None:
                return None

            if isinstance(area, NavigableString):
                return str(area)

            return extract_first_numbers(area.text)

        @staticmethod
        def height(soup: BeautifulSoup) -> None:
            return None

        @staticmethod
        def bathrooms(soup: BeautifulSoup) -> Optional[float | str]:

            bathrooms: Optional[Tag | NavigableString] = EstateAm.SoupFinder.bathrooms(soup)

            if bathrooms is None:
                return None

            if isinstance(bathrooms, NavigableString):
                return str(bathrooms)

            return extract_first_numbers(bathrooms.text)

        @staticmethod
        def rooms(soup: BeautifulSoup) -> Optional[float | str]:

            rooms: Optional[Tag | NavigableString] = EstateAm.SoupFinder.rooms(soup)

            if rooms is None:
                return None

            if isinstance(rooms, NavigableString) or isinstance(rooms, int):
                return str(rooms)

            return extract_first_numbers(rooms.text)

        @staticmethod
        def floor(soup: BeautifulSoup) -> Optional[float | str]:

            floor: Optional[Tag | NavigableString] = EstateAm.SoupFinder.floors(soup)

            if floor is None:
                return None

            if isinstance(floor, NavigableString) or isinstance(floor, int):
                return str(floor)

            if '/' not in floor.text:  # if house
                return None

            return extract_first_numbers(floor.text)

        @staticmethod
        def building_floors(soup: BeautifulSoup) -> Optional[float | str]:

            floor: Optional[Tag | NavigableString] = EstateAm.SoupFinder.floors(soup)

            if floor is None:
                return None

            if isinstance(floor, NavigableString) or isinstance(floor, int):
                return str(floor)

            if '/' not in floor.text:  # if house
                return extract_first_numbers(floor.text)

            numbers = extract_numbers(floor.text)

            return numbers[1] if len(numbers) > 1 else ""

        @staticmethod
        def renovation(soup: BeautifulSoup) -> Optional[str]:

            renovation: Optional[Tag | NavigableString] = EstateAm.SoupFinder.renovation(soup)

            if renovation is None:
                return None

            if isinstance(renovation, NavigableString) or isinstance(renovation, int):
                return str(renovation)

            return renovation.text.split(': ')[1]

        @staticmethod
        def furniture(soup: BeautifulSoup) -> Optional[bool | str]:
            description: Optional[Tag | NavigableString] = EstateAm.SoupFinder.description(soup)

            if description is None:
                return None

            if isinstance(description, NavigableString):
                return str(description)

            if 'furnished' in description.text:
                return True

            if 'furniture' in description.text:
                return True

            return False

        # @override
        @staticmethod
        def get_listing_data(html: str, url: str, rent_or_sale: str) -> dict[str, Any]:

            soup = BeautifulSoup(html, 'html.parser')

            coordinates: str = EstateAm.SoupExtractor.coordinates(soup)

            x_coord: str = "0"
            y_coord: str = "0"

            if coordinates:
                coordinates_list: list[str] = coordinates.split(',')

                x_coord = coordinates_list[0]
                y_coord = coordinates_list[1]

            data: dict[str, Any] = {
                "id": url[-6:],
                "links": url,
                "source": ESTATE_AM,
                "address": EstateAm.SoupExtractor.address(soup),
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "SHAPE": {
                    "x": x_coord,
                    "y": y_coord,
                    'spatialReference': {'wkid': 4326, 'latestWkid': 4326}
                },
                "square_meters": EstateAm.SoupExtractor.area(soup),
                "building_floors": EstateAm.SoupExtractor.building_floors(soup),
                "floor": EstateAm.SoupExtractor.floor(soup),
                "furniture": EstateAm.SoupExtractor.furniture(soup),
                "height": EstateAm.SoupExtractor.height(soup),
                "renovation": EstateAm.SoupExtractor.renovation(soup),
                "rooms": EstateAm.SoupExtractor.rooms(soup),
                "bathroom": EstateAm.SoupExtractor.bathrooms(soup),
            }

            price = EstateAm.SoupExtractor.price(soup, rent_or_sale)

            if price:
                data["price"] = currency_coverter.convert(
                    float(price),
                    EstateAm.SoupExtractor.currency(soup, rent_or_sale), 'USD')
            else:
                data["price"] = None

            if data['price'] and data['square_meters']:
                data['price_per_meter'] = float(data['price']) / float(data['square_meters'])
            else:
                data['price_per_meter'] = ""

            return data

    def __init__(self,
                 webdriver: WebDriver,
                 limit_per_category: Optional[int] = None,
                 processed: Optional[list[str]] = None) -> None:
        super().__init__(webdriver, url=ESTATE_AM, limit_per_category=limit_per_category, processed=processed)

    @override
    def set_page(self, page: int) -> None:
        super().set_page(page)
        self.options = f"?page={self.current_page}&view=gallery"

    @override
    def get_listings_links_from_gallery(self, url: str) -> list[str]:
        """Finds the endpoints to each listing on the url.

        :param url: The url of the page to open
        :raises TimeoutException:
        :returns: The list of the listings endpoints
        """
        self.webdriver.get(url)
        self.wait.until(ec.url_to_be(url))
        self.wait.until(ec.element_to_be_clickable((By.XPATH, self.XPaths.FIRST_LISTING_OF_PAGE.value)))

        return super().get_listings_links_from_gallery(url)

    @override
    def open_map(self) -> bool:
        try:
            self.wait.until(ec.element_to_be_clickable((By.CLASS_NAME, 'ymaps-2-1-79-copyright__link')))
            return True
        except TimeoutException:
            print("Map couldn't open!")
            return False
