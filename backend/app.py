from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import traceback

# Import original modules
from extractor import DocumentExtractor
from file_manager import FileManager
from categorizer import ExpenseCategorizer
from report_generator import ReportGenerator

# Import new enhancement modules
from ml_extractor import MLExtractor
from currency_manager import CurrencyManager
from duplicate_detector import DuplicateDetector
from budget_manager import BudgetManager
from tax_reporter import TaxReporter

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
DATA_FOLDER = 'data'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif', 'bmp', 'tiff'}

# Ensure folders exist
for folder in [UPLOAD_FOLDER, PROCESSED_FOLDER, DATA_FOLDER]:
    os.makedirs(folder, exist_ok=True)

# Initialize original components
extractor = DocumentExtractor()
file_manager = FileManager(PROCESSED_FOLDER)
categorizer = ExpenseCategorizer(DATA_FOLDER)
report_generator = ReportGenerator(DATA_FOLDER)

# Initialize new enhancement components
ml_extractor = MLExtractor(DATA_FOLDER)
currency_manager = CurrencyManager(DATA_FOLDER)
duplicate_detector = DuplicateDetector(categorizer)
budget_manager = BudgetManager(DATA_FOLDER, categorizer)
tax_reporter = TaxReporter(DATA_FOLDER, categorizer)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# ===== ORIGINAL ENDPOINTS =====

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and initial validation"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        # Save file temporarily
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(filepath)

        return jsonify({
            'success': True,
            'file_id': unique_filename,
            'original_name': filename
        })
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/extract/<file_id>', methods=['POST'])
def extract_data(file_id):
    """Extract data from uploaded document with ML enhancements"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Extract data from document (original)
        extracted_data = extractor.extract(filepath)

        # Enhance with ML if available
        if len(ml_extractor.training_data) > 0:
            extracted_data = ml_extractor.enhance_extraction(extracted_data, extracted_data.get('raw_text', ''))

        # Detect and extract currency
        amount_with_currency = currency_manager.extract_amount_with_currency(extracted_data.get('raw_text', ''))
        if amount_with_currency[0] > 0:
            extracted_data['amount'] = amount_with_currency[0]
            extracted_data['currency'] = amount_with_currency[1]
            extracted_data['currency_confidence'] = amount_with_currency[2]
        else:
            extracted_data['currency'] = 'USD'
            extracted_data['currency_confidence'] = 50

        # Check for duplicates
        is_duplicate, duplicate_info, confidence = duplicate_detector.check_duplicate(filepath, extracted_data)
        extracted_data['is_potential_duplicate'] = is_duplicate
        if is_duplicate:
            extracted_data['duplicate_info'] = {
                'type': duplicate_info['type'],
                'confidence': confidence,
                'existing_expense': duplicate_info.get('expense', {}).get('id', 'Unknown')
            }

        # Calculate file hash for future duplicate detection
        file_hash = duplicate_detector.calculate_file_hash(filepath)
        extracted_data['file_hash'] = file_hash

        # Calculate image hash if possible
        image_hashes = duplicate_detector.calculate_image_hash(filepath)
        if image_hashes:
            extracted_data['image_hashes'] = image_hashes

        return jsonify({
            'success': True,
            'data': extracted_data
        })
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/categorize', methods=['POST'])
def categorize_expense():
    """Get category suggestions based on vendor and description"""
    try:
        data = request.json
        vendor = data.get('vendor', '')
        description = data.get('description', '')

        suggestions = categorizer.suggest_category(vendor, description)

        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_document():
    """Complete processing: rename, organize, and store expense data"""
    try:
        data = request.json
        file_id = data.get('file_id')
        expense_data = data.get('expense_data')
        original_extraction = data.get('original_extraction', {})

        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Learn from corrections if user modified extracted data
        if original_extraction:
            raw_text = original_extraction.get('raw_text', '')
            ml_extractor.add_correction(raw_text, original_extraction, expense_data)

        # Handle currency conversion to base currency
        currency = expense_data.get('currency', 'USD')
        amount = expense_data.get('amount', 0)

        if currency != 'USD':
            converted_amount = currency_manager.convert_to_base(amount, currency)
            expense_data['original_amount'] = amount
            expense_data['original_currency'] = currency
            expense_data['amount'] = converted_amount
            expense_data['converted_to_usd'] = True
        else:
            expense_data['currency'] = 'USD'

        # Generate new filename
        new_filename = file_manager.generate_filename(expense_data)

        # Organize file into folder structure
        final_path = file_manager.organize_file(filepath, expense_data, new_filename)

        # Store expense record
        expense_data['file_path'] = final_path
        expense_data['processed_date'] = datetime.now().isoformat()
        expense_id = categorizer.add_expense(expense_data)

        # Check budgets after adding expense
        budget_check = budget_manager.check_all_budgets()

        response = {
            'success': True,
            'expense_id': expense_id,
            'final_path': final_path,
            'filename': new_filename
        }

        # Include budget alerts if any were triggered
        if budget_check['new_alerts']:
            response['budget_alerts'] = budget_check['new_alerts']

        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses with optional filters"""
    try:
        category = request.args.get('category')
        vendor = request.args.get('vendor')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search')

        expenses = categorizer.get_expenses(
            category=category,
            vendor=vendor,
            start_date=start_date,
            end_date=end_date,
            search=search
        )

        return jsonify({
            'success': True,
            'expenses': expenses
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all available expense categories"""
    try:
        categories = categorizer.get_all_categories()
        return jsonify({
            'success': True,
            'categories': categories
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get all unique vendors"""
    try:
        vendors = categorizer.get_all_vendors()
        return jsonify({
            'success': True,
            'vendors': vendors
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate expense report"""
    try:
        data = request.json
        report_type = data.get('type', 'summary')
        filters = data.get('filters', {})

        report = report_generator.generate_report(report_type, filters)

        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report/export', methods=['POST'])
def export_report():
    """Export report to CSV"""
    try:
        data = request.json
        report_type = data.get('type', 'summary')
        filters = data.get('filters', {})

        csv_path = report_generator.export_to_csv(report_type, filters)

        return send_file(csv_path, as_attachment=True, download_name='expense_report.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get dashboard statistics"""
    try:
        stats = categorizer.get_statistics()

        # Add ML statistics
        stats['ml_stats'] = ml_extractor.get_statistics()

        # Add currency info
        stats['currency_info'] = currency_manager.get_exchange_rate_info()

        # Add duplicate stats
        stats['duplicate_stats'] = duplicate_detector.get_duplicate_statistics()

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== NEW ENHANCEMENT ENDPOINTS =====

# ML Extractor Endpoints
@app.route('/api/ml/stats', methods=['GET'])
def get_ml_stats():
    """Get ML training statistics"""
    try:
        stats = ml_extractor.get_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ml/retrain', methods=['POST'])
def retrain_ml_model():
    """Manually trigger ML model retraining"""
    try:
        ml_extractor.retrain()
        return jsonify({
            'success': True,
            'message': 'Model retrained successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Currency Endpoints
@app.route('/api/currency/supported', methods=['GET'])
def get_supported_currencies():
    """Get list of supported currencies"""
    try:
        currencies = currency_manager.get_supported_currencies()
        return jsonify({
            'success': True,
            'currencies': currencies
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/currency/convert', methods=['POST'])
def convert_currency():
    """Convert amount between currencies"""
    try:
        data = request.json
        amount = data.get('amount', 0)
        from_currency = data.get('from', 'USD')
        to_currency = data.get('to', 'USD')

        converted = currency_manager.convert_currency(amount, from_currency, to_currency)

        return jsonify({
            'success': True,
            'original_amount': amount,
            'converted_amount': converted,
            'from_currency': from_currency,
            'to_currency': to_currency
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/currency/rates', methods=['GET'])
def get_exchange_rates():
    """Get current exchange rates"""
    try:
        info = currency_manager.get_exchange_rate_info()
        return jsonify({
            'success': True,
            'rates_info': info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Duplicate Detection Endpoints
@app.route('/api/duplicates', methods=['GET'])
def get_duplicates():
    """Get all expenses marked as duplicates"""
    try:
        duplicates = duplicate_detector.get_duplicates()
        return jsonify({
            'success': True,
            'duplicates': duplicates
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/duplicates/mark', methods=['POST'])
def mark_duplicate():
    """Mark an expense as duplicate"""
    try:
        data = request.json
        expense_id = data.get('expense_id')
        original_id = data.get('original_id')

        duplicate_detector.mark_as_duplicate(expense_id, original_id)

        return jsonify({
            'success': True,
            'message': 'Expense marked as duplicate'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/duplicates/similar/<expense_id>', methods=['GET'])
def get_similar_expenses(expense_id):
    """Find expenses similar to the given expense"""
    try:
        # Find the expense
        expense = None
        for exp in categorizer.expenses:
            if exp.get('id') == expense_id:
                expense = exp
                break

        if not expense:
            return jsonify({'error': 'Expense not found'}), 404

        similar = duplicate_detector.find_similar_expenses(expense, limit=10)

        return jsonify({
            'success': True,
            'similar_expenses': similar
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Budget Endpoints
@app.route('/api/budgets', methods=['GET'])
def get_budgets():
    """Get all budgets"""
    try:
        budgets = budget_manager.get_all_budgets()
        return jsonify({
            'success': True,
            'budgets': budgets
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets', methods=['POST'])
def create_budget():
    """Create a new budget"""
    try:
        data = request.json
        budget_id = budget_manager.create_budget(data)

        return jsonify({
            'success': True,
            'budget_id': budget_id,
            'message': 'Budget created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/<budget_id>', methods=['PUT'])
def update_budget(budget_id):
    """Update a budget"""
    try:
        data = request.json
        success = budget_manager.update_budget(budget_id, data)

        if success:
            return jsonify({
                'success': True,
                'message': 'Budget updated successfully'
            })
        else:
            return jsonify({'error': 'Budget not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/<budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        budget_manager.delete_budget(budget_id)
        return jsonify({
            'success': True,
            'message': 'Budget deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/status/<budget_id>', methods=['GET'])
def get_budget_status(budget_id):
    """Get status of a specific budget"""
    try:
        status = budget_manager.get_budget_status(budget_id)

        if not status:
            return jsonify({'error': 'Budget not found'}), 404

        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/summary', methods=['GET'])
def get_budget_summary():
    """Get summary of all budgets"""
    try:
        summary = budget_manager.get_budget_summary()
        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/check', methods=['POST'])
def check_budgets():
    """Check all budgets and generate alerts"""
    try:
        result = budget_manager.check_all_budgets()
        return jsonify({
            'success': True,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/budgets/forecast/<budget_id>', methods=['GET'])
def get_budget_forecast(budget_id):
    """Get spending forecast for a budget"""
    try:
        forecast = budget_manager.get_spending_forecast(budget_id)

        if not forecast:
            return jsonify({'error': 'Budget not found or forecast unavailable'}), 404

        return jsonify({
            'success': True,
            'forecast': forecast
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get budget alerts"""
    try:
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        undismissed_only = request.args.get('undismissed_only', 'false').lower() == 'true'

        alerts = budget_manager.get_alerts(unread_only, undismissed_only)

        return jsonify({
            'success': True,
            'alerts': alerts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/read', methods=['POST'])
def mark_alert_read(alert_id):
    """Mark an alert as read"""
    try:
        success = budget_manager.mark_alert_read(alert_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Alert marked as read'
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts/<alert_id>/dismiss', methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    try:
        success = budget_manager.dismiss_alert(alert_id)

        if success:
            return jsonify({
                'success': True,
                'message': 'Alert dismissed'
            })
        else:
            return jsonify({'error': 'Alert not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tax Reporting Endpoints
@app.route('/api/tax/summary', methods=['GET'])
def get_tax_summary():
    """Get tax summary for a year"""
    try:
        tax_year = request.args.get('year', type=int)
        summary = tax_reporter.generate_tax_summary(tax_year)

        return jsonify({
            'success': True,
            'summary': summary
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/schedule-c', methods=['GET'])
def get_schedule_c():
    """Get Schedule C report"""
    try:
        tax_year = request.args.get('year', type=int)
        report = tax_reporter.generate_schedule_c_report(tax_year)

        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/quarterly', methods=['GET'])
def get_quarterly_estimate():
    """Get quarterly tax estimate"""
    try:
        quarter = request.args.get('quarter', type=int)
        tax_year = request.args.get('year', type=int)

        if not quarter or quarter < 1 or quarter > 4:
            return jsonify({'error': 'Invalid quarter (must be 1-4)'}), 400

        estimate = tax_reporter.generate_quarterly_estimate(quarter, tax_year)

        return jsonify({
            'success': True,
            'estimate': estimate
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/export', methods=['POST'])
def export_tax_report():
    """Export tax report to CSV"""
    try:
        data = request.json
        tax_year = data.get('year')

        csv_path = tax_reporter.export_tax_report_csv(tax_year)

        return send_file(csv_path, as_attachment=True, download_name=f'tax_report_{tax_year}.csv')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/recommendations', methods=['GET'])
def get_tax_recommendations():
    """Get deduction recommendations"""
    try:
        recommendations = tax_reporter.get_deduction_recommendations()

        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/settings', methods=['GET'])
def get_tax_settings():
    """Get tax settings"""
    try:
        settings = tax_reporter.tax_settings
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/settings', methods=['POST'])
def update_tax_settings():
    """Update tax settings"""
    try:
        data = request.json
        tax_reporter.update_tax_settings(data)

        return jsonify({
            'success': True,
            'message': 'Tax settings updated successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tax/stats', methods=['GET'])
def get_tax_stats():
    """Get tax statistics"""
    try:
        stats = tax_reporter.get_tax_statistics()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("Invoice & Receipt Processor - Enhanced Edition")
    print("=" * 60)
    print("✅ Machine Learning - Active")
    print("✅ Multi-Currency Support - Active")
    print("✅ Duplicate Detection - Active")
    print("✅ Budget Tracking - Active")
    print("✅ Tax Reporting - Active")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
