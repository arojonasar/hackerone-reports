"""
This script runs first.

It will scroll through hacktivity until the appearance of URL of the first report in data.csv.
Then script searches for all new reports' URLs and add them to data.csv.

To use it without modifications you should put non-empty data.csv file
in the same directory with this script (current data.csv is good), because
scrolling through the whole hacktivity is almost impossible for now.
"""

import time
import csv
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By

hacktivity_url = 'https://hackerone.com/hacktivity/overview?queryString=disclosed%3Atrue&sortField=disclosed_at&sortDirection=DESC&pageIndex=0'
page_loading_timeout = 5

def create_argument_parser():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        '--browser-binary',
        type=str,
        help='Path to browser binary (Chrome or Chromium)',
        default="C:/Program Files/Google/Chrome/Application/chrome.exe")
    argparser.add_argument(
        '--input-data-file',
        type=str,
        help='Path to input data file',
        default='data.csv'
    )
    argparser.add_argument(
        '--output-data-file',
        type=str,
        help='Path to output data file',
        default='data.csv'
    )
    return argparser

def extract_reports(raw_reports):
    reports = []
    for raw_report in raw_reports:
        href = raw_report.get_attribute("href")
        if not href or "/reports/" not in href:
            continue
        report = {
            'program': '',
            'title': '',
            'reporter': '',
            'link': href,
            'upvotes': 0,
            'bounty': 0.,
            'vuln_type': '',
            'substate': '',
            'severity': '',
            'asset_type': '',
            'submitted_at': '',
            'disclosed_at': ''
        }
        reports.append(report)
    return reports

def fetch(commandline_args):
    options = ChromeOptions()
    options.binary_location = commandline_args.browser_binary
    options.add_argument('--no-sandbox')
    options.add_argument('--headless=new')
    options.add_argument("--js-flags=--max-old-space-size=4096")
    # driver = Chrome(options=options)
    driver = webdriver.Safari()

    reports = []
    with open(commandline_args.input_data_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            reports.append(dict(row))
    first_report_link = reports[0]["link"] if reports else None
    print("First known report link:", first_report_link)

    try:
        driver.get(hacktivity_url)
        time.sleep(page_loading_timeout)

        page = 0
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        new_reports = []

        while True:
            raw_reports = driver.find_elements(By.CLASS_NAME, 'routerlink')
            page_reports = extract_reports(raw_reports)

            found = False
            for i, rep in enumerate(page_reports):
                link = rep.get('link')
                if first_report_link and link == first_report_link:
                    reports = page_reports[:i] + reports
                    found = True
                    break

            if found:
                print("Found first known report, stopping.")
                break

            new_reports.extend(page_reports)
            
            page += 1
            print("Page:", page)

            try:
                next_page_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='hacktivity-pagination--pagination-next-page']")
                driver.execute_script("arguments[0].click();", next_page_button)
                time.sleep(page_loading_timeout)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except Exception:
                print("No next page button found; stopping.")
                break

    except Exception as e:
        print("Error:", e)
        now = datetime.now().strftime('%Y-%m-%d')
        driver.get_screenshot_as_file(f'error-{now}.png')
    finally:
        driver.quit()

    all_reports = new_reports + reports
    with open(commandline_args.output_data_file, 'w', newline='', encoding='utf-8') as file:
        keys = all_reports[0].keys()
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(all_reports)

if __name__ == '__main__':
    parser = create_argument_parser()
    args = parser.parse_args()
    fetch(args)
