import jigsawstack
from PIL import Image, ImageDraw, ImageFont
import os
import json
import re
from datetime import datetime
import textwrap

# Initialize the JigsawStack API client with the secret key
api_key = "sk_0216182a50416767e995590b3ed5550a49e6db13d5a048b65898e1746f484673ce47db3a84e7e086609366b69409f6476e097f97cdebddf5314ce8d4767a2d98024gq3iNJFLILBYHbrFKH"
public_key = "pk_7ed4797c1b081d58e62f4050d5fb38c836e6a9c3082fb405303611d1029bff3851d7326dc07fb867494d5143adaec57d8dc3ffde3450e831e73ad47f25cf46070247eEshiKMt3EIG8hbBt"
client = jigsawstack.JigsawStack(api_key)


def debug_print(message, obj):
    print(message)
    print(f"Type: {type(obj)}")
    print(f"Content: {obj}")
    print("-" * 50)


# Upload Image to JigsawStack's File Storage using the SDK
def upload_image_to_storage(image_path):
    try:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        filename = os.path.basename(image_path)
        result = client.store.upload(
            image_data,
            {
                "overwrite": True,
                "filename": filename,
            },
        )

        debug_print("Upload result:", result)

        if isinstance(result, dict) and "url" in result:
            public_url = f"{result['url']}?x-api-key={public_key}"
            return public_url
        else:
            debug_print("Unexpected upload result format:", result)
            return None
    except Exception as e:
        debug_print("Exception in upload_image_to_storage:", str(e))
        return None


# Invoice Parsing (OCR) using JigsawStack vOCR API with Public URL
def parse_invoice_with_url(image_url):
    try:
        response = client.vision.vocr(
            {
                "prompt": "Extract all text from this invoice image. Return a JSON structure with the extracted information and also include the raw extracted text.",
                "url": image_url,
            }
        )
        debug_print("Raw OCR response:", response)

        if isinstance(response, dict) and response.get("success", False):
            extracted_info = {
                "total_amount": extract_total_amount(response),
                "vendor": extract_vendor(response),
                "date": extract_date(response),
            }
            debug_print("Extracted invoice information:", extracted_info)
            return extracted_info
        else:
            debug_print("OCR parsing failed or unexpected response format:", response)
            return None
    except Exception as e:
        debug_print("Exception in parse_invoice_with_url:", str(e))
        return None


def extract_total_amount(ocr_response):
    try:
        content = json.loads(ocr_response["context"].strip("```json\n"))
        print(f"JSON content: {json.dumps(content, indent=2)}")

        # Check if 'invoice_details' exists and contains 'total_due'
        if "invoice_details" in content and "total_due" in content["invoice_details"]:
            total_due = content["invoice_details"]["total_due"]
            return float(total_due.replace("$", "").replace(",", ""))

        # If not found in the expected structure, search in the raw text
        raw_text = content.get("raw_text", "")
        print(f"Raw text: {raw_text}")
        match = re.search(
            r"TOTAL DUE\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", raw_text, re.IGNORECASE
        )
        if match:
            return float(match.group(1).replace(",", ""))

        print("No match found for total amount in JSON structure or raw text")
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        print(f"Error extracting total amount: {e}")
    return 0.0


def extract_vendor(ocr_response):
    try:
        content = json.loads(ocr_response["context"].strip("```json\n"))
        if (
            "invoice_details" in content
            and "company_name" in content["invoice_details"]
        ):
            return content["invoice_details"]["company_name"]

        # If not found in the expected structure, search in the raw text
        raw_text = content.get("raw_text", "")
        lines = raw_text.split("\n")
        if lines:
            return lines[0].strip()
    except (KeyError, json.JSONDecodeError) as e:
        print(f"Error extracting vendor: {e}")
    return "Unknown Vendor"


def extract_date(ocr_response):
    try:
        content = json.loads(ocr_response["context"].strip("```json\n"))
        if (
            "invoice_details" in content
            and "invoice_date" in content["invoice_details"]
        ):
            date_str = content["invoice_details"]["invoice_date"]
        else:
            # If not found in the expected structure, search in the raw text
            raw_text = content.get("raw_text", "")
            match = re.search(
                r"DATE:?\s*([A-Z]+DAY,\s+[A-Z]+\s+\d{1,2},\s+\d{4})",
                raw_text,
                re.IGNORECASE,
            )
            if match:
                date_str = match.group(1)
            else:
                return "Unknown Date"

        date_obj = datetime.strptime(date_str, "%A, %B %d, %Y")
        return f"{date_obj.strftime('%Y-%m-%d')} {date_obj.strftime('%A')}"
    except (KeyError, json.JSONDecodeError, ValueError) as e:
        print(f"Error extracting date: {e}")
    return "Unknown Date"


