import json
import os
from datetime import datetime
from collections import defaultdict
from fuzzywuzzy import fuzz

class ExpenseCategorizer:
    """Categorize expenses and provide smart suggestions"""

    # Predefined categories with keywords
    CATEGORIES = {
        'Office Supplies': ['office', 'staples', 'paper', 'pen', 'desk', 'supplies', 'depot'],
        'Software & Services': ['software', 'saas', 'subscription', 'cloud', 'hosting', 'adobe', 'microsoft', 'google'],
        'Travel': ['hotel', 'airbnb', 'flight', 'airline', 'uber', 'lyft', 'taxi', 'rental', 'car'],
        'Meals & Entertainment': ['restaurant', 'food', 'coffee', 'starbucks', 'meal', 'dining', 'catering'],
        'Utilities': ['electric', 'gas', 'water', 'internet', 'phone', 'utility'],
        'Marketing': ['advertising', 'marketing', 'facebook', 'google ads', 'social media', 'promotion'],
        'Equipment': ['computer', 'laptop', 'monitor', 'equipment', 'hardware', 'machinery'],
        'Professional Services': ['consulting', 'legal', 'accounting', 'professional', 'attorney', 'cpa'],
        'Insurance': ['insurance', 'policy', 'premium', 'coverage'],
        'Rent & Lease': ['rent', 'lease', 'property', 'landlord'],
        'Shipping': ['shipping', 'fedex', 'ups', 'usps', 'dhl', 'postage'],
        'Maintenance': ['repair', 'maintenance', 'cleaning', 'service'],
        'Training': ['training', 'course', 'education', 'workshop', 'seminar', 'conference'],
        'Miscellaneous': []
    }

    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.expenses_file = os.path.join(data_folder, 'expenses.json')
        self.expenses = self.load_expenses()
        self.vendor_history = self.build_vendor_history()

    def load_expenses(self):
        """Load expenses from JSON file"""
        if os.path.exists(self.expenses_file):
            try:
                with open(self.expenses_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_expenses(self):
        """Save expenses to JSON file"""
        with open(self.expenses_file, 'w') as f:
            json.dump(self.expenses, f, indent=2)

    def build_vendor_history(self):
        """Build vendor-to-category mapping from history"""
        history = defaultdict(lambda: defaultdict(int))

        for expense in self.expenses:
            vendor = expense.get('vendor', '').lower()
            category = expense.get('category', '')
            if vendor and category:
                history[vendor][category] += 1

        return history

    def suggest_category(self, vendor, description=''):
        """Suggest category based on vendor and description"""
        suggestions = []

        # Normalize input
        vendor_lower = vendor.lower()
        description_lower = description.lower()
        combined_text = f"{vendor_lower} {description_lower}"

        # 1. Check vendor history (highest priority)
        if vendor_lower in self.vendor_history:
            # Get most frequently used category for this vendor
            category_counts = self.vendor_history[vendor_lower]
            if category_counts:
                most_common = max(category_counts.items(), key=lambda x: x[1])
                suggestions.append({
                    'category': most_common[0],
                    'confidence': 95,
                    'reason': f'Used {most_common[1]} times for this vendor'
                })

        # 2. Check for fuzzy vendor matches in history
        if not suggestions:
            for known_vendor in self.vendor_history.keys():
                similarity = fuzz.ratio(vendor_lower, known_vendor)
                if similarity > 80:  # High similarity threshold
                    category_counts = self.vendor_history[known_vendor]
                    if category_counts:
                        most_common = max(category_counts.items(), key=lambda x: x[1])
                        suggestions.append({
                            'category': most_common[0],
                            'confidence': similarity,
                            'reason': f'Similar to "{known_vendor}"'
                        })
                        break

        # 3. Check keyword matching
        keyword_matches = []
        for category, keywords in self.CATEGORIES.items():
            score = 0
            matched_keywords = []

            for keyword in keywords:
                if keyword in combined_text:
                    score += 1
                    matched_keywords.append(keyword)

            if score > 0:
                confidence = min(70 + (score * 10), 90)
                keyword_matches.append({
                    'category': category,
                    'confidence': confidence,
                    'reason': f'Matches: {", ".join(matched_keywords)}'
                })

        # Sort keyword matches by confidence
        keyword_matches.sort(key=lambda x: x['confidence'], reverse=True)

        # Add top keyword matches to suggestions
        suggestions.extend(keyword_matches[:3])

        # If no matches, suggest Miscellaneous
        if not suggestions:
            suggestions.append({
                'category': 'Miscellaneous',
                'confidence': 50,
                'reason': 'Default category'
            })

        return suggestions

    def add_expense(self, expense_data):
        """Add new expense record"""
        # Generate unique ID
        expense_id = f"EXP{datetime.now().strftime('%Y%m%d%H%M%S')}"

        expense_record = {
            'id': expense_id,
            'date': expense_data.get('date'),
            'vendor': expense_data.get('vendor'),
            'amount': expense_data.get('amount'),
            'category': expense_data.get('category'),
            'description': expense_data.get('description'),
            'invoice_number': expense_data.get('invoice_number', ''),
            'tags': expense_data.get('tags', []),
            'file_path': expense_data.get('file_path', ''),
            'processed_date': expense_data.get('processed_date'),
            'notes': expense_data.get('notes', '')
        }

        self.expenses.append(expense_record)
        self.save_expenses()

        # Update vendor history
        vendor_lower = expense_record['vendor'].lower()
        category = expense_record['category']
        self.vendor_history[vendor_lower][category] += 1

        return expense_id

    def get_expenses(self, category=None, vendor=None, start_date=None, end_date=None, search=None):
        """Get expenses with optional filters"""
        filtered = self.expenses

        # Filter by category
        if category:
            filtered = [e for e in filtered if e.get('category') == category]

        # Filter by vendor
        if vendor:
            filtered = [e for e in filtered if vendor.lower() in e.get('vendor', '').lower()]

        # Filter by date range
        if start_date:
            filtered = [e for e in filtered if e.get('date', '') >= start_date]

        if end_date:
            filtered = [e for e in filtered if e.get('date', '') <= end_date]

        # Search in vendor, description, and notes
        if search:
            search_lower = search.lower()
            filtered = [
                e for e in filtered
                if search_lower in e.get('vendor', '').lower()
                or search_lower in e.get('description', '').lower()
                or search_lower in e.get('notes', '').lower()
            ]

        # Sort by date (newest first)
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)

        return filtered

    def get_all_categories(self):
        """Get all available categories"""
        return list(self.CATEGORIES.keys())

    def get_all_vendors(self):
        """Get all unique vendors"""
        vendors = set()
        for expense in self.expenses:
            vendor = expense.get('vendor')
            if vendor:
                vendors.add(vendor)
        return sorted(list(vendors))

    def get_statistics(self):
        """Get expense statistics"""
        if not self.expenses:
            return {
                'total_expenses': 0,
                'total_amount': 0,
                'by_category': {},
                'by_vendor': {},
                'by_month': {},
                'recent_expenses': []
            }

        total_amount = sum(e.get('amount', 0) for e in self.expenses)

        # By category
        by_category = defaultdict(lambda: {'count': 0, 'total': 0})
        for expense in self.expenses:
            cat = expense.get('category', 'Uncategorized')
            by_category[cat]['count'] += 1
            by_category[cat]['total'] += expense.get('amount', 0)

        # By vendor
        by_vendor = defaultdict(lambda: {'count': 0, 'total': 0})
        for expense in self.expenses:
            vendor = expense.get('vendor', 'Unknown')
            by_vendor[vendor]['count'] += 1
            by_vendor[vendor]['total'] += expense.get('amount', 0)

        # By month
        by_month = defaultdict(lambda: {'count': 0, 'total': 0})
        for expense in self.expenses:
            date_str = expense.get('date', '')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, '%Y-%m-%d')
                    month_key = dt.strftime('%Y-%m')
                    by_month[month_key]['count'] += 1
                    by_month[month_key]['total'] += expense.get('amount', 0)
                except ValueError:
                    pass

        # Recent expenses
        recent = sorted(self.expenses, key=lambda x: x.get('processed_date', ''), reverse=True)[:10]

        return {
            'total_expenses': len(self.expenses),
            'total_amount': total_amount,
            'by_category': dict(by_category),
            'by_vendor': dict(sorted(by_vendor.items(), key=lambda x: x[1]['total'], reverse=True)[:10]),
            'by_month': dict(sorted(by_month.items(), reverse=True)),
            'recent_expenses': recent
        }
