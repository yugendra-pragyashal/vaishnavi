# import os
# from pdf2image import convert_from_path
# from PIL import Image
# import pytesseract
# import pandas as pd
# import re
# from flask import Flask

# # Function to process images
# def process_image(file_path):
#     try:
#         image = Image.open(file_path)
#         text = pytesseract.image_to_string(image)
#         return text
#     except Exception as e:
#         print(f"Error processing image {file_path}: {e}")
#         return ""

# # Function to process PDFs
# def process_pdf(file_path):
#     try:
#         pages = convert_from_path(file_path, dpi=300)
#         text = ""
#         for page in pages:
#             text += pytesseract.image_to_string(page)
#         return text
#     except Exception as e:
#         print(f"Error processing PDF {file_path}: {e}")
#         return ""

# # Function to parse text into structured data
# def parse_text(text):
#     parsed_data = []
#     for line in text.split("\n"):
#         # Example regex to capture items and prices
#         match = re.match(r"(.+?)\s+([\d|]+(?:\.\d{1,2})?)$", line)
#         if match:
#             item = match.group(1).strip()
#             price = match.group(2).strip()
#             parsed_data.append({"Item": item, "Description": "", "Price": price})
#         else:
#             # Optional: Handle multi-line descriptions
#             pass
#     return parsed_data

# # Main pipeline function
# def data_extraction_pipeline(input_folder, output_excel):
#     all_data = []

#     # Iterate over all files in the folder
#     for root, _, files in os.walk(input_folder):
#         for file in files:
#             file_path = os.path.join(root, file)
#             if file.lower().endswith((".jpg", ".jpeg", ".png")):
#                 print(f"Processing image: {file_path}")
#                 text = process_image(file_path)
#             elif file.lower().endswith(".pdf"):
#                 print(f"Processing PDF: {file_path}")
#                 text = process_pdf(file_path)
#             else:
#                 print(f"Unsupported file type: {file_path}")
#                 continue

#             # Parse text to extract structured data
#             parsed_data = parse_text(text)
#             for data in parsed_data:
#                 data["Source File"] = file  # Add source file info
#             all_data.extend(parsed_data)

#     # Convert data to DataFrame
#     df = pd.DataFrame(all_data)

#     # Save to Excel
#     df.to_excel(output_excel, index=False)
#     print(f"Data extraction complete. Output saved to {output_excel}")

# # Define input folder and output file
# input_folder = "/content/drive/MyDrive/Menu-zip_1"  # path to your folder
# output_excel = "extracted_menu_data.xlsx"

# # Run the pipeline
# data_extraction_pipeline(input_folder, output_excel)



import os
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import zipfile
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import pandas as pd
import re
import tempfile

app = Flask(__name__)

# Function to process images
def process_image(file_path):
    try:
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error processing image {file_path}: {e}")
        return ""

# Function to process PDFs
def process_pdf(file_path):
    try:
        pages = convert_from_path(file_path, dpi=300)
        text = ""
        for page in pages:
            text += pytesseract.image_to_string(page)
        return text
    except Exception as e:
        print(f"Error processing PDF {file_path}: {e}")
        return ""

# Function to parse text into structured data
def parse_text(text):
    parsed_data = []
    for line in text.split("\n"):
        # Example regex to capture items and prices
        match = re.match(r"(.+?)\s+([\d|]+(?:\.\d{1,2})?)$", line)
        if match:
            item = match.group(1).strip()
            price = match.group(2).strip()
            parsed_data.append({"Item": item, "Description": "", "Price": price})
    return parsed_data

# Main pipeline function
def data_extraction_pipeline(input_folder, output_excel):
    all_data = []

    # Iterate over all files in the folder
    for root, _, files in os.walk(input_folder):
        for file in files:
            file_path = os.path.join(root, file)
            if file.lower().endswith((".jpg", ".jpeg", ".png")):
                print(f"Processing image: {file_path}")
                text = process_image(file_path)
            elif file.lower().endswith(".pdf"):
                print(f"Processing PDF: {file_path}")
                text = process_pdf(file_path)
            else:
                print(f"Unsupported file type: {file_path}")
                continue

            # Parse text to extract structured data
            parsed_data = parse_text(text)
            for data in parsed_data:
                data["Source File"] = file  # Add source file info
            all_data.extend(parsed_data)

    # Convert data to DataFrame
    df = pd.DataFrame(all_data)

    # Save to Excel
    df.to_excel(output_excel, index=False)
    print(f"Data extraction complete. Output saved to {output_excel}")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]
        if file.filename == "":
            return "No selected file"

        if file:
            filename = secure_filename(file.filename)
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, filename)
                file.save(zip_path)

                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                output_excel = os.path.join(temp_dir, "extracted_menu_data.xlsx")
                data_extraction_pipeline(temp_dir, output_excel)

                return send_file(output_excel, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)