from datetime import datetime
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import mimetypes
from PIL import Image
import pathlib
import textwrap
from io import BytesIO
from IPython.display import display
from IPython.display import Markdown

load_dotenv()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
# Set up the model
generation_config = {
  "temperature": 0.9,
  "top_p": 1,
  "top_k": 1,
  "max_output_tokens": 2048,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
]

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

def search_google(query):
    """Searches Google for the given query and returns a list of results."""
    base_url = "https://www.google.com/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    }
    params = {"q": query}
    try:
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    except requests.exceptions.RequestException as e:
        print(f"Error during web search: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    search_results = []

    # Find all search result containers
    for result in soup.find_all("div", class_="tF2Cxc"):
        # Extract title, link, and snippet
        title_element = result.find("h3", class_="LC20lb DKV0Md")
        link_element = result.find("a")
        snippet_element = result.find("span", class_="aCOpRe")

        title = title_element.text if title_element else ""
        link = link_element["href"] if link_element else ""
        snippet = snippet_element.text if snippet_element else ""

        search_results.append({"title": title, "link": link, "snippet": snippet})

    return search_results

def summarize_with_gemini(results):
    """Summarizes the search results using the Gemini API."""
    if not results:
        return "No search results to summarize."

    # Concatenate the search results into a single string
    search_results_text = ""
    for result in results:
        search_results_text += f"Title: {result['title']}\n"
        search_results_text += f"Snippet: {result['snippet']}\n\n"

    # Use Gemini to summarize the concatenated text
    model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
    prompt = f"""
Summarize the following search results, including the main points and key takeaways.
Also, provide a list of the top 5 relevant web links from the results.
Search Results:
{search_results_text}
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in summarize_with_gemini: {e}")
        return "Sorry, I couldn't summarize the search results."

def perform_web_search(query):
    """Performs a web search and returns a summarized result."""
    search_results = search_google(query)
    summary = summarize_with_gemini(search_results)

    # Find and format the top 5 links from the original search results
    top_links = "\n".join([f"{i+1}. {result['link']}" for i, result in enumerate(search_results[:5])])
    if top_links:
      summary += f"\n\n**Top 5 Web Links:**\n{top_links}"

    return summary