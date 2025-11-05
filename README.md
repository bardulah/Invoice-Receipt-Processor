# Invoice & Receipt Processor 📊

> **Your Digital Accountant Assistant** - Transform messy invoice documents into organized, categorized, and easily searchable records.

## 🎉 Enhanced Edition - Now with Advanced Features!

This system now includes **8 powerful enhancements**:

1. 🧠 **Machine Learning** - Learns from your corrections for better accuracy
2. 💱 **Multi-Currency Support** - Process invoices in 10+ currencies
3. 🔍 **Duplicate Detection** - Prevents processing the same invoice twice
4. 💰 **Budget Tracking** - Set budgets and receive alerts
5. 📊 **Tax Reporting** - IRS-compliant Schedule C reports
6. 📧 **Email Auto-Processing** - Forward invoices via email
7. 🌍 **Multi-Language OCR** - Support for 18+ languages
8. 📱 **Mobile Scanner** - Scan receipts with your phone camera

**➡️ See [ENHANCEMENTS.md](ENHANCEMENTS.md) for complete documentation**

## Overview

The Invoice & Receipt Processor is a comprehensive web application that automates the tedious task of managing financial documents. Upload invoices and receipts, and watch as the system extracts key information, intelligently categorizes expenses, organizes files, and generates insightful reports.

## Key Features

### 🎯 Core Functionality

- **Document Upload & Processing**
  - Drag-and-drop file upload
  - Support for PDF, PNG, JPG, JPEG, and other image formats
  - Batch processing capabilities

- **OCR-like Data Extraction**
  - Automatically extract vendor names
  - Detect transaction amounts
  - Parse dates in multiple formats
  - Capture invoice/receipt numbers
  - Extract item descriptions
  - Image preprocessing for better accuracy

- **Intelligent File Organization**
  - Automatic renaming in `Date-Vendor-Amount` format
  - Organized folder structure: `YYYY/MM-Month/Vendor/`
  - Example: `processed/2024/11-November/Amazon/2024-11-05-Amazon-4299.pdf`

- **Smart Categorization**
  - AI-powered category suggestions based on vendor history
  - Fuzzy matching for similar vendors
  - Keyword-based categorization
  - Learn from your categorization patterns
  - 13+ predefined expense categories

- **Expense Management**
  - View all expenses with detailed information
  - Advanced filtering by category, vendor, date range
  - Full-text search across vendors, descriptions, and notes
  - Add custom notes to any expense

- **Report Generation**
  - Summary reports with key metrics
  - Category-based breakdowns
  - Vendor spending analysis
  - Monthly expense trends
  - Export to CSV for external analysis

- **Dashboard Analytics**
  - Real-time statistics
  - Recent expenses overview
  - Top categories and vendors
  - Visual data presentation

## Design Philosophy

The application is designed to feel like a **personal accountant assistant** rather than a cold tax form:

- ✅ **Visual Processing Pipeline** - See your documents move through each step
- 🎨 **Warm, Professional Colors** - Inspire confidence and trust
- 📊 **Visual Confirmations** - Clear feedback at every step
- 💡 **Smart Suggestions** - Learn from your history to save time
- 🚀 **Intuitive Interface** - Minimal clicks, maximum productivity

## Project Structure

```
Invoice-Receipt-Processor/
├── backend/
│   ├── app.py                 # Flask server & API endpoints
│   ├── extractor.py           # OCR & data extraction engine
│   ├── file_manager.py        # File naming & organization
│   ├── categorizer.py         # Expense categorization & smart suggestions
│   └── report_generator.py   # Report generation & export
├── frontend/
│   ├── index.html            # Main application UI
│   ├── style.css             # Beautiful, professional styling
│   └── app.js                # Frontend logic & API integration
├── uploads/                  # Temporary upload storage
├── processed/                # Organized files by date/vendor
├── data/                     # Expense database (JSON)
├── requirements.txt          # Python dependencies
└── README.md                # This file
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR engine
- pip (Python package manager)

### 1. Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/Invoice-Receipt-Processor.git
cd Invoice-Receipt-Processor
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
cd backend
python app.py
```

The application will start on `http://localhost:5000`

## Usage Guide

### Processing Your First Document

1. **Upload**
   - Navigate to the Upload tab
   - Drag and drop your invoice/receipt, or click to browse
   - Supported formats: PDF, PNG, JPG, JPEG

2. **Watch the Pipeline**
   - The processing pipeline will activate, showing each step:
     - 📤 Upload - Receiving your document
     - 🔍 Extract - Reading data with OCR
     - ✏️ Review - Waiting for your verification
     - 🏷️ Categorize - Applying smart suggestions
     - ✅ Complete - Filed and organized!

3. **Review & Edit**
   - Verify the extracted information
   - Edit any incorrect data
   - See smart category suggestions based on the vendor
   - Add notes if needed

4. **Complete Processing**
   - Click "Process & File Document"
   - Document is automatically renamed and organized
   - Ready to view in your expenses!

### Managing Expenses

**Viewing Expenses:**
- Navigate to the Expenses tab
- See all your processed documents
- Each card shows vendor, amount, date, category, and description

**Filtering:**
- Use the search box for full-text search
- Filter by category or vendor
- Set date ranges for specific periods
- Click "Clear Filters" to reset

### Generating Reports

1. Navigate to the Reports tab
2. Select report type:
   - **Summary** - Overview with key metrics
   - **By Category** - Expenses grouped by category
   - **By Vendor** - Spending per vendor
   - **Monthly** - Month-by-month breakdown
