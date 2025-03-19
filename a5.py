
import sys
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
from bs4 import BeautifulSoup

# Configure Gemini AI
genai.configure(api_key="AIzaSyDDljnJthyMihrzv3fjIvgmltaNKBAy12o")

def fetch_webpage(url):
    """Fetch full webpage content using Selenium with improvements for general websites."""
    
    # Setup Chrome WebDriver with more realistic browser settings
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (no GUI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    
    # Add a realistic user agent
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Disable automation flags that might trigger anti-bot measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Launch browser
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Set page load timeout
    driver.set_page_load_timeout(30)
    
    try:
        # Add a small random delay to mimic human behavior
        time.sleep(random.uniform(1, 2))
        
        driver.get(url)
        
        # Wait for the page to load properly
        wait_time = 8
        WebDriverWait(driver, wait_time).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Scroll down to load lazy-loaded content
        scroll_pause_time = 0.8
        screen_height = driver.execute_script("return window.screen.height;")
        i = 1
        
        # Scroll gradually to trigger lazy loading (works for most modern websites)
        for scroll in range(3):  # Scroll 3 times
            driver.execute_script(f"window.scrollTo(0, {screen_height * i});")
            i += 1
            time.sleep(scroll_pause_time)
        
        # Scroll back to top
        driver.execute_script("window.scrollTo(0, 0);")
        
        html_content = driver.page_source
        
        # Extract meaningful text elements that work across different types of websites
        elements = driver.find_elements(By.CSS_SELECTOR, 
            "h1, h2, h3, h4, h5, p, li, td, th, figcaption, blockquote, article, section, div.content, " + 
            "span[class*='text'], div[class*='text'], div[class*='content'], meta[name='description'], " +
            "meta[property='og:description'], meta[property='og:title'], img[alt]")
        
        extracted_text = []
        for el in elements:
            text = el.text or el.get_attribute("content") or el.get_attribute("alt")
            if text and text.strip():
                extracted_text.append(text.strip())
        
        # Remove duplicates while preserving order
        seen = set()
        extracted_text = [x for x in extracted_text if not (x in seen or seen.add(x))]
        
    except Exception as e:
        print(f"Error fetching content: {e}")
        return None, []
    finally:
        driver.quit()  # Close the browser
    
    return html_content, extracted_text

def extract_data(html_content, extracted_text):
    """Extracts title, metadata and main content from HTML."""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Get basic metadata
    metadata = {}
    
    # Title
    title = soup.title.string if soup.title else "No Title Found"
    metadata["title"] = title.strip() if title else "No Title Found"
    
    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        metadata["description"] = meta_desc.get("content", "")
    
    # Open Graph data (used by social media)
    og_title = soup.find("meta", property="og:title")
    if og_title:
        metadata["og_title"] = og_title.get("content", "")
    
    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        metadata["og_description"] = og_desc.get("content", "")
    
    # Try to identify main content
    main_content = ""
    
    # Common selectors for main content
    main_selectors = ["main", "article", "#content", ".content", "#main", ".main", ".post", ".article"]
    for selector in main_selectors:
        main_element = soup.select_one(selector)
        if main_element:
            main_content = main_element.get_text(strip=True, separator=" ")
            break
    
    return {
        "metadata": metadata,
        "content": extracted_text,
        "main_content": main_content if main_content else ""
    }

def process_with_gemini(data):
    """Send extracted data to Gemini AI for general summarization."""
    model = genai.GenerativeModel("gemini-1.5-pro")
    
    # Create a generic prompt that works for any website
    prompt = f"""
    Analyze and summarize the following webpage content:
    
    TITLE: {data['metadata'].get('title', 'No title')}
    
    DESCRIPTION: {data['metadata'].get('description', 'No description')}
    
    MAIN CONTENT EXCERPT:
    {data['main_content'][:500] if data['main_content'] else 'No main content identified'}
    
    EXTRACTED CONTENT:
    {' '.join(data['content'][:50])}
    
    Please provide:
    1. What type of webpage this appears to be (article, product page, home page, etc.)
    2. The main topic or purpose of the page
    3. Key information present on the page
    4. A concise summary of the content (3-5 sentences)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text if response else "No response from Gemini AI"
    except Exception as e:
        return f"Error processing with Gemini AI: {e}"

def main():
    """Main function to extract, process, and save data."""
    if len(sys.argv) < 2:
        print("Usage: python script.py <URL>")
        return
    
    url = sys.argv[1]  # Get URL from command-line argument
    print(f"Fetching content from: {url}")
    
    html_content, extracted_text = fetch_webpage(url)
    
    if html_content:
        extracted_data = extract_data(html_content, extracted_text)
        ai_processed_data = process_with_gemini(extracted_data)
        
        output_data = {
            "url": url,
            "original_data": extracted_data,
            "ai_processed_data": ai_processed_data
        }
        
        with open("extracted_data2.json", "w", encoding="utf-8") as json_file:
            json.dump(output_data, json_file, indent=4)
        
        print(" Data successfully extracted and saved in 'extracted_data2.json'!")
    else:
        print(" Failed to fetch content from the URL.")

if __name__ == "__main__":
    main()