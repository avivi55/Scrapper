import re


def extract_numbers(s: str) -> list:
    return re.findall(r'\b\d+\.?\d*', s)


def extract_first_numbers(s: str) -> float | str:
    if reg := extract_numbers(s):
        return float(reg[0])
    return ""

