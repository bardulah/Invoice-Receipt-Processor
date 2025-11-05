# Quick Start Guide 🚀

Get up and running with Invoice & Receipt Processor in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (need 3.8+)
python --version

# Check if Tesseract is installed
tesseract --version
```

## Installation Steps

### 1. Install Tesseract OCR (if not already installed)

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you encounter permission issues, use:
```bash
pip install --user -r requirements.txt
```

### 3. Start the Server

```bash
cd backend
python app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
* Running on http://127.0.0.1:5000
```

### 4. Open Your Browser

Navigate to: **http://localhost:5000**

## First Time Usage

### Step 1: Upload a Document
1. Click the **Upload** tab (should be active by default)
2. Drag and drop an invoice or receipt, or click "Browse Files"
3. Supported formats: PDF, PNG, JPG, JPEG

### Step 2: Watch the Magic
The system will automatically:
- Upload your document ✅
- Extract vendor, amount, date, and other details 🔍
- Present the information for your review ✏️

### Step 3: Review & Adjust
- Verify the extracted information
- Edit any incorrect fields
- Notice the smart category suggestions based on the vendor
- Add optional notes

### Step 4: Complete Processing
- Click **"Process & File Document"**
- Your document is automatically:
  - Renamed to `Date-Vendor-Amount` format
  - Filed into organized folders by date and vendor
  - Saved to the expense database

### Step 5: Explore Your Data
- **Expenses Tab**: View all processed documents
- **Reports Tab**: Generate expense reports
- **Dashboard**: See statistics and insights

## Testing the System

### Test with Sample Data

Create a simple test invoice image with this text:
```
Amazon.com
Invoice #: 12345
Date: November 5, 2024
Total: $42.99
```

Save it as a PNG or PDF and upload it!

### Expected Results

After processing, you should see:
- File renamed to: `2024-11-05-Amazon-4299.pdf`
- Organized into: `processed/2024/11-November/Amazon/`
- Category suggestion: "Office Supplies" or "Software & Services"

## Common Issues

### "Tesseract not found"
```bash
# Add Tesseract to PATH or install it
# On Ubuntu:
sudo apt-get install tesseract-ocr

# Verify:
tesseract --version
```

### "Port 5000 already in use"
Change the port in `backend/app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Dependencies Installation Fails
Try installing dependencies individually:
```bash
pip install Flask Flask-CORS Werkzeug Pillow pytesseract pdf2image python-dateutil opencv-python numpy fuzzywuzzy python-Levenshtein
```

## What's Next?

1. **Process More Documents**: Build up your expense history
2. **Explore Categories**: The system learns from your categorization
3. **Generate Reports**: See your spending patterns
4. **Customize**: Add your own categories and adjust settings

## Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Review the [Troubleshooting](README.md#troubleshooting) section
- Open an issue on GitHub

---

**You're all set! Start processing those invoices! 📊✨**
