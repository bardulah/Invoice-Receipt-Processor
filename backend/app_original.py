from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
import traceback

from extractor import DocumentExtractor
from file_manager import FileManager
from categorizer import ExpenseCategorizer
from report_generator import ReportGenerator

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

# Initialize components
extractor = DocumentExtractor()
file_manager = FileManager(PROCESSED_FOLDER)
categorizer = ExpenseCategorizer(DATA_FOLDER)
report_generator = ReportGenerator(DATA_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

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
    """Extract data from uploaded document"""
    try:
        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Extract data from document
        extracted_data = extractor.extract(filepath)

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

        filepath = os.path.join(UPLOAD_FOLDER, file_id)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404

        # Generate new filename
        new_filename = file_manager.generate_filename(expense_data)

        # Organize file into folder structure
        final_path = file_manager.organize_file(filepath, expense_data, new_filename)

        # Store expense record
        expense_data['file_path'] = final_path
        expense_data['processed_date'] = datetime.now().isoformat()
        expense_id = categorizer.add_expense(expense_data)

        return jsonify({
            'success': True,
            'expense_id': expense_id,
            'final_path': final_path,
            'filename': new_filename
        })
    except Exception as e:
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    """Get all expenses with optional filters"""
    try:
        # Get query parameters
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
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
