import pandas as pd
from pandas import DataFrame
from ListAm import ListAm
from EstateAm import EstateAm
from RealEstateAm import RealEstateAm

# import selenium.webdriver as webdriver
import undetected_chromedriver as uc  # type: ignore

options = uc.ChromeOptions()
options.add_argument('--blink-settings=imagesEnabled=false')

driver = uc.Chrome(options=options)


df: DataFrame = pd.read_csv('csvs/housings.csv', sep='\t', header=0)
processed = list(df.links)

new_df = ListAm(driver, limit_per_category=10, processed=processed).to_data_frame()
if len(new_df) > 0:
    df = pd.concat([df, new_df], ignore_index=True, sort=False)

new_df = EstateAm(driver, limit_per_category=10, processed=processed).to_data_frame()
if len(new_df) > 0:
    df = pd.concat([df, new_df], ignore_index=True, sort=False)

new_df = RealEstateAm(driver, limit_per_category=10, processed=processed).to_data_frame()
if len(new_df) > 0:
    df = pd.concat([df, new_df], ignore_index=True, sort=False)

df.to_csv('csvs/housings.csv', sep='\t', index=False)

driver.close()
