import json
import os
import re
from datetime import datetime, timedelta

class CurrencyManager:
    """Handle multi-currency detection, conversion, and management"""

    # Major currencies with their symbols and patterns
    CURRENCIES = {
        'USD': {'symbol': '$', 'name': 'US Dollar', 'pattern': r'\$\s*(\d+[,.]?\d*\.?\d{2})'},
        'EUR': {'symbol': '€', 'name': 'Euro', 'pattern': r'€\s*(\d+[,.]?\d*\.?\d{2})'},
        'GBP': {'symbol': '£', 'name': 'British Pound', 'pattern': r'£\s*(\d+[,.]?\d*\.?\d{2})'},
        'JPY': {'symbol': '¥', 'name': 'Japanese Yen', 'pattern': r'¥\s*(\d+[,.]?\d*)'},
        'CAD': {'symbol': 'C$', 'name': 'Canadian Dollar', 'pattern': r'C\$\s*(\d+[,.]?\d*\.?\d{2})'},
        'AUD': {'symbol': 'A$', 'name': 'Australian Dollar', 'pattern': r'A\$\s*(\d+[,.]?\d*\.?\d{2})'},
        'CHF': {'symbol': 'CHF', 'name': 'Swiss Franc', 'pattern': r'CHF\s*(\d+[,.]?\d*\.?\d{2})'},
        'CNY': {'symbol': '¥', 'name': 'Chinese Yuan', 'pattern': r'CNY\s*(\d+[,.]?\d*\.?\d{2})'},
        'INR': {'symbol': '₹', 'name': 'Indian Rupee', 'pattern': r'₹\s*(\d+[,.]?\d*\.?\d{2})'},
        'MXN': {'symbol': 'MX$', 'name': 'Mexican Peso', 'pattern': r'MX\$\s*(\d+[,.]?\d*\.?\d{2})'},
    }

    # Static exchange rates (fallback - in production, use live API)
    FALLBACK_RATES = {
        'EUR': 1.10,
        'GBP': 1.27,
        'JPY': 0.0067,
        'CAD': 0.73,
        'AUD': 0.65,
        'CHF': 1.13,
        'CNY': 0.14,
        'INR': 0.012,
        'MXN': 0.058,
    }

    def __init__(self, data_folder, base_currency='USD'):
        self.data_folder = data_folder
        self.base_currency = base_currency
        self.rates_file = os.path.join(data_folder, 'exchange_rates.json')
        self.exchange_rates = self.load_exchange_rates()

    def load_exchange_rates(self):
        """Load exchange rates from file or use fallback"""
        if os.path.exists(self.rates_file):
            try:
                with open(self.rates_file, 'r') as f:
                    data = json.load(f)
                    # Check if rates are recent (within 24 hours)
                    last_update = datetime.fromisoformat(data.get('last_update', '2000-01-01'))
                    if datetime.now() - last_update < timedelta(hours=24):
                        return data
            except (json.JSONDecodeError, ValueError):
                pass

        # Use fallback rates
        return {
            'base': self.base_currency,
            'rates': self.FALLBACK_RATES.copy(),
            'last_update': datetime.now().isoformat(),
            'source': 'fallback'
        }

    def save_exchange_rates(self):
        """Save exchange rates to file"""
        with open(self.rates_file, 'w') as f:
            json.dump(self.exchange_rates, f, indent=2)

    def detect_currency(self, text):
        """
        Detect currency from document text
        Returns currency code and confidence
        """
        currency_matches = {}

        for code, info in self.CURRENCIES.items():
            # Check for currency symbol
            if info['symbol'] in text:
                currency_matches[code] = currency_matches.get(code, 0) + 3

            # Check for currency code (e.g., "USD", "EUR")
            if code in text:
                currency_matches[code] = currency_matches.get(code, 0) + 2

            # Check for currency name
            if info['name'].lower() in text.lower():
                currency_matches[code] = currency_matches.get(code, 0) + 1

        # Default to base currency if no match
        if not currency_matches:
            return self.base_currency, 50

        # Return currency with highest score
        best_currency = max(currency_matches.items(), key=lambda x: x[1])
        confidence = min(95, 60 + (best_currency[1] * 10))

        return best_currency[0], confidence

    def extract_amount_with_currency(self, text):
        """
        Extract amount and currency from text
        Returns (amount, currency, confidence)
        """
        best_match = None
        best_confidence = 0

        for code, info in self.CURRENCIES.items():
            pattern = info['pattern']
            matches = re.finditer(pattern, text)

            for match in matches:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)

                    # Reasonable amount range
                    if 0 < amount < 1000000:
                        # Calculate confidence based on context
                        context = text[max(0, match.start()-20):match.end()+20].lower()
                        confidence = 70

                        if any(keyword in context for keyword in ['total', 'amount', 'due', 'balance']):
                            confidence += 20

                        if confidence > best_confidence:
                            best_match = (amount, code, confidence)
                            best_confidence = confidence

                except (ValueError, IndexError):
                    continue

        # If no pattern match, try to detect currency separately
        if not best_match:
            currency, curr_conf = self.detect_currency(text)
            # Try basic amount extraction
            amounts = re.findall(r'(\d+[,.]?\d*\.?\d{2})', text)
            if amounts:
                try:
                    amount = float(amounts[-1].replace(',', ''))  # Take last (often total)
                    if 0 < amount < 1000000:
                        return amount, currency, min(curr_conf, 60)
                except ValueError:
                    pass

            return 0, self.base_currency, 30

        return best_match

    def convert_to_base(self, amount, from_currency):
        """
        Convert amount from foreign currency to base currency
        """
        if from_currency == self.base_currency:
            return amount

        rate = self.exchange_rates['rates'].get(from_currency)
        if not rate:
            # If rate not found, return original
            return amount

        # Convert to base currency (USD)
        if self.base_currency == 'USD':
            return amount * rate
        else:
            # Convert through USD
            usd_amount = amount * rate
            base_rate = self.exchange_rates['rates'].get(self.base_currency, 1)
            return usd_amount / base_rate

    def convert_currency(self, amount, from_currency, to_currency):
        """
        Convert amount between any two currencies
        """
        if from_currency == to_currency:
            return amount

        # Convert to USD first, then to target
        if from_currency != 'USD':
            rate = self.exchange_rates['rates'].get(from_currency, 1)
            amount = amount * rate

        # Convert from USD to target
        if to_currency != 'USD':
            rate = self.exchange_rates['rates'].get(to_currency, 1)
            amount = amount / rate

        return amount

    def format_amount(self, amount, currency):
        """
        Format amount with currency symbol
        """
        symbol = self.CURRENCIES.get(currency, {}).get('symbol', currency)

        # Format based on currency
        if currency == 'JPY':
            # No decimals for Yen
            return f"{symbol}{int(amount):,}"
        else:
            return f"{symbol}{amount:,.2f}"

    def get_supported_currencies(self):
        """Get list of supported currencies"""
        return [
            {
                'code': code,
                'name': info['name'],
                'symbol': info['symbol']
            }
            for code, info in self.CURRENCIES.items()
        ]

    def update_exchange_rates(self, rates_data=None):
        """
        Update exchange rates
        In production, this would fetch from an API like exchangerate-api.com
        """
        if rates_data:
            self.exchange_rates = {
                'base': self.base_currency,
                'rates': rates_data,
                'last_update': datetime.now().isoformat(),
                'source': 'manual'
            }
        else:
            # Simulate API update (in production, use real API)
            self.exchange_rates['last_update'] = datetime.now().isoformat()
            self.exchange_rates['source'] = 'simulated'

        self.save_exchange_rates()

    def get_exchange_rate_info(self):
        """Get current exchange rate information"""
        return {
            'base_currency': self.exchange_rates['base'],
            'last_update': self.exchange_rates['last_update'],
            'source': self.exchange_rates.get('source', 'unknown'),
            'currencies_count': len(self.exchange_rates['rates'])
        }

    def validate_currency_code(self, code):
        """Check if currency code is supported"""
        return code in self.CURRENCIES

    def get_currency_info(self, code):
        """Get information about a specific currency"""
        if code in self.CURRENCIES:
            info = self.CURRENCIES[code].copy()
            info['code'] = code
            if code in self.exchange_rates['rates']:
                info['exchange_rate'] = self.exchange_rates['rates'][code]
            return info
        return None
