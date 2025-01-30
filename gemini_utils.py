from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import os
import mimetypes
import json
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

async def generate_gemini_response(user_message):
    """Generates a response using the Gemini API."""
    model = genai.GenerativeModel(model_name="gemini-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
    try:
        response = model.generate_content(user_message)
        return response.text
    except Exception as e:
        print(f"Error in generate_gemini_response: {e}")
        return "Sorry, I encountered an error while processing your request."

async def analyze_image(image_path):
    """Analyzes an image using the Gemini API."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    try:
        image = Image.open(image_path)
        image_bytes = BytesIO()
        image.save(image_bytes, format='JPEG')
        image_parts = [
            {
                "mime_type": "image/jpeg",
                "data": image_bytes.getvalue()
            },
        ]
        prompt_parts = [
            "Look at the image and give me all details in very short format, as you are limited to 100 words",
            image_parts[0],
        ]
        response = model.generate_content(prompt_parts)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error in analyze_image: {e}")
        return "Sorry, I encountered an error while analyzing the image."

async def analyze_pdf(pdf_path):
    """Analyzes a PDF file using the Gemini API."""
    model = genai.GenerativeModel('gemini-pro-vision')
    mime_type = "application/pdf"
    try:
        with open(pdf_path, 'rb') as pdf_file:
          pdf_data = pdf_file.read()
        file_data = {
            "mime_type": mime_type,
            "data": pdf_data
        }
        prompt_parts = [
            "Look at the pdf and give me all details in very short format, as you are limited to 100 words",
            file_data,
        ]
        response = model.generate_content(prompt_parts)
        response.resolve()
        return response.text
    except Exception as e:
        print(f"Error in analyze_pdf: {e}")
        return "Sorry, I encountered an error while analyzing the PDF."