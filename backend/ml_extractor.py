import json
import os
from datetime import datetime
from collections import defaultdict
import re

class MLExtractor:
    """Machine learning-enhanced extractor that learns from user corrections"""

    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.training_file = os.path.join(data_folder, 'ml_training.json')
        self.patterns_file = os.path.join(data_folder, 'learned_patterns.json')
        self.training_data = self.load_training_data()
        self.learned_patterns = self.load_learned_patterns()

    def load_training_data(self):
        """Load training data from corrections"""
        if os.path.exists(self.training_file):
            try:
                with open(self.training_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_training_data(self):
        """Save training data"""
        with open(self.training_file, 'w') as f:
            json.dump(self.training_data, f, indent=2)

    def load_learned_patterns(self):
        """Load learned patterns"""
        if os.path.exists(self.patterns_file):
            try:
                with open(self.patterns_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.initialize_patterns()
        return self.initialize_patterns()

    def initialize_patterns(self):
        """Initialize pattern structure"""
        return {
            'vendor_patterns': {},
            'amount_contexts': {},
            'date_formats': {},
            'invoice_patterns': {}
        }

    def save_learned_patterns(self):
        """Save learned patterns"""
        with open(self.patterns_file, 'w') as f:
            json.dump(self.learned_patterns, f, indent=2)

    def add_correction(self, raw_text, extracted_data, corrected_data):
        """
        Learn from user corrections
        Compare what was extracted vs what the user corrected it to
        """
        correction = {
            'timestamp': datetime.now().isoformat(),
            'raw_text': raw_text,
            'extracted': extracted_data,
            'corrected': corrected_data
        }

        self.training_data.append(correction)
        self.save_training_data()

        # Update learned patterns
        self._update_vendor_patterns(raw_text, extracted_data.get('vendor'), corrected_data.get('vendor'))
        self._update_amount_patterns(raw_text, extracted_data.get('amount'), corrected_data.get('amount'))
        self._update_date_patterns(raw_text, extracted_data.get('date'), corrected_data.get('date'))

        self.save_learned_patterns()

        # Retrain if we have enough data
        if len(self.training_data) >= 10 and len(self.training_data) % 10 == 0:
            self.retrain()

    def _update_vendor_patterns(self, raw_text, extracted_vendor, corrected_vendor):
        """Learn vendor extraction patterns"""
        if not corrected_vendor or extracted_vendor == corrected_vendor:
            return

        # Find where the correct vendor appears in the text
        lines = raw_text.split('\n')
        for i, line in enumerate(lines):
            if corrected_vendor.lower() in line.lower():
                # Record the context
                context = {
                    'line_number': i,
                    'total_lines': len(lines),
                    'line_content': line.strip(),
                    'before': lines[i-1].strip() if i > 0 else '',
                    'after': lines[i+1].strip() if i < len(lines)-1 else ''
                }

                if corrected_vendor not in self.learned_patterns['vendor_patterns']:
                    self.learned_patterns['vendor_patterns'][corrected_vendor] = []

                self.learned_patterns['vendor_patterns'][corrected_vendor].append(context)
                break

    def _update_amount_patterns(self, raw_text, extracted_amount, corrected_amount):
        """Learn amount extraction patterns"""
        if not corrected_amount or extracted_amount == corrected_amount:
            return

        # Find amount patterns in context
        amount_str = f"{corrected_amount:.2f}"
        if amount_str in raw_text or str(int(corrected_amount)) in raw_text:
            # Find surrounding context
            lines = raw_text.split('\n')
            for line in lines:
                if amount_str in line or str(int(corrected_amount)) in line:
                    context_key = self._extract_amount_context(line)
                    if context_key:
                        if context_key not in self.learned_patterns['amount_contexts']:
                            self.learned_patterns['amount_contexts'][context_key] = 0
                        self.learned_patterns['amount_contexts'][context_key] += 1

    def _extract_amount_context(self, line):
        """Extract context keywords around amount"""
        keywords = ['total', 'amount', 'due', 'balance', 'sum', 'grand total', 'subtotal', 'pay']
        line_lower = line.lower()

        for keyword in keywords:
            if keyword in line_lower:
                return keyword

        return None

    def _update_date_patterns(self, raw_text, extracted_date, corrected_date):
        """Learn date format patterns"""
        if not corrected_date or extracted_date == corrected_date:
            return

        # Record successful date format if we got it right
        if extracted_date == corrected_date:
            date_format = self._detect_date_format(raw_text, corrected_date)
            if date_format:
                if date_format not in self.learned_patterns['date_formats']:
                    self.learned_patterns['date_formats'][date_format] = 0
                self.learned_patterns['date_formats'][date_format] += 1

    def _detect_date_format(self, text, date_str):
        """Detect what format the date was in"""
        # Try to find the original date string in the text
        date_patterns = [
            (r'\d{1,2}/\d{1,2}/\d{4}', 'MM/DD/YYYY'),
            (r'\d{4}-\d{2}-\d{2}', 'YYYY-MM-DD'),
            (r'\d{1,2}-\d{1,2}-\d{4}', 'MM-DD-YYYY'),
            (r'\w+ \d{1,2}, \d{4}', 'Month DD, YYYY'),
        ]

        for pattern, format_name in date_patterns:
            if re.search(pattern, text):
                return format_name

        return None

    def enhance_extraction(self, extracted_data, raw_text):
        """
        Enhance extraction using learned patterns
        Apply ML corrections based on historical data
        """
        enhanced_data = extracted_data.copy()

        # Enhance vendor extraction
        vendor_confidence = 0
        for learned_vendor, contexts in self.learned_patterns['vendor_patterns'].items():
            if len(contexts) >= 3:  # High confidence if seen 3+ times
                # Check if this vendor appears in the text
                if learned_vendor.lower() in raw_text.lower():
                    # Check context similarity
                    lines = raw_text.split('\n')
                    for context in contexts:
                        if context['line_number'] < len(lines):
                            similarity = self._calculate_context_similarity(
                                lines[context['line_number']],
                                context['line_content']
                            )
                            if similarity > 0.7:
                                enhanced_data['vendor'] = learned_vendor
                                vendor_confidence = min(95, 70 + len(contexts) * 5)
                                break

        # Enhance amount extraction using learned contexts
        if enhanced_data.get('amount') == 0 or enhanced_data.get('amount') is None:
            # Try to find amount using learned contexts
            for context_key, count in self.learned_patterns['amount_contexts'].items():
                if count >= 3:  # High confidence pattern
                    amount = self._extract_amount_with_context(raw_text, context_key)
                    if amount:
                        enhanced_data['amount'] = amount

        # Boost confidence based on learning
        original_confidence = enhanced_data.get('confidence', 0)
        learning_boost = min(20, len(self.training_data) * 2)
        enhanced_data['confidence'] = min(100, original_confidence + learning_boost)
        enhanced_data['ml_enhanced'] = True
        enhanced_data['training_samples'] = len(self.training_data)

        return enhanced_data

    def _calculate_context_similarity(self, text1, text2):
        """Calculate similarity between two text strings"""
        text1_lower = text1.lower().strip()
        text2_lower = text2.lower().strip()

        if text1_lower == text2_lower:
            return 1.0

        # Simple word-based similarity
        words1 = set(text1_lower.split())
        words2 = set(text2_lower.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _extract_amount_with_context(self, text, context_key):
        """Try to extract amount using learned context"""
        lines = text.split('\n')

        for line in lines:
            if context_key.lower() in line.lower():
                # Extract number from this line
                amounts = re.findall(r'\$?\s*(\d+[,.]?\d*\.?\d{2})', line)
                if amounts:
                    try:
                        amount = float(amounts[0].replace(',', ''))
                        if 0 < amount < 1000000:
                            return amount
                    except ValueError:
                        continue

        return None

    def retrain(self):
        """
        Retrain the model based on accumulated corrections
        Rebuild pattern confidences
        """
        print(f"Retraining ML model with {len(self.training_data)} samples...")

        # Rebuild pattern weights based on frequency
        vendor_frequency = defaultdict(int)
        amount_context_frequency = defaultdict(int)

        for correction in self.training_data:
            corrected = correction.get('corrected', {})
            raw_text = correction.get('raw_text', '')

            # Count vendor occurrences
            vendor = corrected.get('vendor')
            if vendor:
                vendor_frequency[vendor] += 1

        # Sort patterns by frequency for priority matching
        self.learned_patterns['vendor_frequency'] = dict(
            sorted(vendor_frequency.items(), key=lambda x: x[1], reverse=True)
        )

        self.save_learned_patterns()
        print("ML model retrained successfully!")

    def get_statistics(self):
        """Get ML training statistics"""
        return {
            'total_corrections': len(self.training_data),
            'learned_vendors': len(self.learned_patterns['vendor_patterns']),
            'learned_amount_contexts': len(self.learned_patterns['amount_contexts']),
            'learned_date_formats': len(self.learned_patterns['date_formats']),
            'retrain_count': len(self.training_data) // 10
        }
