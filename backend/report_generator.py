import json
import csv
import os
from datetime import datetime
from collections import defaultdict

class ReportGenerator:
    """Generate expense reports in various formats"""

    def __init__(self, data_folder, db_adapter=None):
        self.data_folder = data_folder
        # Use db_adapter if provided, otherwise fall back to ExpenseCategorizer
        if db_adapter:
            self.categorizer = db_adapter
        else:
            from categorizer import ExpenseCategorizer
            self.categorizer = ExpenseCategorizer(data_folder)

    def generate_report(self, report_type, filters=None):
        """Generate report based on type and filters"""
        if filters is None:
            filters = {}

        # Get filtered expenses
        expenses = self.categorizer.get_expenses(
            category=filters.get('category'),
            vendor=filters.get('vendor'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            search=filters.get('search')
        )

        if report_type == 'summary':
            return self.generate_summary_report(expenses)
        elif report_type == 'detailed':
            return self.generate_detailed_report(expenses)
        elif report_type == 'by_category':
            return self.generate_category_report(expenses)
        elif report_type == 'by_vendor':
            return self.generate_vendor_report(expenses)
        elif report_type == 'monthly':
            return self.generate_monthly_report(expenses)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    def generate_summary_report(self, expenses):
        """Generate summary report"""
        if not expenses:
            return {
                'total_expenses': 0,
                'total_amount': 0,
                'date_range': {'start': None, 'end': None},
                'categories': [],
                'top_vendors': []
            }

        total_amount = sum(e.get('amount', 0) for e in expenses)

        # Get date range
        dates = [e.get('date') for e in expenses if e.get('date')]
        date_range = {
            'start': min(dates) if dates else None,
            'end': max(dates) if dates else None
        }

        # Group by category
        by_category = defaultdict(lambda: {'count': 0, 'total': 0})
        for expense in expenses:
            cat = expense.get('category', 'Uncategorized')
            by_category[cat]['count'] += 1
            by_category[cat]['total'] += expense.get('amount', 0)

        categories = [
            {'category': cat, 'count': data['count'], 'total': data['total']}
            for cat, data in by_category.items()
        ]
        categories.sort(key=lambda x: x['total'], reverse=True)

        # Top vendors
        by_vendor = defaultdict(lambda: {'count': 0, 'total': 0})
        for expense in expenses:
            vendor = expense.get('vendor', 'Unknown')
            by_vendor[vendor]['count'] += 1
            by_vendor[vendor]['total'] += expense.get('amount', 0)

        top_vendors = [
            {'vendor': vendor, 'count': data['count'], 'total': data['total']}
            for vendor, data in by_vendor.items()
        ]
        top_vendors.sort(key=lambda x: x['total'], reverse=True)
        top_vendors = top_vendors[:10]

        return {
            'total_expenses': len(expenses),
            'total_amount': total_amount,
            'average_amount': total_amount / len(expenses) if expenses else 0,
            'date_range': date_range,
            'categories': categories,
            'top_vendors': top_vendors
        }

    def generate_detailed_report(self, expenses):
        """Generate detailed line-by-line report"""
        return {
            'expenses': expenses,
            'total_amount': sum(e.get('amount', 0) for e in expenses),
            'count': len(expenses)
        }

    def generate_category_report(self, expenses):
        """Generate report grouped by category"""
        by_category = defaultdict(list)

        for expense in expenses:
            cat = expense.get('category', 'Uncategorized')
            by_category[cat].append(expense)

        report = []
        for category, cat_expenses in by_category.items():
            total = sum(e.get('amount', 0) for e in cat_expenses)
            report.append({
                'category': category,
                'count': len(cat_expenses),
                'total': total,
                'expenses': sorted(cat_expenses, key=lambda x: x.get('date', ''), reverse=True)
            })

        report.sort(key=lambda x: x['total'], reverse=True)

        return {
            'categories': report,
            'total_amount': sum(e.get('amount', 0) for e in expenses),
            'total_expenses': len(expenses)
        }

    def generate_vendor_report(self, expenses):
        """Generate report grouped by vendor"""
        by_vendor = defaultdict(list)

        for expense in expenses:
            vendor = expense.get('vendor', 'Unknown')
            by_vendor[vendor].append(expense)

        report = []
        for vendor, vendor_expenses in by_vendor.items():
            total = sum(e.get('amount', 0) for e in vendor_expenses)
            report.append({
                'vendor': vendor,
                'count': len(vendor_expenses),
                'total': total,
                'expenses': sorted(vendor_expenses, key=lambda x: x.get('date', ''), reverse=True)
            })

        report.sort(key=lambda x: x['total'], reverse=True)

        return {
            'vendors': report,
            'total_amount': sum(e.get('amount', 0) for e in expenses),
            'total_expenses': len(expenses)
        }

    def generate_monthly_report(self, expenses):
        """Generate report grouped by month"""
        by_month = defaultdict(list)

        for expense in expenses:
            date_str = expense.get('date', '')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    month_key = dt.strftime('%Y-%m')
                    month_name = dt.strftime('%B %Y')
                    by_month[(month_key, month_name)].append(expense)
                except ValueError:
                    by_month[('unknown', 'Unknown')].append(expense)
            else:
                by_month[('unknown', 'Unknown')].append(expense)

        report = []
        for (month_key, month_name), month_expenses in by_month.items():
            total = sum(e.get('amount', 0) for e in month_expenses)

            # Break down by category within month
            by_category = defaultdict(lambda: {'count': 0, 'total': 0})
            for expense in month_expenses:
                cat = expense.get('category', 'Uncategorized')
                by_category[cat]['count'] += 1
                by_category[cat]['total'] += expense.get('amount', 0)

            categories = [
                {'category': cat, 'count': data['count'], 'total': data['total']}
                for cat, data in by_category.items()
            ]
            categories.sort(key=lambda x: x['total'], reverse=True)

            report.append({
                'month_key': month_key,
                'month_name': month_name,
                'count': len(month_expenses),
                'total': total,
                'categories': categories,
                'expenses': sorted(month_expenses, key=lambda x: x.get('date', ''), reverse=True)
            })

        report.sort(key=lambda x: x['month_key'], reverse=True)

        return {
            'months': report,
            'total_amount': sum(e.get('amount', 0) for e in expenses),
            'total_expenses': len(expenses)
        }

    def export_to_csv(self, report_type, filters=None):
        """Export report to CSV file"""
        if filters is None:
            filters = {}

        # Get filtered expenses
        expenses = self.categorizer.get_expenses(
            category=filters.get('category'),
            vendor=filters.get('vendor'),
            start_date=filters.get('start_date'),
            end_date=filters.get('end_date'),
            search=filters.get('search')
        )

        # Create CSV file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"expense_report_{timestamp}.csv"
        filepath = os.path.join(self.data_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Date', 'Vendor', 'Amount', 'Category', 'Description', 'Invoice Number', 'Notes']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for expense in expenses:
                writer.writerow({
                    'Date': expense.get('date', ''),
                    'Vendor': expense.get('vendor', ''),
                    'Amount': expense.get('amount', 0),
                    'Category': expense.get('category', ''),
                    'Description': expense.get('description', ''),
                    'Invoice Number': expense.get('invoice_number', ''),
                    'Notes': expense.get('notes', '')
                })

            # Add summary row
            writer.writerow({})
            writer.writerow({
                'Date': 'TOTAL',
                'Vendor': '',
                'Amount': sum(e.get('amount', 0) for e in expenses),
                'Category': '',
                'Description': f'{len(expenses)} expenses',
                'Invoice Number': '',
                'Notes': ''
            })

        return filepath
