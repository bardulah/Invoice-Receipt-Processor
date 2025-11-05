import os
import shutil
import re
from datetime import datetime

class FileManager:
    """Manage file naming and organization"""

    def __init__(self, processed_folder):
        self.processed_folder = processed_folder

    def generate_filename(self, expense_data):
        """
        Generate intelligent filename in format: Date-Vendor-Amount.ext
        Example: 2024-03-15-Amazon-4299.pdf
        """
        # Extract components
        date = expense_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        vendor = expense_data.get('vendor', 'Unknown')
        amount = expense_data.get('amount', 0)

        # Clean vendor name for filename
        vendor_clean = self.sanitize_filename(vendor)

        # Format amount (remove decimals if .00, otherwise keep 2 decimals)
        amount_str = f"{amount:.2f}".replace('.00', '').replace('.', '')

        # Get file extension from original filename or default to pdf
        original_filename = expense_data.get('original_filename', 'document.pdf')
        ext = os.path.splitext(original_filename)[1] or '.pdf'

        # Construct filename
        filename = f"{date}-{vendor_clean}-{amount_str}{ext}"

        return filename

    def sanitize_filename(self, name):
        """Clean up name for use in filename"""
        # Remove special characters
        name = re.sub(r'[^\w\s-]', '', name)

        # Replace spaces with hyphens
        name = re.sub(r'\s+', '-', name)

        # Remove multiple consecutive hyphens
        name = re.sub(r'-+', '-', name)

        # Limit length
        if len(name) > 30:
            name = name[:30]

        # Remove trailing hyphens
        name = name.strip('-')

        return name or 'Unknown'

    def organize_file(self, source_path, expense_data, new_filename):
        """
        Organize file into folder structure: processed/YYYY/MM-MonthName/Vendor/
        Example: processed/2024/03-March/Amazon/2024-03-15-Amazon-4299.pdf
        """
        # Parse date
        date_str = expense_data.get('date', datetime.now().strftime('%Y-%m-%d'))
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            date_obj = datetime.now()

        # Build folder structure
        year = date_obj.strftime('%Y')
        month = date_obj.strftime('%m-%B')  # 03-March
        vendor = self.sanitize_filename(expense_data.get('vendor', 'Unknown'))

        # Create folder path
        folder_path = os.path.join(self.processed_folder, year, month, vendor)
        os.makedirs(folder_path, exist_ok=True)

        # Build full destination path
        dest_path = os.path.join(folder_path, new_filename)

        # Handle duplicate filenames
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(new_filename)
            counter = 1
            while os.path.exists(dest_path):
                new_filename = f"{base}_{counter}{ext}"
                dest_path = os.path.join(folder_path, new_filename)
                counter += 1

        # Move/copy file
        shutil.move(source_path, dest_path)

        # Return relative path for storage
        return os.path.relpath(dest_path, self.processed_folder)

    def get_folder_structure(self):
        """Get the current folder structure as a tree"""
        tree = {}

        if not os.path.exists(self.processed_folder):
            return tree

        for year in sorted(os.listdir(self.processed_folder), reverse=True):
            year_path = os.path.join(self.processed_folder, year)
            if not os.path.isdir(year_path):
                continue

            tree[year] = {}

            for month in sorted(os.listdir(year_path), reverse=True):
                month_path = os.path.join(year_path, month)
                if not os.path.isdir(month_path):
                    continue

                tree[year][month] = {}

                for vendor in sorted(os.listdir(month_path)):
                    vendor_path = os.path.join(month_path, vendor)
                    if not os.path.isdir(vendor_path):
                        continue

                    files = [f for f in os.listdir(vendor_path) if os.path.isfile(os.path.join(vendor_path, f))]
                    tree[year][month][vendor] = {
                        'count': len(files),
                        'files': sorted(files, reverse=True)
                    }

        return tree

    def get_file_stats(self):
        """Get statistics about organized files"""
        stats = {
            'total_files': 0,
            'total_vendors': set(),
            'years': {},
        }

        if not os.path.exists(self.processed_folder):
            return stats

        for year in os.listdir(self.processed_folder):
            year_path = os.path.join(self.processed_folder, year)
            if not os.path.isdir(year_path):
                continue

            year_count = 0

            for month in os.listdir(year_path):
                month_path = os.path.join(year_path, month)
                if not os.path.isdir(month_path):
                    continue

                for vendor in os.listdir(month_path):
                    vendor_path = os.path.join(month_path, vendor)
                    if not os.path.isdir(vendor_path):
                        continue

                    stats['total_vendors'].add(vendor)
                    files = [f for f in os.listdir(vendor_path) if os.path.isfile(os.path.join(vendor_path, f))]
                    file_count = len(files)
                    year_count += file_count
                    stats['total_files'] += file_count

            stats['years'][year] = year_count

        stats['total_vendors'] = len(stats['total_vendors'])

        return stats
