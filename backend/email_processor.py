import imaplib
import email
from email.header import decode_header
import os
import json
from datetime import datetime
import time
import threading

class EmailProcessor:
    """Monitor email for forwarded invoices and process them automatically"""

    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.settings_file = os.path.join(data_folder, 'email_settings.json')
        self.settings = self.load_settings()
        self.is_running = False
        self.monitor_thread = None

    def load_settings(self):
        """Load email settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.get_default_settings()
        return self.get_default_settings()

    def get_default_settings(self):
        """Get default email settings"""
        return {
            'enabled': False,
            'server': '',  # e.g., imap.gmail.com
            'port': 993,
            'email': '',
            'password': '',  # App password recommended
            'folder': 'INBOX',
            'check_interval': 300,  # 5 minutes
            'auto_process': True,
            'subject_filters': ['invoice', 'receipt', 'bill'],
            'sender_whitelist': [],  # Only process from these senders (empty = all)
            'delete_after_process': False,
            'mark_as_read': True
        }

    def save_settings(self):
        """Save email settings"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def update_settings(self, new_settings):
        """Update email settings"""
        self.settings.update(new_settings)
        self.save_settings()

    def test_connection(self):
        """Test email connection"""
        try:
            mail = imaplib.IMAP4_SSL(self.settings['server'], self.settings['port'])
            mail.login(self.settings['email'], self.settings['password'])
            mail.select(self.settings['folder'])
            mail.logout()
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def connect(self):
        """Connect to email server"""
        mail = imaplib.IMAP4_SSL(self.settings['server'], self.settings['port'])
        mail.login(self.settings['email'], self.settings['password'])
        return mail

    def check_for_invoices(self):
        """Check email for new invoices"""
        if not self.settings['enabled']:
            return []

        try:
            mail = self.connect()
            mail.select(self.settings['folder'])

            # Build search criteria
            search_criteria = 'UNSEEN' if self.settings['mark_as_read'] else 'ALL'

            # Search for emails
            status, messages = mail.search(None, search_criteria)

            if status != 'OK':
                mail.logout()
                return []

            email_ids = messages[0].split()

            found_invoices = []

            for email_id in email_ids:
                # Fetch the email
                status, msg_data = mail.fetch(email_id, '(RFC822)')

                if status != 'OK':
                    continue

                # Parse email
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Get subject
                subject = self.decode_subject(msg.get('Subject', ''))

                # Get sender
                sender = msg.get('From', '')

                # Check if this email matches our filters
                if not self.should_process_email(subject, sender):
                    continue

                # Extract attachments
                attachments = self.extract_attachments(msg, email_id.decode())

                if attachments:
                    invoice_info = {
                        'email_id': email_id.decode(),
                        'subject': subject,
                        'sender': sender,
                        'date': msg.get('Date', ''),
                        'attachments': attachments
                    }
                    found_invoices.append(invoice_info)

                    # Mark as read if configured
                    if self.settings['mark_as_read']:
                        mail.store(email_id, '+FLAGS', '\\Seen')

            mail.logout()
            return found_invoices

        except Exception as e:
            print(f"Error checking email: {str(e)}")
            return []

    def decode_subject(self, subject):
        """Decode email subject"""
        if not subject:
            return ""

        decoded_parts = decode_header(subject)
        decoded_subject = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_subject += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_subject += part

        return decoded_subject

    def should_process_email(self, subject, sender):
        """Check if email should be processed based on filters"""
        # Check sender whitelist
        if self.settings['sender_whitelist']:
            sender_match = False
            for allowed_sender in self.settings['sender_whitelist']:
                if allowed_sender.lower() in sender.lower():
                    sender_match = True
                    break

            if not sender_match:
                return False

        # Check subject filters
        subject_lower = subject.lower()
        subject_match = False

        for filter_word in self.settings['subject_filters']:
            if filter_word.lower() in subject_lower:
                subject_match = True
                break

        return subject_match

    def extract_attachments(self, msg, email_id):
        """Extract attachments from email"""
        attachments = []
        temp_folder = os.path.join('uploads', 'email_temp')
        os.makedirs(temp_folder, exist_ok=True)

        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue

            if part.get('Content-Disposition') is None:
                continue

            filename = part.get_filename()

            if not filename:
                continue

            # Check if file type is allowed
            allowed_extensions = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff']
            file_ext = filename.rsplit('.', 1)[-1].lower()

            if file_ext not in allowed_extensions:
                continue

            # Save attachment
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"email_{email_id}_{timestamp}_{filename}"
            filepath = os.path.join(temp_folder, unique_filename)

            with open(filepath, 'wb') as f:
                f.write(part.get_payload(decode=True))

            attachments.append({
                'original_filename': filename,
                'saved_filename': unique_filename,
                'filepath': filepath,
                'size': os.path.getsize(filepath)
            })

        return attachments

    def start_monitoring(self, process_callback=None):
        """Start monitoring email in background"""
        if self.is_running:
            return False, "Monitoring already running"

        if not self.settings['enabled']:
            return False, "Email monitoring is disabled"

        # Test connection first
        success, message = self.test_connection()
        if not success:
            return False, message

        self.is_running = True
        self.process_callback = process_callback

        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        return True, "Email monitoring started"

    def stop_monitoring(self):
        """Stop monitoring email"""
        self.is_running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        return True, "Email monitoring stopped"

    def _monitor_loop(self):
        """Background loop for monitoring email"""
        print(f"Email monitoring started. Checking every {self.settings['check_interval']} seconds...")

        while self.is_running:
            try:
                # Check for new invoices
                invoices = self.check_for_invoices()

                if invoices and self.process_callback:
                    # Process each invoice
                    for invoice in invoices:
                        try:
                            self.process_callback(invoice)
                        except Exception as e:
                            print(f"Error processing invoice from email: {str(e)}")

                # Sleep for configured interval
                time.sleep(self.settings['check_interval'])

            except Exception as e:
                print(f"Error in email monitor loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying

    def get_status(self):
        """Get monitoring status"""
        return {
            'enabled': self.settings['enabled'],
            'running': self.is_running,
            'email': self.settings['email'],
            'server': self.settings['server'],
            'check_interval': self.settings['check_interval'],
            'auto_process': self.settings['auto_process']
        }

    def get_processing_instructions(self):
        """Get instructions for users on how to forward invoices"""
        forward_email = self.settings['email']

        instructions = f"""
# Email Forwarding Instructions

To automatically process invoices and receipts, simply forward them to:

**{forward_email}**

## Tips for Best Results:

1. **Subject Line**: Include keywords like "invoice", "receipt", or "bill"
2. **Attachments**: Attach PDF or image files of your invoices
3. **Format**: PDF, PNG, JPG, JPEG formats work best
4. **Quality**: Ensure documents are clear and readable

## Processing:

- Emails are checked every {self.settings['check_interval'] // 60} minutes
- Documents are automatically extracted and categorized
- You'll find processed invoices in your expenses

## Security:

- Only attachments are processed
- Email content is not stored
- Configure sender whitelist for additional security
"""

        return instructions
