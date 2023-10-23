############################################################################################
# Required Includes
############################################################################################

# Importing necessary libraries and modules
import requests  # for making HTTP requests
import json  # for handling JSON data
from bs4 import BeautifulSoup  # for parsing HTML content
from urllib.parse import urljoin, urlparse  # for URL manipulation
from concurrent.futures import ThreadPoolExecutor  # for concurrent execution of functions
import random  # for generating random numbers
import re  # for regular expression operations
import os  # for file and directory operations
import tempfile  # for creating temporary files
from threading import Lock  # for thread synchronization
from robotexclusionrulesparser import RobotFileParserLookalike  # for parsing robots.txt files
from selenium import webdriver  # for web scraping with browser automation
from selenium.webdriver.firefox.options import Options  # for configuring Firefox options
from bs4 import BeautifulSoup  # for parsing HTML content
from bs4.element import Comment  # for identifying comment elements in HTML
import logging  # for logging messages
import time  # for time-related operations
from tldextract import extract  # for extracting components of a domain

# Initialize logging configuration
# logging.basicConfig(level=logging.INFO)

############################################################################################
# Functions & Classes
############################################################################################

# Function to determine if a tag is visible on a webpage
def tag_visible(element):
    # List of tags that, if an element is a child of them, the element is considered invisible
    invisible_tags = ["style", "script", "head", "title", "meta", "[document]"]
    if element.parent.name in invisible_tags:
        return False
    if isinstance(element, Comment):  # If the element is a comment, it's considered invisible
        return False
    return True  # If none of the above conditions are met, the element is considered visible

# Function to extract visible text from HTML content
def text_from_html(body):
    soup = BeautifulSoup(body, "html.parser")  # Parse the HTML content
    # Filter out visible text elements and join them into a single string
    visible_texts = filter(tag_visible, soup.find_all(text=True))
    return " ".join(t.strip() for t in visible_texts)

# Function to check if a webpage primarily uses JavaScript for content loading
def uses_javascript(html_content):
    visible_text = text_from_html(html_content)  # Extract visible text from the HTML content
    return len(visible_text) < 2000  # If the amount of visible text is below a threshold, assume JavaScript is used

# Function to scrape a URL's content using Selenium for JavaScript-heavy websites
def scrape_url_with_selenium(url):
    options = Options()
    options.headless = True  # Run the browser in headless mode (no GUI)
    driver = webdriver.Firefox(options=options)  # Initialize a Firefox webdriver with the specified options
    
    driver.get(url)  # Navigate to the specified URL
    driver.implicitly_wait(10)  # Wait for JavaScript to execute
    
    html_content = driver.page_source  # Get the page's HTML content
    driver.quit()  # Close the browser
    return html_content

# Initialize RobotFileParserLookalike for parsing robots.txt files
robots_parser = RobotFileParserLookalike()

# Function to check if scraping a URL is allowed based on robots.txt
def is_allowed(url):
    return robots_parser.can_fetch("*", url)  # Check if the URL can be fetched by any user-agent

# Function to clean and normalize text
def clean_text(text):
    text = " ".join(text.split())  # Remove extra whitespaces
    text = text.replace("\n", " ").replace("\r", "")  # Remove line breaks
    text = re.sub(r"[^\w\s]", "", text)  # Remove special characters or punctuations
    return text

# Create a global lock for thread-safe operations on JSON data
json_lock = Lock()

# Function to read scraped data from a JSON file
def read_scraped_data(filename):
    with json_lock:  # Acquire the lock to ensure thread safety
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"An error occurred while reading JSON data: {e}")
            return {"a_id": a_id, "b_id": b_id, "webpages": []}

# Function to write scraped data to a JSON file
def write_scraped_data(data, filename):
    with json_lock:  # Acquire the lock to ensure thread safety
        try:
            with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            os.replace(f.name, filename)
        except Exception as e:
            logging.error(f"An error occurred while writing JSON data: {e}")

# Function to check if a URL is valid and belongs to the same domain as the base URL
def is_valid(url, base_url):
    parsed = urlparse(url)
    base_parsed = urlparse(base_url)
    return bool(parsed.netloc) and parsed.netloc == base_parsed.netloc