# Meme Generation Function with Text Wrapping
def generate_meme(template_path, top_text, bottom_text, output_path):
    try:
        image = Image.open(template_path)
        draw = ImageDraw.Draw(image)
        width, height = image.size

        # Adjust the font path for your system
        if os.name == "nt":  # Windows
            font_path = "C:/Windows/Fonts/Arial.ttf"
        elif os.name == "posix":  # macOS or Linux
            font_path = "/System/Library/Fonts/Helvetica.ttc"
            if not os.path.exists(font_path):  # If on Linux and font doesn't exist
                font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

        # Adjusted get_font_size function
        def get_font_size(text, font_path, image_width, max_font_size=100):
            try:
                for size in range(max_font_size, 1, -1):
                    font = ImageFont.truetype(font_path, size)
                    bbox = font.getbbox(text)
                    if (
                        bbox[2] < image_width * 0.9
                    ):  # Ensure text fits within 90% of image width
                        return font
                print(f"Warning: Could not find a suitable font size for text: {text}")
                return ImageFont.truetype(
                    font_path, 10
                )  # Default to a very small font size
            except OSError as e:
                return ImageFont.load_default()  # Fallback to the default font

        # Helper function to wrap text to fit within image width
        def draw_text_wrapped(draw, text, position, font, max_width):
            lines = textwrap.wrap(
                text, width=int(max_width / font.getbbox("A")[2])
            )  # Dynamically adjust wrapping width
            y_offset = position[1]
            for line in lines:
                line_width, line_height = font.getbbox(line)[
                    2:4
                ]  # Calculate text dimensions
                draw.text(
                    ((max_width - line_width) / 2, y_offset),
                    line,
                    font=font,
                    fill="white",
                    stroke_width=2,
                    stroke_fill="black",
                )
                y_offset += line_height

        # Get appropriate font sizes
        top_font = get_font_size(top_text, font_path, width)
        bottom_font = get_font_size(bottom_text, font_path, width)

        # Calculate text positions with padding
        top_padding = 30  # Padding at the top to prevent cutoff
        bottom_padding = 30  # Padding at the bottom to prevent cutoff
        top_text_position = (10, top_padding)
        bottom_text_position = (
            10,
            height - bottom_padding - bottom_font.getbbox(bottom_text)[3],
        )

        # Draw wrapped text
        draw_text_wrapped(draw, top_text, top_text_position, top_font, width)
        draw_text_wrapped(draw, bottom_text, bottom_text_position, bottom_font, width)

        image.save(output_path)
        print(f"Meme saved to {output_path}")
    except Exception as e:
        print(f"Error generating meme: {e}")
        import traceback

        traceback.print_exc()


# Trigger Meme Based on Invoice Data
def trigger_meme_based_on_invoice(invoice_data):
    total_amount = invoice_data.get("total_amount", 0)
    vendor = invoice_data.get("vendor", "Unknown Vendor")
    date = invoice_data.get("date", "Unknown Date")

    if "Friday" in date:
        generate_meme(
            "deploy_friday_template.jpg",
            f"Invoice from {vendor} on a Friday?",
            "Hope it's not for a deployment!",
            "output_friday_meme.jpg",
        )
    elif total_amount > 4000:
        generate_meme(
            "expensive_template.jpg",
            f"When {vendor}'s invoice arrives",
            f"${total_amount:.2f}?! That's a lot!",
            "output_expensive_meme.jpg",
        )
    elif total_amount < 1000:
        generate_meme(
            "cheap_template.jpg",
            f"When {vendor}'s invoice arrives",
            f"Only ${total_amount:.2f}? What a deal!",
            "output_cheap_meme.jpg",
        )
    else:
        generate_meme(
            "default_template.jpg",
            f"Invoice from {vendor}",
            f"${total_amount:.2f} for their services",
            "output_default_meme.jpg",
        )


# Main Function
def main(image_path):
    try:
        if not os.path.isfile(image_path):
            raise FileNotFoundError(f"No such file or directory: '{image_path}'")

        print(f"Processing image: {image_path}")
        image_url = upload_image_to_storage(image_path)
        if image_url is None:
            print(f"Failed to upload image: {image_path}")
            return

        print(f"Image uploaded successfully. URL: {image_url}")

        invoice_data = parse_invoice_with_url(image_url)
        if invoice_data is None:
            print(f"Failed to parse invoice from image: {image_path}")
            return

        trigger_meme_based_on_invoice(invoice_data)
        print("Meme generation process completed!")
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback

        traceback.print_exc()


# Example 
if __name__ == "__main__":
    main("DevOps_invoice.jpg")
    main("git_invoice.jpg")
