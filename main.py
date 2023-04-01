import argparse
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm.contrib.concurrent import thread_map
from webdriver_manager.chrome import ChromeDriverManager


def compress(args):
    path, args = args
    name = os.path.basename(path)
    download_name = name.replace(".pdf", "-compressed.pdf")

    if os.path.exists(f'output/{name}'):
        return

    service = Service(ChromeDriverManager().install())
    chrome_options = webdriver.ChromeOptions()
    output_path = f'{Path("output").absolute().__str__()}{os.sep}'
    prefs = {
        'download': {
            'default_directory': output_path,
            'directory_upgrade': True,
            'prompt_for_download': False,
        }
    }
    chrome_options.add_experimental_option('prefs', prefs)

    with webdriver.Chrome(service=service, options=chrome_options) as driver:
        driver.get("https://www.adobe.com/ca/acrobat/online/compress-pdf.html")

        # upload file
        selector = (By.CSS_SELECTOR, 'input[type="file"]')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located(selector))
        input = driver.find_element(*selector)
        input.send_keys(path)

        # click convert button
        selector = (By.CSS_SELECTOR, 'button[data-test-id="ls-footer-primary-compress-button"]')
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable(selector))
        button = driver.find_element(*selector)
        driver.execute_script("arguments[0].click();", button)

        # click download button
        selector = (By.CSS_SELECTOR, 'button[data-test-id="download"]')
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable(selector))
        button = driver.find_element(*selector)
        driver.execute_script("arguments[0].click();", button)

        # wait for download
        WebDriverWait(driver, 300).until(
            lambda _: os.path.exists(f'output/{download_name}')
        )

    os.rename(
        f'output/{download_name}',
        f'output/{name}'
    )

    if args.remove:
        os.remove(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--remove",
        action="store_true",
        help="Remove input files after compression"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=8,
        help="Number of workers to use"
    )

    args = parser.parse_args()

    if not os.path.exists("input"):
        os.makedirs("input")

    if not os.path.exists("output"):
        os.makedirs("output")

    files = [entry for entry in os.scandir(
        Path("input").absolute()) if entry.is_file()]

    thread_map(
        compress,
        [(file.path, args) for file in files],
        max_workers=args.max_workers
    )


if __name__ == "__main__":
    main()