# Function to get all valid links from a webpage's HTML content
def get_all_links(html_content, base_url):
    soup = BeautifulSoup(html_content, "html.parser")  # Parse the HTML content
    links = [a.get("href") for a in soup.find_all("a", href=True)]  # Extract all links
    # Validate and join relative links with the base URL
    return [urljoin(base_url, link) for link in links if is_valid(urljoin(base_url, link), base_url)]

# Function to get a random user-agent string from a predefined list
def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537",
        "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.1.249.1045 Safari/532.5",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.2309.372 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:64.0) Gecko/20100101 Firefox/64.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
        "Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.111 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
    ]
    return random.choice(user_agents)  # Return a random user-agent string

# Function to scrape a URL's content and find links to other pages
def scrape_url(url, max_depth, visited, base_url, filename):
    time.sleep(1)  # Delay to avoid overloading the server
    if url in visited or max_depth < 0:  # Stop if URL has been visited or max depth reached
        return

    parsed_url = urlparse(url)
    parsed_base_url = urlparse(base_url)
    if parsed_url.netloc != parsed_base_url.netloc:  # Skip if URL is not in the same domain as the starting URL
        print(f"Skipping {url} as it is not in the same domain as the starting URL.")
        return

    if not is_allowed(url):  # Check robots.txt to see if scraping is allowed
        print(f"Skipping {url} due to robots.txt")
        return

    print(f"Scraping {url}")
    visited.add(url)  # Mark the URL as visited

    headers = {"User-Agent": get_random_user_agent()}  # Set a random user-agent

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
    except requests.RequestException as e:
        logging.error(f"An error occurred while making a request to {url}: {e}")
        return

    try:
        if uses_javascript(response.text):  # Check if the webpage relies on JavaScript
            print(f"{url} seems to rely on JavaScript, using Selenium for scraping.")
            html_content = scrape_url_with_selenium(url)
        else:
            html_content = response.text

        soup = BeautifulSoup(html_content, "html.parser")
        # Remove certain HTML elements that typically don't contain main content
        for tag in soup.find_all(["nav", "header", "footer", "a", "button", "script", "style"]):
            tag.decompose()
        main_content = soup.find("body")
        text = main_content.text.strip() if main_content else soup.text.strip()
        cleaned_text = clean_text(text)  # Clean and normalize the text

        # Read, update, and write the scraped data
        scraped_data = read_scraped_data(filename)
        website_data = {"url": url, "content": cleaned_text, "a_id": a_id, "b_id": b_id}
        scraped_data["webpages"].append(website_data)
        write_scraped_data(scraped_data, filename)

        # Recursively scrape URLs found in the current page
        links = get_all_links(html_content, url)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(scrape_url, link, max_depth - 1, visited, base_url, filename) for link in links]
            for future in futures:
                future.result()
    except requests.RequestException as e:
        logging.error(f"An error occurred while scraping {url}: {e}")

# Function to generate a filename based on the URL
def generate_filename_from_url(url):
    tsd, td, tsu = extract(url)  # Extract components of the domain
    return f"{td}_scraped_content.json"

############################################################################################
# Main Function
############################################################################################

def main(start_url, max_depth=3, output_file=None):
    visited = set()  # Set to keep track of visited URLs

    # Fetch and parse robots.txt
    robots_url = urljoin(start_url, "robots.txt")
    try:
        robots_response = requests.get(robots_url)
        if robots_response.status_code == 200:
            robots_parser.parse(robots_response.text.splitlines())
    except requests.RequestException as e:
        print(f"Failed to fetch or parse robots.txt from {start_url}, proceeding anyway: {e}")

    # Generate filename if not provided
    filename = output_file if output_file else generate_filename_from_url(start_url)
    scrape_url(start_url, max_depth, visited, start_url, filename)  # Start scraping

if __name__ == "__main__":
    start_url = input("Please enter the starting URL: ")  # Ask the user for the URL
    max_depth = 3
    a_id = "aaa"
    b_id = "bbbb"
    main(start_url, max_depth)
