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

REAL_ESTATE_AM = r"https://www.real-estate.am/en/"


class RealEstateAm(ListingScrapperBase):
    """The scrapper designed for real-estate.am"""

    @override
    class Endpoints(Enum):

        APARTMENTS_RENTAL = "rent/yerevan-apartment/?propertyActionType=RENT&propertyTypes=APARTMENT"
        HOUSE_RENTAL = "rent/yerevan-house/?propertyActionType=RENT&propertyTypes=HOUSE"

        APARTMENTS_SALE = "sale/yerevan-apartment/?propertyActionType=SALE&propertyTypes=APARTMENT"
        HOUSE_SALE = "sale/yerevan-house/?propertyActionType=SALE&propertyTypes=HOUSE"

    @override
    class SVGS(Enum):

        FLOORS = 'M14.238 3.45752H11.4978C11.0768 3.45752 10.7356 3.79846 10.7356 4.21961V6.19791H8.7573C8.33615 6.19791 7.99496 6.53873 7.99496 6.95991V8.93834H6.01665C5.59551 8.93834 5.25445 9.27965 5.25445 9.70036V11.7741H3.18119C2.97888 11.7741 2.78502 11.8543 2.64215 11.997C2.49915 12.1399 2.41895 12.3346 2.41895 12.5361L2.41919 14.1306C2.41919 14.5521 2.7605 14.893 3.1814 14.893H14.238C14.6591 14.893 15.0001 14.5521 15.0001 14.1306V4.21957C15.0002 3.79846 14.6591 3.45752 14.238 3.45752Z'
        HEIGHT = 'M3.83334 3.8249H5.325C5.7 3.8249 5.88334 3.3749 5.61667 3.11657L3.29167 0.799902C3.125 0.641569 2.86667 0.641569 2.7 0.799902L0.383336 3.11657C0.116669 3.3749 0.300003 3.8249 0.675003 3.8249H2.16667V12.1749H0.675003C0.300003 12.1749 0.116669 12.6249 0.383336 12.8832L2.70834 15.1999C2.875 15.3582 3.13334 15.3582 3.3 15.1999L5.625 12.8832C5.89167 12.6249 5.7 12.1749 5.33334 12.1749H3.83334V3.8249Z'

    @override
    class XPaths(Enum):

        FIRST_LISTING_OF_PAGE = '//*[@id="__next"]/div[1]/div[1]/div[2]/div/div[3]/div[1]/div/div[1]/a/div/div[2]'
        MAP_USER_AGREEMENT = '//*[@id="property-details-container"]/div/div[2]/div[2]/div/div/div[1]/ymaps/ymaps/ymaps/ymaps[3]/ymaps[2]/ymaps/ymaps[2]/ymaps/ymaps[1]/ymaps/ymaps[2]/a'
        MAP_USER_AGREEMENT_ALT = '//*[@id="property-details-container"]/div/div[2]/div/div/div/div[1]/ymaps/ymaps/ymaps/ymaps[3]/ymaps[2]/ymaps/ymaps[2]/ymaps/ymaps[1]/ymaps/ymaps[2]/a'

    @override
    class SoupFinder:

        @staticmethod
        def address(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('div', class_='PropertyTitleAndaddress_address_info__Ee_vF')

        @staticmethod
        def price(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('div', class_='Propertyprice_container__6_MBs PropertyDetails_price__mJO7i')

        @staticmethod
        def price_per_square_meter(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            return soup.find('div', class_='PropertyDetails_price_detailed_info___mHSJ')

        @staticmethod
        def amenities(soup: BeautifulSoup) -> ResultSet:
            return soup.find_all('div', class_='PropertyDetails_utility__8RVQg')

        @staticmethod
        def area(soup: BeautifulSoup) -> Optional[Tag]:
            element = soup.find('g', {'clip-path': "url(#clip0_1653_45530)"})

            if element is None:
                return None

            element_parent = element.parent

            if element_parent is None:
                return None

            return element_parent.parent

        @staticmethod
        def floors(soup: BeautifulSoup) -> Optional[Tag]:

            element = soup.find('path', d=RealEstateAm.SVGS.FLOORS.value)
            if element is None:
                return None

            element_parent = element.parent

            if element_parent is None:
                return None

            return element_parent.parent

        @staticmethod
        def height(soup: BeautifulSoup) -> Optional[Tag]:

            element = soup.find('path', d=RealEstateAm.SVGS.HEIGHT.value)
            if element is None:
                return None

            element_parent = element.parent

            if element_parent is None:
                return None

            return element_parent.parent

        @staticmethod
        def bathrooms(soup: BeautifulSoup) -> Optional[Tag]:

            element = soup.find('g', {'clip-path': "url(#clip0_1653_45537)"})

            if element is None:
                return None

            element_parent = element.parent

            if element_parent is None:
                return None

            return element_parent.parent

        @staticmethod
        def rooms(soup: BeautifulSoup) -> Optional[Tag]:

            element = soup.find('g', {'clip-path': "url(#clip0_1653_45506)"})

            if element is None:
                return None

            element_parent = element.parent

            if element_parent is None:
                return None

            return element_parent.parent

        @staticmethod
        def renovation(soup: BeautifulSoup) -> Optional[Tag]:

            element = soup.find('g', {'clip-path': "url(#clip0_195_10157)"})

            if element is None:
                return None

            element_parent = element.parent

            if element_parent is None:
                return None

            return element_parent.parent

        @staticmethod
        def coordinates(soup: BeautifulSoup) -> Optional[Tag | NavigableString]:
            scripts = soup.find_all('script', charset="utf-8", src=True)
            for script in scripts:
                if 'https://api-maps.yandex.ru/services/coverage/v2/' not in script['src']:
                    continue

                return script

            raise AssertionError("Shouldn't be reachable! (could not find map element on page)")

    @override
    class SoupExtractor:

        @staticmethod
        def price(soup: BeautifulSoup) -> str:

            price: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.price(soup)

            if price is None:
                return ""

            if isinstance(price, NavigableString):
                return str(price)

            return ''.join(extract_numbers(price.text))

        @staticmethod
        def coordinates(soup: BeautifulSoup) -> str:

            coordinates: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.coordinates(soup)

            if coordinates is None:
                return ""

            if isinstance(coordinates, NavigableString):
                return str(coordinates)

            if 'src' not in coordinates.attrs.keys():
                return ""

            url_params = dict(parse.parse_qsl(parse.urlsplit(coordinates.attrs['src']).query))

            if 'll' in url_params.keys():
                return url_params['ll']

            if 'amp;ll' in url_params.keys():
                return url_params['amp;ll']

            return ""

        @staticmethod
        def address(soup: BeautifulSoup) -> str:

            address_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.address(soup)

            if address_parent is None:
                return ""

            address: Optional[Tag | NavigableString] = address_parent.find('p')  # type: ignore

            if address is None:
                return ""

            if isinstance(address, NavigableString):
                return str(address)

            return address.text

        @staticmethod
        def price_per_square_meter(soup: BeautifulSoup) -> str:
            price_per_square_meter: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.price_per_square_meter(soup)

            if price_per_square_meter is None:
                return ""

            if isinstance(price_per_square_meter, NavigableString):
                return str(price_per_square_meter)

            return ''.join(extract_numbers(price_per_square_meter.text))

        @staticmethod
        def area(soup: BeautifulSoup) -> float | str:

            area_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.area(soup)

            if area_parent is None:
                return ""

            area = area_parent.find('p')

            if area is None:
                return ""

            if isinstance(area, NavigableString) or isinstance(area, int):
                return str(area)

            return extract_first_numbers(area.text)

        @staticmethod
        def height(soup: BeautifulSoup) -> float | str:

            height_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.height(soup)

            if height_parent is None:
                return ""

            height = height_parent.find('p')

            if height is None:
                return ""

            if isinstance(height, NavigableString) or isinstance(height, int):
                return str(height)

            return extract_first_numbers(height.text)

        @staticmethod
        def bathrooms(soup: BeautifulSoup) -> float | str:

            bathrooms_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.bathrooms(soup)

            if bathrooms_parent is None:
                return ""

            bathrooms = bathrooms_parent.find('p')

            if bathrooms is None:
                return ""

            if isinstance(bathrooms, NavigableString) or isinstance(bathrooms, int):
                return str(bathrooms)

            return extract_first_numbers(bathrooms.text)

        @staticmethod
        def rooms(soup: BeautifulSoup) -> float | str:

            rooms_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.rooms(soup)

            if rooms_parent is None:
                return ""

            rooms = rooms_parent.find('p')

            if rooms is None:
                return ""

            if isinstance(rooms, NavigableString) or isinstance(rooms, int):
                return str(rooms)

            return extract_first_numbers(rooms.text)

        @staticmethod
        def floor(soup: BeautifulSoup) -> float | str:

            floor_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.floors(soup)

            if floor_parent is None:
                return ""

            floor = floor_parent.find('p')

            if floor is None:
                return ""

            if isinstance(floor, NavigableString) or isinstance(floor, int):
                return str(floor)

            if '/' not in floor.text:  # if house
                return ""

            return extract_first_numbers(floor.text)

        @staticmethod
        def building_floors(soup: BeautifulSoup) -> float | str:

            floor_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.floors(soup)

            if floor_parent is None:
                return ""

            floor = floor_parent.find('p')

            if floor is None:
                return ""

            if isinstance(floor, NavigableString) or isinstance(floor, int):
                return str(floor)

            if '/' not in floor.text:  # if house
                return extract_first_numbers(floor.text)

            return extract_numbers(floor.text)[1]

        @staticmethod
        def renovation(soup: BeautifulSoup) -> str:

            renovation_parent: Optional[Tag | NavigableString] = RealEstateAm.SoupFinder.renovation(soup)

            if renovation_parent is None:
                return ""

            renovation = renovation_parent.find('p')

            if renovation is None:
                return ""

            if isinstance(renovation, NavigableString) or isinstance(renovation, int):
                return str(renovation)

            return renovation.text

        @staticmethod
        def furniture(soup: BeautifulSoup) -> bool | str:
            amenities: ResultSet = RealEstateAm.SoupFinder.amenities(soup)

            if amenities is None:
                return ""

            for amenity in amenities:
                if 'furniture' in amenity.text:
                    return True

            return False

        # @override
        @staticmethod
        def get_listing_data(html: str, url: str) -> dict[str, Any]:

            soup = BeautifulSoup(html, 'html.parser')

            coordinates: str = RealEstateAm.SoupExtractor.coordinates(soup)

            x_coord: str = "0"
            y_coord: str = "0"

            if coordinates:
                coordinates_list: list[str] = coordinates.split(',')

                x_coord = coordinates_list[0]
                y_coord = coordinates_list[1]

            data: dict[str, Any] = {
                "id": url[-7:][:-1],
                "links": url,
                "source": REAL_ESTATE_AM,
                "price": RealEstateAm.SoupExtractor.price(soup),
                "address": RealEstateAm.SoupExtractor.address(soup),
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "SHAPE": {
                    "x": x_coord,
                    "y": y_coord,
                    'spatialReference': {'wkid': 4326, 'latestWkid': 4326}
                },
                "price_per_meter": RealEstateAm.SoupExtractor.price_per_square_meter(soup),
                "square_meters": RealEstateAm.SoupExtractor.area(soup),
                "building_floors": RealEstateAm.SoupExtractor.building_floors(soup),
                "floor": RealEstateAm.SoupExtractor.floor(soup),
                "furniture": RealEstateAm.SoupExtractor.furniture(soup),
                "height": RealEstateAm.SoupExtractor.height(soup),
                "renovation": RealEstateAm.SoupExtractor.renovation(soup),
                "rooms": RealEstateAm.SoupExtractor.rooms(soup),
                "bathroom": RealEstateAm.SoupExtractor.bathrooms(soup),
            }

            if not data['price_per_meter'] and data['price'] and data['square_meters']:
                data['price_per_meter'] = float(data['price']) / float(data['square_meters'])

            return data

    def __init__(self, webdriver: WebDriver, limit_per_category: Optional[int] = None, processed: Optional[list[str]] = None) -> None:
        super().__init__(webdriver, url=REAL_ESTATE_AM, limit_per_category=limit_per_category, processed=processed)

    @override
    def get_listings_links_from_gallery(self, url: str) -> list[str]:

        self.webdriver.get(url)
        self.wait.until(ec.url_to_be(url))
        self.wait.until(ec.element_to_be_clickable((By.XPATH, self.XPaths.FIRST_LISTING_OF_PAGE.value)))

        soup = BeautifulSoup(self.webdriver.page_source, 'html.parser')

        listings_links: ResultSet[Tag] = soup.find_all('a', href=True)

        endpoints: list[str] = []

        for link in listings_links:
            if ('/en/' not in link['href']
                    or ('/buy' not in link['href'] and '/for-rent' not in link['href'])):
                continue
            endpoints.append(f"{link['href']}"[4:])  # we take out the `/en/`

            if self.limit_per_category and len(endpoints) >= self.limit_per_category:
                return endpoints

        return endpoints

    @override
    def open_map(self) -> bool:
        try:
            self.wait.until(ec.element_to_be_clickable((By.XPATH, self.XPaths.MAP_USER_AGREEMENT.value)))
            return True
        except TimeoutException:
            try:
                self.wait.until(ec.element_to_be_clickable((By.XPATH, self.XPaths.MAP_USER_AGREEMENT_ALT.value)))
                return True
            except TimeoutException:
                print("Map couldn't open!")
                return False

    @override
    def set_page(self, page: int) -> None:
        super().set_page(page)
        self.options = f"&page={self.current_page}&size=300&currency=USD"
