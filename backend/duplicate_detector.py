import hashlib
import os
from PIL import Image
import imagehash
from datetime import datetime
from fuzzywuzzy import fuzz

class DuplicateDetector:
    """Detect duplicate invoices and receipts"""

    def __init__(self, categorizer):
        self.categorizer = categorizer
        self.duplicate_threshold = 85  # Similarity threshold for duplicates

    def calculate_file_hash(self, filepath):
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def calculate_image_hash(self, filepath):
        """
        Calculate perceptual hash of image
        This detects similar images even if slightly modified
        """
        try:
            if filepath.lower().endswith('.pdf'):
                # For PDFs, we'd need to convert first
                # For now, just use file hash
                return None

            image = Image.open(filepath)
            # Use average hash for quick comparison
            avg_hash = imagehash.average_hash(image)
            # Use perceptual hash for better accuracy
            p_hash = imagehash.phash(image)

            return {
                'average_hash': str(avg_hash),
                'perceptual_hash': str(p_hash)
            }
        except Exception as e:
            print(f"Error calculating image hash: {e}")
            return None

    def check_duplicate(self, filepath, extracted_data):
        """
        Check if document is a duplicate
        Returns (is_duplicate, duplicate_info, confidence)
        """
        duplicates = []

        # 1. Check file hash (exact duplicate)
        file_hash = self.calculate_file_hash(filepath)
        exact_duplicate = self._check_file_hash_duplicate(file_hash)
        if exact_duplicate:
            return True, exact_duplicate, 100

        # 2. Check image hash (visually similar)
        image_hashes = self.calculate_image_hash(filepath)
        if image_hashes:
            similar_image = self._check_image_hash_duplicate(image_hashes)
            if similar_image:
                duplicates.append({
                    'type': 'visual_similarity',
                    'expense': similar_image,
                    'confidence': 95
                })

        # 3. Check metadata similarity
        metadata_duplicates = self._check_metadata_duplicate(extracted_data)
        if metadata_duplicates:
            duplicates.extend(metadata_duplicates)

        # Return highest confidence duplicate
        if duplicates:
            best_duplicate = max(duplicates, key=lambda x: x['confidence'])
            if best_duplicate['confidence'] >= self.duplicate_threshold:
                return True, best_duplicate, best_duplicate['confidence']

        return False, None, 0

    def _check_file_hash_duplicate(self, file_hash):
        """Check if file hash exists in expenses"""
        expenses = self.categorizer.expenses

        for expense in expenses:
            if expense.get('file_hash') == file_hash:
                return {
                    'type': 'exact_match',
                    'expense': expense
                }

        return None

    def _check_image_hash_duplicate(self, image_hashes):
        """Check for visually similar images"""
        if not image_hashes:
            return None

        expenses = self.categorizer.expenses
        avg_hash_str = image_hashes['average_hash']
        p_hash_str = image_hashes['perceptual_hash']

        for expense in expenses:
            stored_hashes = expense.get('image_hashes', {})
            if not stored_hashes:
                continue

            # Compare perceptual hashes
            if 'perceptual_hash' in stored_hashes:
                stored_p_hash = stored_hashes['perceptual_hash']
                # Calculate Hamming distance
                distance = self._hamming_distance(p_hash_str, stored_p_hash)

                # Hashes are 16 characters (64 bits), distance < 10 is very similar
                if distance < 10:
                    return {
                        'type': 'visual_similarity',
                        'expense': expense,
                        'distance': distance
                    }

        return None

    def _hamming_distance(self, hash1, hash2):
        """Calculate Hamming distance between two hash strings"""
        if len(hash1) != len(hash2):
            return 999

        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def _check_metadata_duplicate(self, extracted_data):
        """Check for duplicates based on metadata similarity"""
        duplicates = []
        expenses = self.categorizer.expenses

        vendor = extracted_data.get('vendor', '').lower()
        amount = extracted_data.get('amount', 0)
        date = extracted_data.get('date', '')
        invoice_number = extracted_data.get('invoice_number', '')

        for expense in expenses:
            similarity_score = 0
            reasons = []

            # 1. Check invoice number (strongest indicator)
            if invoice_number and expense.get('invoice_number'):
                if invoice_number.lower() == expense['invoice_number'].lower():
                    similarity_score += 50
                    reasons.append('Same invoice number')

            # 2. Check vendor similarity
            expense_vendor = expense.get('vendor', '').lower()
            if vendor and expense_vendor:
                vendor_similarity = fuzz.ratio(vendor, expense_vendor)
                if vendor_similarity > 85:
                    similarity_score += 20
                    reasons.append(f'Vendor match ({vendor_similarity}%)')

            # 3. Check amount
            expense_amount = expense.get('amount', 0)
            if amount and expense_amount:
                if abs(amount - expense_amount) < 0.01:
                    similarity_score += 20
                    reasons.append('Same amount')
                elif abs(amount - expense_amount) < amount * 0.05:  # Within 5%
                    similarity_score += 10
                    reasons.append('Similar amount')

            # 4. Check date proximity
            expense_date = expense.get('date', '')
            if date and expense_date:
                try:
                    date1 = datetime.strptime(date, '%Y-%m-%d')
                    date2 = datetime.strptime(expense_date, '%Y-%m-%d')
                    days_diff = abs((date1 - date2).days)

                    if days_diff == 0:
                        similarity_score += 15
                        reasons.append('Same date')
                    elif days_diff <= 7:
                        similarity_score += 5
                        reasons.append('Similar date')
                except ValueError:
                    pass

            # If similarity is high enough, mark as potential duplicate
            if similarity_score >= 70:
                duplicates.append({
                    'type': 'metadata_similarity',
                    'expense': expense,
                    'confidence': similarity_score,
                    'reasons': reasons
                })

        return duplicates

    def find_similar_expenses(self, expense_data, limit=5):
        """
        Find expenses similar to the given expense
        Useful for finding related transactions
        """
        similar = []
        expenses = self.categorizer.expenses

        vendor = expense_data.get('vendor', '').lower()
        amount = expense_data.get('amount', 0)
        category = expense_data.get('category', '')

        for expense in expenses:
            if expense.get('id') == expense_data.get('id'):
                continue  # Skip self

            similarity_score = 0

            # Vendor similarity
            expense_vendor = expense.get('vendor', '').lower()
            if vendor and expense_vendor:
                vendor_sim = fuzz.ratio(vendor, expense_vendor)
                similarity_score += vendor_sim * 0.4

            # Category match
            if category and expense.get('category') == category:
                similarity_score += 30

            # Amount similarity
            expense_amount = expense.get('amount', 0)
            if amount and expense_amount:
                amount_diff = abs(amount - expense_amount)
                max_amount = max(amount, expense_amount)
                if max_amount > 0:
                    amount_similarity = (1 - min(amount_diff / max_amount, 1)) * 30
                    similarity_score += amount_similarity

            if similarity_score >= 50:
                similar.append({
                    'expense': expense,
                    'similarity': similarity_score
                })

        # Sort by similarity and return top results
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]

    def get_duplicate_statistics(self):
        """Get statistics about duplicate detection"""
        expenses = self.categorizer.expenses

        stats = {
            'total_expenses': len(expenses),
            'expenses_with_hash': sum(1 for e in expenses if 'file_hash' in e),
            'expenses_with_image_hash': sum(1 for e in expenses if 'image_hashes' in e),
            'expenses_with_invoice_number': sum(1 for e in expenses if e.get('invoice_number'))
        }

        return stats

    def mark_as_duplicate(self, expense_id, original_expense_id):
        """Mark an expense as a duplicate of another"""
        expenses = self.categorizer.expenses

        for expense in expenses:
            if expense.get('id') == expense_id:
                expense['is_duplicate'] = True
                expense['duplicate_of'] = original_expense_id
                expense['marked_duplicate_date'] = datetime.now().isoformat()
                break

        self.categorizer.save_expenses()

    def unmark_duplicate(self, expense_id):
        """Unmark an expense as duplicate"""
        expenses = self.categorizer.expenses

        for expense in expenses:
            if expense.get('id') == expense_id:
                expense['is_duplicate'] = False
                expense.pop('duplicate_of', None)
                expense.pop('marked_duplicate_date', None)
                break

        self.categorizer.save_expenses()

    def get_duplicates(self):
        """Get all expenses marked as duplicates"""
        expenses = self.categorizer.expenses
        return [e for e in expenses if e.get('is_duplicate', False)]
