import os
import re
from datetime import datetime
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import cv2
import numpy as np

class DocumentExtractor:
    """Extract key information from invoice and receipt documents"""

    def __init__(self):
        # Common vendor patterns
        self.vendor_patterns = [
            r'(?:from|pay to|vendor|merchant|seller):\s*([A-Za-z0-9\s\-&.,]+)',
            r'^([A-Z][A-Za-z0-9\s\-&.,]{2,30})',  # Company name at top
        ]

        # Amount patterns
        self.amount_patterns = [
            r'(?:total|amount|sum|balance|due)[\s:$]*\$?\s*(\d+[,.]?\d*\.?\d{2})',
            r'\$\s*(\d+[,.]?\d*\.?\d{2})',
            r'(\d+[,.]?\d*\.?\d{2})\s*(?:USD|usd|\$)',
        ]

        # Date patterns
        self.date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})',
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
        ]

        # Invoice/receipt number patterns
        self.invoice_patterns = [
            r'(?:invoice|receipt|order|ref|reference|no|#)[\s#:]*([A-Z0-9\-]+)',
        ]

    def extract(self, filepath):
        """Extract data from document"""
        try:
            # Convert to image if PDF
            if filepath.lower().endswith('.pdf'):
                images = convert_from_path(filepath, first_page=1, last_page=1)
                image = images[0]
            else:
                image = Image.open(filepath)

            # Preprocess image for better OCR
            image = self.preprocess_image(image)

            # Perform OCR
            text = pytesseract.image_to_string(image)

            # Extract information
            extracted_data = {
                'vendor': self.extract_vendor(text),
                'amount': self.extract_amount(text),
                'date': self.extract_date(text),
                'invoice_number': self.extract_invoice_number(text),
                'description': self.extract_description(text),
                'raw_text': text,
                'confidence': self.calculate_confidence(text)
            }

            return extracted_data

        except Exception as e:
            raise Exception(f"Error extracting data: {str(e)}")

    def preprocess_image(self, image):
        """Preprocess image for better OCR accuracy"""
        # Convert PIL image to OpenCV format
        img_array = np.array(image)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Apply thresholding to get better text contrast
        # Use adaptive thresholding for varied lighting
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)

        # Convert back to PIL Image
        return Image.fromarray(denoised)

    def extract_vendor(self, text):
        """Extract vendor name from text"""
        lines = text.split('\n')

        # Try pattern matching first
        for pattern in self.vendor_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                vendor = match.group(1).strip()
                # Clean up vendor name
                vendor = re.sub(r'\s+', ' ', vendor)
                if len(vendor) > 2 and len(vendor) < 50:
                    return vendor

        # Fallback: use first non-empty line (often the company name)
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 2 and len(line) < 50:
                # Skip if it looks like a date or number
                if not re.match(r'^\d+[/-]\d+', line):
                    return line

        return 'Unknown Vendor'

    def extract_amount(self, text):
        """Extract total amount from text"""
        amounts = []

        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = float(amount_str)
                    if 0 < amount < 1000000:  # Reasonable range
                        amounts.append(amount)
                except ValueError:
                    continue

        # Return the largest amount (usually the total)
        if amounts:
            return max(amounts)

        return 0.0

    def extract_date(self, text):
        """Extract date from text"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Try to parse the date
                parsed_date = self.parse_date(date_str)
                if parsed_date:
                    return parsed_date

        # Default to today if no date found
        return datetime.now().strftime('%Y-%m-%d')

    def parse_date(self, date_str):
        """Parse various date formats"""
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y',
            '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y',
            '%B %d %Y', '%b %d %Y', '%d %B %Y', '%d %b %Y',
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    def extract_invoice_number(self, text):
        """Extract invoice or receipt number"""
        for pattern in self.invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_num = match.group(1).strip()
                if len(invoice_num) > 2 and len(invoice_num) < 30:
                    return invoice_num

        return ''

    def extract_description(self, text):
        """Extract a brief description from line items"""
        lines = text.split('\n')

        # Look for item descriptions (lines with both text and numbers)
        items = []
        for line in lines:
            line = line.strip()
            # Skip empty lines and lines that are just numbers
            if not line or line.isdigit():
                continue
            # Look for lines that might be items (have both text and price)
            if re.search(r'[A-Za-z]{3,}', line) and re.search(r'\d+\.?\d*', line):
                # Clean up the line
                clean_line = re.sub(r'\s+', ' ', line)
                if len(clean_line) > 5 and len(clean_line) < 100:
                    items.append(clean_line)

        # Return first few items or generic description
        if items:
            return '; '.join(items[:3])

        return 'Expense'

    def calculate_confidence(self, text):
        """Calculate confidence score based on extracted data quality"""
        score = 0

        # Check if we have reasonable amount of text
        if len(text) > 50:
            score += 30

        # Check for common invoice/receipt keywords
        keywords = ['total', 'amount', 'invoice', 'receipt', 'date', 'vendor', 'tax']
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in text.lower())
        score += min(keyword_count * 10, 40)

        # Check for numbers (amounts)
        if re.search(r'\d+\.?\d{2}', text):
            score += 15

        # Check for dates
        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', text):
            score += 15

        return min(score, 100)
