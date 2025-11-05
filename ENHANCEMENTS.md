# Advanced Features & Enhancements 🚀

This document describes all the advanced features added to the Invoice & Receipt Processor system.

## Table of Contents

1. [Machine Learning Enhancement](#1-machine-learning-enhancement)
2. [Multi-Currency Support](#2-multi-currency-support)
3. [Duplicate Detection](#3-duplicate-detection)
4. [Budget Tracking & Alerts](#4-budget-tracking--alerts)
5. [Tax Reporting](#5-tax-reporting)
6. [Email Auto-Processing](#6-email-auto-processing)
7. [Multi-Language OCR](#7-multi-language-ocr)
8. [Mobile Receipt Scanner](#8-mobile-receipt-scanner)

---

## 1. Machine Learning Enhancement 🧠

### Overview
The system now learns from your corrections to improve extraction accuracy over time.

### Features

- **Learning from Corrections**: When you correct extracted data, the system remembers the patterns
- **Pattern Recognition**: Identifies vendor-specific formats and layouts
- **Confidence Boosting**: Extraction confidence improves as the system learns
- **Automatic Retraining**: Model retrains every 10 corrections

### How It Works

1. System extracts data from invoice
2. You review and correct any errors
3. ML module learns the differences
4. Future extractions are more accurate

### API Endpoints

```
GET  /api/ml/stats           - Get ML training statistics
POST /api/ml/retrain         - Manually trigger retraining
```

### Usage Example

The ML enhancement works automatically. No configuration needed!

After processing 10-20 invoices from the same vendor, you'll notice:
- Higher confidence scores
- Fewer corrections needed
- Better vendor name recognition

---

## 2. Multi-Currency Support 💱

### Overview
Process invoices in multiple currencies with automatic detection and conversion.

### Supported Currencies

- 🇺🇸 USD - US Dollar
- 🇪🇺 EUR - Euro
- 🇬🇧 GBP - British Pound
- 🇯🇵 JPY - Japanese Yen
- 🇨🇦 CAD - Canadian Dollar
- 🇦🇺 AUD - Australian Dollar
- 🇨🇭 CHF - Swiss Franc
- 🇨🇳 CNY - Chinese Yuan
- 🇮🇳 INR - Indian Rupee
- 🇲🇽 MXN - Mexican Peso

### Features

- **Automatic Currency Detection**: Recognizes currency symbols and codes
- **Real-time Conversion**: Converts to base currency (USD by default)
- **Exchange Rate Management**: Uses current exchange rates
- **Original Amount Preservation**: Keeps both original and converted amounts

### API Endpoints

```
GET  /api/currency/supported - List supported currencies
POST /api/currency/convert   - Convert between currencies
GET  /api/currency/rates     - Get exchange rates
```

### Usage Example

```javascript
// Convert EUR to USD
POST /api/currency/convert
{
  "amount": 100,
  "from": "EUR",
  "to": "USD"
}

// Response
{
  "success": true,
  "original_amount": 100,
  "converted_amount": 110,
  "from_currency": "EUR",
  "to_currency": "USD"
}
```

### Configuration

Set your base currency in the currency manager:
- Default: USD
- All expenses stored in base currency
- Original currency preserved in expense record

---

## 3. Duplicate Detection 🔍

### Overview
Automatically detects and prevents processing of duplicate documents.

### Detection Methods

1. **Exact Duplicate**: Same file uploaded twice (file hash)
2. **Visual Similarity**: Similar-looking documents (perceptual hash)
3. **Metadata Match**: Same vendor, amount, date, and invoice number

### Features

- **Real-time Detection**: Checks during upload
- **Confidence Scoring**: Shows likelihood of duplicate (85%+ threshold)
- **Similar Expense Search**: Find related transactions
- **Duplicate Management**: Mark/unmark duplicates

### API Endpoints

```
GET  /api/duplicates                    - Get all duplicates
POST /api/duplicates/mark               - Mark as duplicate
GET  /api/duplicates/similar/:id        - Find similar expenses
```

### How It Works

**During Upload:**
1. Calculate file hash
2. Calculate image hash (if image)
3. Extract metadata (vendor, amount, date)
4. Compare with existing expenses
5. Alert if potential duplicate found

**Similarity Factors:**
- Same invoice number: +50 points
- Same vendor: +20 points
- Same amount: +20 points
- Same date: +15 points
- Threshold: 85 points

### Usage Tips

- Review potential duplicates before processing
- System shows confidence score
- Can manually mark/unmark duplicates
- Useful for expense reimbursement tracking

---

## 4. Budget Tracking & Alerts 💰

### Overview
Set budgets by category, vendor, or time period and receive alerts when approaching limits.

### Features

#### Budget Types
- **Category Budgets**: Track spending per expense category
- **Vendor Budgets**: Limit spending with specific vendors
- **Period Budgets**: Monthly, quarterly, yearly, or custom periods

#### Alert Thresholds
- 50% - Good progress
- 75% - Warning
- 90% - Critical
- 100% - Exceeded

#### Forecasting
- Predict total spending based on current rate
- Recommended daily spending to stay on budget
- Days remaining in period

### API Endpoints

```
GET    /api/budgets                    - Get all budgets
POST   /api/budgets                    - Create budget
PUT    /api/budgets/:id                - Update budget
DELETE /api/budgets/:id                - Delete budget
GET    /api/budgets/status/:id         - Get budget status
GET    /api/budgets/summary            - Get budget summary
POST   /api/budgets/check              - Check all budgets
GET    /api/budgets/forecast/:id       - Get spending forecast
GET    /api/alerts                     - Get budget alerts
POST   /api/alerts/:id/read            - Mark alert as read
POST   /api/alerts/:id/dismiss         - Dismiss alert
```

### Creating a Budget

```javascript
POST /api/budgets
{
  "name": "Office Supplies Budget",
  "amount": 500.00,
  "period": "monthly",
  "category": "Office Supplies",
  "start_date": "2024-01-01",
  "alert_thresholds": [75, 90, 100]
}
```

### Budget Status Example

```json
{
  "budget_id": "BDG20241105120000",
  "budget_name": "Office Supplies Budget",
  "budget_amount": 500.00,
  "spent": 375.50,
  "remaining": 124.50,
  "percentage": 75.1,
  "status": "warning",
  "period_start": "2024-11-01",
  "period_end": "2024-11-30",
  "expense_count": 15
}
```

### Spending Forecast

The system predicts if you'll exceed your budget:

```json
{
  "budget_id": "BDG20241105120000",
  "current_spent": 375.50,
  "budget_amount": 500.00,
  "days_elapsed": 15,
  "days_remaining": 15,
  "daily_average": 25.03,
  "forecasted_total": 751.00,
  "will_exceed": true,
  "forecasted_overage": 251.00,
  "recommended_daily_spending": 8.30,
  "status": "over_budget"
}
```

---

## 5. Tax Reporting 📊

### Overview
Generate IRS-compliant tax reports for business expense deductions.

### Features

#### IRS Category Mapping
- Maps expense categories to IRS Schedule C lines
- Includes deduction percentages (e.g., meals at 50%)
- Provides form and line number references

#### Report Types
1. **Tax Summary**: Annual overview with deductible amounts
2. **Schedule C Report**: Formatted for Schedule C filing
3. **Quarterly Estimates**: Q1-Q4 breakdowns
4. **Detailed Export**: CSV with all transactions

#### Tax Categories (IRS-Compliant)

| Category | Form | Line | Deduction % |
|----------|------|------|-------------|
| Office Supplies | Schedule C | 22 | 100% |
| Software & Services | Schedule C | 18/27 | 100% |
| Travel | Schedule C | 24 | 100% |
| Meals & Entertainment | Schedule C | 24b | 50% |
| Utilities | Schedule C | 25 | 100% |
| Marketing | Schedule C | 8 | 100% |
| Equipment | Schedule C/Form 4562 | 13 | 100%* |
| Professional Services | Schedule C | 17 | 100% |
| Insurance | Schedule C | 15 | 100% |
| Rent & Lease | Schedule C | 20 | 100% |
| Shipping | Schedule C | 27 | 100% |
| Maintenance | Schedule C | 21 | 100% |
| Training | Schedule C | 27 | 100% |

*Equipment may require depreciation

### API Endpoints

```
GET  /api/tax/summary            - Get tax summary
GET  /api/tax/schedule-c         - Get Schedule C report
GET  /api/tax/quarterly          - Get quarterly estimate
POST /api/tax/export             - Export to CSV
GET  /api/tax/recommendations    - Get deduction tips
GET  /api/tax/settings           - Get tax settings
POST /api/tax/settings           - Update tax settings
GET  /api/tax/stats              - Get tax statistics
```

### Tax Summary Example

```json
{
  "tax_year": 2024,
  "total_expenses": 15250.00,
  "total_deductible": 14375.50,
  "total_non_deductible": 874.50,
  "expense_count": 156,
  "categories": [
    {
      "category": "Software & Services",
      "total": 4500.00,
      "deductible_amount": 4500.00,
      "count": 45,
      "irs_category": "Software/Subscriptions",
      "form": "Schedule C",
      "line": "18 or 27",
      "percentage": 100
    }
  ]
}
```

### Tax Settings

Configure your tax profile:

```javascript
POST /api/tax/settings
{
  "tax_year": 2024,
  "entity_type": "sole_proprietorship",
  "mileage_rate": 0.655,
  "home_office_sqft": 150,
  "total_home_sqft": 1500
}
```

### Deduction Recommendations

System analyzes your expenses and suggests additional deductions:

- Home office deduction
- Mileage tracking
- Equipment depreciation (Section 179)
- Overlooked categories

---

## 6. Email Auto-Processing 📧

### Overview
Forward invoices to a dedicated email address for automatic processing.

### Features

- **IMAP Integration**: Monitors email inbox
- **Automatic Extraction**: Processes attachments automatically
- **Configurable Filters**: Subject and sender filters
- **Background Monitoring**: Checks email at regular intervals
- **Security**: Whitelist trusted senders

### Setup Instructions

1. **Enable Email Monitoring**
   ```javascript
   POST /api/email/settings
   {
     "enabled": true,
     "server": "imap.gmail.com",
     "port": 993,
     "email": "invoices@yourdomain.com",
     "password": "app_password",
     "check_interval": 300
   }
   ```

2. **Configure Filters**
   ```javascript
   {
     "subject_filters": ["invoice", "receipt", "bill"],
     "sender_whitelist": ["vendor@example.com"],
     "auto_process": true
   }
   ```

3. **Start Monitoring**
   ```javascript
   POST /api/email/start
   ```

### Email Forwarding

Simply forward invoices to your configured email address:

**To:** invoices@yourdomain.com
**Subject:** Invoice from Amazon
**Attach:** invoice.pdf

The system will:
1. Detect the email
2. Download attachments
3. Extract data with OCR
4. Categorize expense
5. File document
6. Send confirmation (optional)

### API Endpoints

```
GET  /api/email/settings         - Get email settings
POST /api/email/settings         - Update settings
POST /api/email/test             - Test connection
POST /api/email/start            - Start monitoring
POST /api/email/stop             - Stop monitoring
GET  /api/email/status           - Get status
GET  /api/email/instructions     - Get forwarding instructions
```

### Security Best Practices

1. **Use App Passwords**: Don't use your main email password
2. **Enable Sender Whitelist**: Only process from trusted senders
3. **SSL/TLS Required**: Always use encrypted connections
4. **Regular Monitoring**: Check processed emails periodically

### Gmail Setup Example

1. Enable IMAP in Gmail settings
2. Generate App Password (Google Account → Security → 2-Step Verification → App passwords)
3. Use App Password in configuration
4. Set up email forwarding rule

---

## 7. Multi-Language OCR 🌍

### Overview
Process invoices in multiple languages with automatic language detection.

### Supported Languages

- 🇬🇧 English
- 🇪🇸 Spanish
- 🇫🇷 French
- 🇩🇪 German
- 🇮🇹 Italian
- 🇵🇹 Portuguese
- 🇳🇱 Dutch
- 🇷🇺 Russian
- 🇯🇵 Japanese
- 🇨🇳 Chinese (Simplified & Traditional)
- 🇰🇷 Korean
- 🇸🇦 Arabic
- 🇮🇳 Hindi
- 🇵🇱 Polish
- 🇺🇦 Ukrainian
- 🇻🇳 Vietnamese
- 🇹🇭 Thai

### Features

#### Automatic Language Detection
- Detects script type (Latin, Cyrillic, Arabic, etc.)
- Selects appropriate OCR language
- Works with mixed-language documents

#### Multi-Language Mode
- Process documents with multiple languages
- Useful for international companies
- Combines languages for better accuracy

#### OCR Engine Configuration
- **Engine Mode**: Legacy, LSTM, or Combined
- **Page Segmentation**: 13 different modes
- **Confidence Tuning**: Adjust for accuracy vs speed

### API Endpoints

```
GET  /api/ocr/languages          - List available languages
GET  /api/ocr/settings           - Get OCR settings
POST /api/ocr/settings           - Update settings
POST /api/ocr/detect             - Detect language
POST /api/ocr/benchmark          - Test languages
```

### Configuration

```javascript
POST /api/ocr/settings
{
  "default_language": "eng",
  "auto_detect_language": true,
  "multi_language_mode": false,
  "languages": ["eng", "spa", "fra"],
  "ocr_engine_mode": "3",
  "page_segmentation_mode": "3"
}
```

### Engine Modes

- **0**: Legacy engine only
- **1**: Neural nets LSTM engine only
- **2**: Legacy + LSTM engines
- **3**: Default (recommended)

### Page Segmentation Modes

- **3**: Fully automatic (recommended for invoices)
- **6**: Single uniform block of text
- **11**: Sparse text (find as much as possible)

### Installing Additional Languages

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr-spa  # Spanish
sudo apt-get install tesseract-ocr-fra  # French
```

**macOS:**
```bash
brew install tesseract-lang
```

**Windows:**
Download language data from Tesseract GitHub

---

## 8. Mobile Receipt Scanner 📱

### Overview
Mobile-optimized interface for scanning receipts on-the-go using your phone's camera.

### Features

#### Camera Integration
- Direct camera access
- Real-time preview
- Capture from camera or gallery
- Front/back camera switching

#### Mobile-Optimized UI
- Touch-friendly controls
- Large capture button
- Swipe gestures
- Responsive design

#### Quick Capture
- Position guide overlay
- Flash support
- Instant feedback
- Photo preview

### Access

Navigate to: `http://your-server:5000/mobile-scanner.html`

Or bookmark on your phone's home screen for app-like experience.

### How to Use

1. **Open Mobile Scanner** on your phone
2. **Grant Camera Permission** when prompted
3. **Position Receipt** within the frame
4. **Tap Capture Button** to take photo
5. **Review Photo** and ensure clarity
6. **Process Receipt** to extract data
7. **Review & Save** in main interface

### Tips for Best Results

✅ **Good Lighting**: Use natural light or bright indoor lighting
✅ **Flat Surface**: Lay receipt flat on table
✅ **All Corners**: Capture entire receipt including corners
✅ **Avoid Glare**: Position to avoid reflections
✅ **High Resolution**: Use highest quality camera setting

❌ **Avoid Shadows**: Don't block light source
❌ **No Wrinkles**: Smooth out creases
❌ **No Blur**: Hold phone steady

### PWA Installation

Add to home screen for offline access:

**iOS:**
1. Tap Share button
2. Tap "Add to Home Screen"
3. Name it "Receipt Scanner"

**Android:**
1. Tap menu (⋮)
2. Tap "Add to Home screen"
3. Confirm

### Supported Browsers

- ✅ Chrome (Android/iOS)
- ✅ Safari (iOS)
- ✅ Firefox (Android)
- ✅ Edge (Android/iOS)

---

## Integration Examples

### Complete Workflow with All Features

```javascript
// 1. Upload from mobile scanner
// (User captures photo with mobile scanner)

// 2. ML-enhanced extraction with multi-language support
POST /api/extract/:file_id
// Returns extracted data with ML enhancements

// 3. Check for duplicates
// Automatic during extraction

// 4. Multi-currency conversion
POST /api/currency/convert
{
  "amount": 100,
  "from": "EUR",
  "to": "USD"
}

// 5. Process with ML correction learning
POST /api/process
{
  "file_id": "...",
  "expense_data": {...},
  "original_extraction": {...}
}

// 6. Check budget impact
GET /api/budgets/summary
// Automatic alerts if threshold crossed

// 7. Generate tax report
GET /api/tax/summary?year=2024
```

### Email + Budget + Tax Workflow

1. Vendor emails invoice → Auto-processed
2. System checks budget → Alert if over threshold
3. Expense categorized → Tax category assigned
4. End of quarter → Generate tax estimate
5. End of year → Export Schedule C report

---

## Performance & Scalability

### Optimization Tips

1. **ML Training**: Retrains every 10 corrections, caches patterns
2. **Currency Rates**: Cached for 24 hours
3. **Duplicate Detection**: Uses efficient hashing algorithms
4. **Budget Checks**: Only run when expenses added
5. **OCR**: Image preprocessing for faster extraction

### Resource Usage

- **Storage**: ~1MB per document (varies)
- **Processing**: ~2-5 seconds per invoice
- **Memory**: ~50MB base + 10MB per concurrent process
- **Database**: JSON files (upgradeable to SQL)

### Scaling Recommendations

- **Small Business** (<100 invoices/month): Current setup
- **Medium Business** (100-1000/month): Upgrade to PostgreSQL
- **Large Business** (1000+/month): Add queue system (Celery/Redis)

---

## Security & Privacy

### Data Protection

- All data stored locally (no cloud dependency)
- Passwords encrypted
- HTTPS recommended for production
- Email credentials use app passwords

### Best Practices

1. Enable HTTPS
2. Use strong passwords
3. Regular backups
4. Limit email sender whitelist
5. Review processed documents periodically

---

## Troubleshooting

### ML Not Learning
- Ensure corrections are being submitted
- Check ML stats endpoint
- Manual retrain if needed

### Currency Conversion Issues
- Verify exchange rates are current
- Check currency code spelling
- Update rates manually if needed

### Duplicate False Positives
- Adjust similarity threshold
- Review duplicate criteria
- Manually unmark if needed

### Budget Alerts Not Working
- Verify budget is enabled
- Check alert thresholds
- Ensure expenses in correct category

### Tax Report Discrepancies
- Verify expense categories correct
- Check date ranges
- Review deduction percentages

### Email Processing Not Working
- Test IMAP connection
- Check credentials
- Verify subject filters
- Review sender whitelist

### OCR Language Issues
- Check language is installed
- Test language detection
- Adjust segmentation mode

### Mobile Scanner Issues
- Grant camera permissions
- Use HTTPS for camera access
- Check browser compatibility
- Clear browser cache

---

## API Reference

Complete API documentation available at: `/api/docs` (when server is running)

All endpoints return JSON in this format:

```json
{
  "success": true,
  "data": {...},
  "error": null
}
```

Or on error:

```json
{
  "success": false,
  "error": "Error message",
  "trace": "Stack trace (debug mode only)"
}
```

---

## Future Roadmap

Planned enhancements:

- [ ] QuickBooks/Xero integration
- [ ] Advanced ML models (transformer-based)
- [ ] Blockchain receipts verification
- [ ] Voice commands
- [ ] Batch processing UI
- [ ] Cloud backup options
- [ ] Mobile native apps
- [ ] Collaborative features (teams)
- [ ] Custom workflows
- [ ] API webhooks

---

## Support & Contributing

**Issues**: Report bugs on GitHub Issues
**Documentation**: Full docs at `/docs`
**Community**: Join discussions
**Contributing**: Pull requests welcome!

**Built with ❤️ to make business expense management effortless!**
