# Unlisted Youtube Video Demo Link: https://www.youtube.com/watch?v=5iuL4-4eL7A

# JigsawStackDevRelTask

This project demonstrates the use of JigsawStack's API for various tasks such as uploading images, parsing invoices using OCR, and generating memes based on extracted invoice data.

## Features

- **Image Upload**: Upload an image to JigsawStack's file storage.
- **Invoice Parsing**: Extract key information (e.g., total amount, vendor, and date) from an invoice image using JigsawStack's OCR (vOCR) API.
- **Meme Generation**: Automatically generate memes based on the parsed invoice data (e.g., a meme for expensive invoices, or a "Friday" deployment joke).

## How It Works

1. **Image Upload**: The script uploads an invoice image to JigsawStack's storage.
2. **OCR Parsing**: The image is processed by the vOCR API to extract relevant information.
3. **Meme Generation**: Based on the extracted data, a meme is generated using predefined templates.

## Usage

1. **Initialize JigsawStack API Client**: 
   - Update your API keys in the script to connect to JigsawStack's services.

2. **Run the Script**:
   - The script processes an invoice image and generates a meme based on the invoice data.
   - Example images used in the script are `DevOps_invoice.jpg` and `git_invoice.jpg`.

3. **Output**:
   - The script saves the generated meme in the current directory.  