3. Set optional date filters
4. Click "Generate Report"
5. Export to CSV for external analysis

### Dashboard

The Dashboard provides at-a-glance insights:
- Total expenses and amounts
- Number of categories and vendors
- Recent expense activity
- Top spending categories

## API Documentation

### Endpoints

#### `POST /api/upload`
Upload a document for processing.

**Request:**
- Form data with file field

**Response:**
```json
{
  "success": true,
  "file_id": "20241105_123456_invoice.pdf",
  "original_name": "invoice.pdf"
}
```

#### `POST /api/extract/<file_id>`
Extract data from uploaded document.

**Response:**
```json
{
  "success": true,
  "data": {
    "vendor": "Amazon",
    "amount": 42.99,
    "date": "2024-11-05",
    "invoice_number": "INV-12345",
    "description": "Office supplies",
    "confidence": 85
  }
}
```

#### `POST /api/categorize`
Get category suggestions.

**Request:**
```json
{
  "vendor": "Amazon",
  "description": "Office supplies"
}
```

**Response:**
```json
{
  "success": true,
  "suggestions": [
    {
      "category": "Office Supplies",
      "confidence": 95,
      "reason": "Used 5 times for this vendor"
    }
  ]
}
```

#### `POST /api/process`
Complete document processing.

**Request:**
```json
{
  "file_id": "20241105_123456_invoice.pdf",
  "expense_data": {
    "vendor": "Amazon",
    "amount": 42.99,
    "date": "2024-11-05",
    "category": "Office Supplies",
    "description": "Office supplies",
    "notes": "Monthly supplies order"
  }
}
```

#### `GET /api/expenses`
Get expenses with optional filters.

**Query Parameters:**
- `category` - Filter by category
- `vendor` - Filter by vendor (partial match)
- `start_date` - Filter by start date (YYYY-MM-DD)
- `end_date` - Filter by end date (YYYY-MM-DD)
- `search` - Full-text search

#### `POST /api/report`
Generate expense report.

**Request:**
```json
{
  "type": "summary",
  "filters": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31"
  }
}
```

#### `POST /api/report/export`
Export report to CSV.

## Expense Categories

The system includes 13 predefined categories with smart keyword matching:

- **Office Supplies** - Stationery, desk items, supplies
- **Software & Services** - SaaS, subscriptions, cloud services
- **Travel** - Hotels, flights, transportation
- **Meals & Entertainment** - Restaurants, coffee, catering
- **Utilities** - Electric, gas, water, internet
- **Marketing** - Advertising, promotions, social media
- **Equipment** - Computers, hardware, machinery
- **Professional Services** - Consulting, legal, accounting
- **Insurance** - All insurance policies
- **Rent & Lease** - Property rent and leases
- **Shipping** - FedEx, UPS, USPS, postage
- **Maintenance** - Repairs, cleaning, services
- **Training** - Courses, education, conferences
- **Miscellaneous** - Everything else

## Customization

### Adding Custom Categories

Edit `backend/categorizer.py` and add to the `CATEGORIES` dictionary:

```python
CATEGORIES = {
    'Your Category': ['keyword1', 'keyword2', 'keyword3'],
    # ... other categories
}
```

### Adjusting OCR Settings

Modify preprocessing in `backend/extractor.py`:

```python
def preprocess_image(self, image):
    # Adjust thresholding parameters
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2  # Modify these values
    )
```

### Customizing File Organization

Edit the folder structure in `backend/file_manager.py`:

```python
def organize_file(self, source_path, expense_data, new_filename):
    # Modify folder structure here
    year = date_obj.strftime('%Y')
    month = date_obj.strftime('%m-%B')
    vendor = self.sanitize_filename(expense_data.get('vendor', 'Unknown'))
```

## Troubleshooting

### OCR Not Working

**Problem:** Extraction confidence is very low or no text detected.

**Solutions:**
- Ensure Tesseract is properly installed
- Check image quality (resolution, clarity)
- Try preprocessing the image externally
- Verify Tesseract is in system PATH

### Files Not Organizing

**Problem:** Files stay in uploads folder.

**Solutions:**
- Check folder permissions
- Verify `processed` folder exists
- Check error logs in console

### Category Suggestions Not Appearing

**Problem:** No smart suggestions showing up.

**Solutions:**
- Process a few expenses first to build history
- Check vendor name spelling consistency
- Verify categorizer is loading expense history

## Performance Tips

1. **Optimize Images Before Upload**
   - Use clear, high-resolution scans
   - Ensure text is readable
   - Avoid skewed or rotated images

2. **Batch Processing**
   - Process similar documents together
   - Use consistent categorization
   - Build vendor history for better suggestions

3. **Regular Maintenance**
   - Periodically export data
   - Clean up old temporary files
   - Review and correct miscategorized items

## Technology Stack

- **Backend:** Python 3.8+, Flask
- **OCR:** Tesseract, OpenCV, Pillow
- **Data Processing:** NumPy, pytesseract, pdf2image
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3
- **Data Storage:** JSON (upgradeable to SQLite/PostgreSQL)

## Future Enhancements

- [ ] Machine learning for better extraction
- [ ] Receipt scanning from mobile devices
- [ ] Multi-currency support
- [ ] Integration with accounting software (QuickBooks, Xero)
- [ ] Email forwarding for automatic processing
- [ ] OCR language selection
- [ ] Duplicate detection
- [ ] Budget tracking and alerts
- [ ] Tax reporting features
- [ ] Multi-user support with authentication

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review the troubleshooting section

---

**Built with ❤️ to make expense management effortless!**
