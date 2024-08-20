from typing import Optional

import requests

amd_data = requests.get('https://open.er-api.com/v6/latest/AMD').json()
usd_data = requests.get('https://open.er-api.com/v6/latest/USD').json()


def convert(amount: float, base: Optional[str], to: Optional[str]) -> float:
    """Converts an amount of AMD or USD to most currencies

    :param amount: The amount of AMD or USD.
    :param base: The base currency.
    :param to: The target currency.
    :return: The converted amount.
    """

    if not base or not to:
        return 0

    if base == 'AMD':
        return amount * amd_data['rates'][to]

    if base == 'USD':
        return amount * usd_data['rates'][to]

    print("UNABLE TO CONVERT")

    return 0
