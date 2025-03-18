import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
genai.configure(api_key="AIzaSyAiWfvY1AZq03mjrqmCdkFRY8uuacnV3NE")  
def fetch_webpage(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        print(f"Failed to fetch webpage. Status Code: {response.status_code}")
        return None

def extract_data(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    title = soup.title.string if soup.title else "No Title Found"
    paragraphs = [p.get_text() for p in soup.find_all("p")]
    return {"title": title, "paragraphs": paragraphs}


def process_with_gemini(data):
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = f"Extract whole context from the provided website:\n{data}"
    response = model.generate_content(prompt)
    return response.text if response else "No response from Gemini AI"


def main():
    url = "https://www.keka.com/"  
    html_content = fetch_webpage(url)

    if html_content:
        extracted_data = extract_data(html_content)
        ai_processed_data = process_with_gemini(extracted_data)

        output_data = {
            "original_data": extracted_data,
            "ai_processed_data": ai_processed_data,
        }

        with open("extracted_data.json", "w", encoding="utf-8") as json_file:
            json.dump(output_data, json_file, indent=4)

        print("Data successfully extracted and saved in 'extracted_data.json'!")

if __name__ == "__main__":
    main()
