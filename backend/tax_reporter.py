import json
import os
import csv
from datetime import datetime
from collections import defaultdict

class TaxReporter:
    """Generate tax reports and track deductible expenses"""

    # IRS-recognized business expense categories with deduction rules
    TAX_CATEGORIES = {
        'Office Supplies': {
            'deductible': True,
            'irs_category': 'Supplies',
            'form': 'Schedule C',
            'line': '22',
            'percentage': 100,
            'notes': 'Fully deductible business supplies'
        },
        'Software & Services': {
            'deductible': True,
            'irs_category': 'Software/Subscriptions',
            'form': 'Schedule C',
            'line': '18 or 27',
            'percentage': 100,
            'notes': 'Business software and online services'
        },
        'Travel': {
            'deductible': True,
            'irs_category': 'Travel',
            'form': 'Schedule C',
            'line': '24',
            'percentage': 100,
            'notes': 'Business travel expenses (lodging, airfare, etc.)'
        },
        'Meals & Entertainment': {
            'deductible': True,
            'irs_category': 'Meals',
            'form': 'Schedule C',
            'line': '24b',
            'percentage': 50,
            'notes': 'Business meals (50% deductible as of 2023)'
        },
        'Utilities': {
            'deductible': True,
            'irs_category': 'Utilities',
            'form': 'Schedule C',
            'line': '25',
            'percentage': 100,
            'notes': 'Business utilities (phone, internet, etc.)'
        },
        'Marketing': {
            'deductible': True,
            'irs_category': 'Advertising',
            'form': 'Schedule C',
            'line': '8',
            'percentage': 100,
            'notes': 'Advertising and promotional expenses'
        },
        'Equipment': {
            'deductible': True,
            'irs_category': 'Equipment',
            'form': 'Schedule C / Form 4562',
            'line': '13',
            'percentage': 100,
            'notes': 'May require depreciation. Section 179 election available.'
        },
        'Professional Services': {
            'deductible': True,
            'irs_category': 'Legal/Professional Services',
            'form': 'Schedule C',
            'line': '17',
            'percentage': 100,
            'notes': 'Fees for professional services'
        },
        'Insurance': {
            'deductible': True,
            'irs_category': 'Insurance',
            'form': 'Schedule C',
            'line': '15',
            'percentage': 100,
            'notes': 'Business insurance premiums'
        },
        'Rent & Lease': {
            'deductible': True,
            'irs_category': 'Rent/Lease',
            'form': 'Schedule C',
            'line': '20',
            'percentage': 100,
            'notes': 'Business property rent or equipment lease'
        },
        'Shipping': {
            'deductible': True,
            'irs_category': 'Freight',
            'form': 'Schedule C',
            'line': '27',
            'percentage': 100,
            'notes': 'Shipping and freight charges'
        },
        'Maintenance': {
            'deductible': True,
            'irs_category': 'Repairs/Maintenance',
            'form': 'Schedule C',
            'line': '21',
            'percentage': 100,
            'notes': 'Repairs and maintenance (not improvements)'
        },
        'Training': {
            'deductible': True,
            'irs_category': 'Education',
            'form': 'Schedule C',
            'line': '27',
            'percentage': 100,
            'notes': 'Business-related education and training'
        },
        'Miscellaneous': {
            'deductible': False,
            'irs_category': 'Other Expenses',
            'form': 'Schedule C',
            'line': '27',
            'percentage': 0,
            'notes': 'Review for potential deductibility'
        }
    }

    def __init__(self, data_folder, categorizer):
        self.data_folder = data_folder
        self.categorizer = categorizer
        self.tax_settings_file = os.path.join(data_folder, 'tax_settings.json')
        self.tax_settings = self.load_tax_settings()

    def load_tax_settings(self):
        """Load tax settings"""
        if os.path.exists(self.tax_settings_file):
            try:
                with open(self.tax_settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.get_default_settings()
        return self.get_default_settings()

    def get_default_settings(self):
        """Get default tax settings"""
        return {
            'tax_year': datetime.now().year,
            'entity_type': 'sole_proprietorship',  # sole_proprietorship, llc, s_corp, c_corp
            'fiscal_year_start': '01-01',
            'mileage_rate': 0.655,  # IRS standard mileage rate (2023)
            'home_office_sqft': 0,
            'total_home_sqft': 0,
            'custom_categories': {}
        }

    def save_tax_settings(self):
        """Save tax settings"""
        with open(self.tax_settings_file, 'w') as f:
            json.dump(self.tax_settings, f, indent=2)

    def update_tax_settings(self, settings):
        """Update tax settings"""
        self.tax_settings.update(settings)
        self.save_tax_settings()

    def generate_tax_summary(self, tax_year=None):
        """
        Generate comprehensive tax summary
        """
        if tax_year is None:
            tax_year = self.tax_settings['tax_year']

        # Get expenses for tax year
        start_date = f"{tax_year}-01-01"
        end_date = f"{tax_year}-12-31"

        expenses = self.categorizer.get_expenses(
            start_date=start_date,
            end_date=end_date
        )

        # Group by category
        by_category = defaultdict(lambda: {
            'expenses': [],
            'total': 0,
            'deductible_amount': 0,
            'count': 0
        })

        total_expenses = 0
        total_deductible = 0

        for expense in expenses:
            category = expense.get('category', 'Miscellaneous')
            amount = expense.get('amount', 0)

            by_category[category]['expenses'].append(expense)
            by_category[category]['total'] += amount
            by_category[category]['count'] += 1

            # Calculate deductible amount
            tax_info = self.TAX_CATEGORIES.get(category, self.TAX_CATEGORIES['Miscellaneous'])
            if tax_info['deductible']:
                deductible = amount * (tax_info['percentage'] / 100)
                by_category[category]['deductible_amount'] += deductible
                total_deductible += deductible

            total_expenses += amount

        # Add tax information to each category
        category_summaries = []
        for category, data in by_category.items():
            tax_info = self.TAX_CATEGORIES.get(category, self.TAX_CATEGORIES['Miscellaneous'])

            category_summaries.append({
                'category': category,
                'total': data['total'],
                'count': data['count'],
                'deductible_amount': data['deductible_amount'],
                'deductible': tax_info['deductible'],
                'irs_category': tax_info['irs_category'],
                'form': tax_info['form'],
                'line': tax_info['line'],
                'percentage': tax_info['percentage'],
                'notes': tax_info['notes']
            })

        # Sort by total amount
        category_summaries.sort(key=lambda x: x['total'], reverse=True)

        return {
            'tax_year': tax_year,
            'total_expenses': total_expenses,
            'total_deductible': total_deductible,
            'total_non_deductible': total_expenses - total_deductible,
            'expense_count': len(expenses),
            'categories': category_summaries,
            'entity_type': self.tax_settings['entity_type'],
            'generated_date': datetime.now().isoformat()
        }

    def generate_schedule_c_report(self, tax_year=None):
        """
        Generate Schedule C formatted report (for sole proprietors)
        """
        summary = self.generate_tax_summary(tax_year)

        # Map categories to Schedule C lines
        schedule_c_lines = defaultdict(lambda: {'amount': 0, 'categories': []})

        for cat_summary in summary['categories']:
            line = cat_summary['line']
            schedule_c_lines[line]['amount'] += cat_summary['deductible_amount']
            schedule_c_lines[line]['categories'].append(cat_summary['category'])

        # Convert to list and sort by line number
        lines = []
        for line_num, data in schedule_c_lines.items():
            lines.append({
                'line': line_num,
                'amount': data['amount'],
                'categories': ', '.join(data['categories'])
            })

        # Sort by line number (handle ranges like "18 or 27")
        lines.sort(key=lambda x: int(x['line'].split()[0]))

        return {
            'tax_year': summary['tax_year'],
            'form': 'Schedule C',
            'total_deductions': summary['total_deductible'],
            'lines': lines,
            'generated_date': datetime.now().isoformat()
        }

    def generate_quarterly_estimate(self, quarter, tax_year=None):
        """
        Generate quarterly tax estimate
        quarter: 1-4
        """
        if tax_year is None:
            tax_year = self.tax_settings['tax_year']

        # Calculate quarter dates
        quarter_months = {
            1: ('01', '03'),
            2: ('04', '06'),
            3: ('07', '09'),
            4: ('10', '12')
        }

        start_month, end_month = quarter_months[quarter]
        start_date = f"{tax_year}-{start_month}-01"

        # Get last day of end month
        if end_month == '12':
            end_date = f"{tax_year}-{end_month}-31"
        else:
            end_date = f"{tax_year}-{end_month}-30"

        expenses = self.categorizer.get_expenses(
            start_date=start_date,
            end_date=end_date
        )

        total_expenses = 0
        total_deductible = 0

        for expense in expenses:
            amount = expense.get('amount', 0)
            category = expense.get('category', 'Miscellaneous')

            total_expenses += amount

            tax_info = self.TAX_CATEGORIES.get(category, self.TAX_CATEGORIES['Miscellaneous'])
            if tax_info['deductible']:
                deductible = amount * (tax_info['percentage'] / 100)
                total_deductible += deductible

        return {
            'tax_year': tax_year,
            'quarter': quarter,
            'start_date': start_date,
            'end_date': end_date,
            'total_expenses': total_expenses,
            'total_deductible': total_deductible,
            'expense_count': len(expenses)
        }

    def export_tax_report_csv(self, tax_year=None):
        """
        Export detailed tax report to CSV
        """
        summary = self.generate_tax_summary(tax_year)

        filename = f"tax_report_{summary['tax_year']}.csv"
        filepath = os.path.join(self.data_folder, filename)

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Write summary
            writer = csv.writer(csvfile)
            writer.writerow(['TAX REPORT', summary['tax_year']])
            writer.writerow([])
            writer.writerow(['Summary'])
            writer.writerow(['Total Expenses', f"${summary['total_expenses']:.2f}"])
            writer.writerow(['Total Deductible', f"${summary['total_deductible']:.2f}"])
            writer.writerow(['Total Non-Deductible', f"${summary['total_non_deductible']:.2f}"])
            writer.writerow(['Expense Count', summary['expense_count']])
            writer.writerow([])

            # Write category breakdown
            writer.writerow(['CATEGORY BREAKDOWN'])
            writer.writerow([
                'Category',
                'Total Amount',
                'Deductible Amount',
                'Deduction %',
                'Count',
                'IRS Category',
                'Form',
                'Line',
                'Notes'
            ])

            for cat in summary['categories']:
                writer.writerow([
                    cat['category'],
                    f"${cat['total']:.2f}",
                    f"${cat['deductible_amount']:.2f}",
                    f"{cat['percentage']}%",
                    cat['count'],
                    cat['irs_category'],
                    cat['form'],
                    cat['line'],
                    cat['notes']
                ])

            writer.writerow([])

            # Write detailed expense list
            writer.writerow(['DETAILED EXPENSE LIST'])
            writer.writerow([
                'Date',
                'Vendor',
                'Amount',
                'Category',
                'Deductible Amount',
                'IRS Category',
                'Form/Line',
                'Description',
                'Invoice #'
            ])

            # Get all expenses for the year
            expenses = self.categorizer.get_expenses(
                start_date=f"{summary['tax_year']}-01-01",
                end_date=f"{summary['tax_year']}-12-31"
            )

            for expense in expenses:
                category = expense.get('category', 'Miscellaneous')
                amount = expense.get('amount', 0)
                tax_info = self.TAX_CATEGORIES.get(category, self.TAX_CATEGORIES['Miscellaneous'])

                deductible = amount * (tax_info['percentage'] / 100) if tax_info['deductible'] else 0

                writer.writerow([
                    expense.get('date', ''),
                    expense.get('vendor', ''),
                    f"${amount:.2f}",
                    category,
                    f"${deductible:.2f}",
                    tax_info['irs_category'],
                    f"{tax_info['form']} - Line {tax_info['line']}",
                    expense.get('description', ''),
                    expense.get('invoice_number', '')
                ])

        return filepath

    def get_deduction_recommendations(self):
        """
        Analyze expenses and recommend additional deductions
        """
        recommendations = []

        # Check for home office deduction
        if self.tax_settings.get('home_office_sqft', 0) > 0:
            total_sqft = self.tax_settings.get('total_home_sqft', 1)
            percentage = self.tax_settings['home_office_sqft'] / total_sqft

            recommendations.append({
                'type': 'home_office',
                'title': 'Home Office Deduction',
                'description': f'You may be eligible for home office deduction ({percentage:.1%} of home expenses)',
                'potential_savings': 'Varies based on home expenses',
                'action': 'Track utilities, rent/mortgage, insurance for home office percentage'
            })

        # Check for mileage tracking
        travel_expenses = self.categorizer.get_expenses(category='Travel')
        if len(travel_expenses) > 5:
            recommendations.append({
                'type': 'mileage',
                'title': 'Mileage Deduction',
                'description': 'Consider tracking business mileage for additional deductions',
                'potential_savings': f'${self.tax_settings["mileage_rate"]:.3f} per business mile',
                'action': 'Use mileage tracking app for business travel'
            })

        # Check for equipment depreciation
        equipment_total = sum(
            e.get('amount', 0)
            for e in self.categorizer.get_expenses(category='Equipment')
        )

        if equipment_total > 2500:
            recommendations.append({
                'type': 'depreciation',
                'title': 'Equipment Depreciation',
                'description': f'${equipment_total:.2f} in equipment may qualify for Section 179 deduction',
                'potential_savings': 'Up to full cost in year of purchase',
                'action': 'Consult with tax professional about Section 179 election'
            })

        return recommendations

    def get_tax_statistics(self):
        """Get tax-related statistics"""
        current_year = datetime.now().year
        summary = self.generate_tax_summary(current_year)

        return {
            'current_year': current_year,
            'total_expenses': summary['total_expenses'],
            'total_deductible': summary['total_deductible'],
            'deduction_rate': (summary['total_deductible'] / summary['total_expenses'] * 100) if summary['total_expenses'] > 0 else 0,
            'expense_count': summary['expense_count'],
            'categories_count': len(summary['categories']),
            'entity_type': self.tax_settings['entity_type']
        }
