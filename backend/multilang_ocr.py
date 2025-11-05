import os
import subprocess
import json
from PIL import Image
import pytesseract

class MultiLanguageOCR:
    """Support for multiple languages in OCR"""

    # Supported Tesseract languages
    SUPPORTED_LANGUAGES = {
        'eng': {'name': 'English', 'code': 'eng'},
        'spa': {'name': 'Spanish', 'code': 'spa'},
        'fra': {'name': 'French', 'code': 'fra'},
        'deu': {'name': 'German', 'code': 'deu'},
        'ita': {'name': 'Italian', 'code': 'ita'},
        'por': {'name': 'Portuguese', 'code': 'por'},
        'nld': {'name': 'Dutch', 'code': 'nld'},
        'rus': {'name': 'Russian', 'code': 'rus'},
        'jpn': {'name': 'Japanese', 'code': 'jpn'},
        'chi_sim': {'name': 'Chinese (Simplified)', 'code': 'chi_sim'},
        'chi_tra': {'name': 'Chinese (Traditional)', 'code': 'chi_tra'},
        'kor': {'name': 'Korean', 'code': 'kor'},
        'ara': {'name': 'Arabic', 'code': 'ara'},
        'hin': {'name': 'Hindi', 'code': 'hin'},
        'pol': {'name': 'Polish', 'code': 'pol'},
        'ukr': {'name': 'Ukrainian', 'code': 'ukr'},
        'vie': {'name': 'Vietnamese', 'code': 'vie'},
        'tha': {'name': 'Thai', 'code': 'tha'},
    }

    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.settings_file = os.path.join(data_folder, 'ocr_settings.json')
        self.settings = self.load_settings()
        self.available_languages = self.detect_installed_languages()

    def load_settings(self):
        """Load OCR settings"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self.get_default_settings()
        return self.get_default_settings()

    def get_default_settings(self):
        """Get default OCR settings"""
        return {
            'default_language': 'eng',
            'auto_detect_language': True,
            'multi_language_mode': False,
            'languages': ['eng'],  # Languages to use in multi-language mode
            'ocr_engine_mode': '3',  # 0=Legacy, 1=LSTM, 2=Legacy+LSTM, 3=Default
            'page_segmentation_mode': '3',  # Fully automatic page segmentation
        }

    def save_settings(self):
        """Save OCR settings"""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)

    def update_settings(self, new_settings):
        """Update OCR settings"""
        self.settings.update(new_settings)
        self.save_settings()

    def detect_installed_languages(self):
        """Detect which Tesseract languages are installed"""
        try:
            # Run tesseract --list-langs
            result = subprocess.run(
                ['tesseract', '--list-langs'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Parse output
                lines = result.stdout.split('\n')
                installed = []

                for line in lines:
                    line = line.strip()
                    if line and line in self.SUPPORTED_LANGUAGES:
                        installed.append(line)

                return installed
            else:
                # Fallback to English only
                return ['eng']

        except Exception as e:
            print(f"Error detecting languages: {e}")
            return ['eng']

    def get_available_languages(self):
        """Get list of available languages"""
        languages = []

        for code in self.available_languages:
            if code in self.SUPPORTED_LANGUAGES:
                lang_info = self.SUPPORTED_LANGUAGES[code].copy()
                lang_info['installed'] = True
                languages.append(lang_info)

        # Add languages not installed
        for code, info in self.SUPPORTED_LANGUAGES.items():
            if code not in self.available_languages:
                lang_info = info.copy()
                lang_info['installed'] = False
                languages.append(lang_info)

        return languages

    def extract_with_language(self, image, language='eng', config=None):
        """
        Extract text using specified language
        image: PIL Image object
        language: language code (e.g., 'eng', 'spa', 'fra')
        """
        if language not in self.available_languages:
            print(f"Warning: Language '{language}' not installed. Falling back to English.")
            language = 'eng'

        # Build tesseract config
        if config is None:
            config = f'--oem {self.settings["ocr_engine_mode"]} --psm {self.settings["page_segmentation_mode"]}'

        try:
            text = pytesseract.image_to_string(image, lang=language, config=config)
            return text
        except Exception as e:
            print(f"Error in OCR extraction: {e}")
            return ""

    def extract_multi_language(self, image, languages=None):
        """
        Extract text using multiple languages
        Useful for documents with mixed languages
        """
        if languages is None:
            languages = self.settings['languages']

        # Filter out languages that aren't installed
        valid_languages = [lang for lang in languages if lang in self.available_languages]

        if not valid_languages:
            valid_languages = ['eng']

        # Combine languages with + separator for Tesseract
        lang_string = '+'.join(valid_languages)

        config = f'--oem {self.settings["ocr_engine_mode"]} --psm {self.settings["page_segmentation_mode"]}'

        try:
            text = pytesseract.image_to_string(image, lang=lang_string, config=config)
            return text
        except Exception as e:
            print(f"Error in multi-language OCR: {e}")
            # Fallback to single language
            return self.extract_with_language(image, valid_languages[0])

    def detect_language(self, image):
        """
        Auto-detect language in document
        Uses OSD (Orientation and Script Detection)
        """
        try:
            # Use Tesseract's OSD feature
            osd = pytesseract.image_to_osd(image)

            # Parse OSD output
            script_line = [line for line in osd.split('\n') if 'Script:' in line]

            if script_line:
                script = script_line[0].split(':')[1].strip()

                # Map script to likely language
                script_to_lang = {
                    'Latin': 'eng',
                    'Arabic': 'ara',
                    'Cyrillic': 'rus',
                    'Han': 'chi_sim',
                    'Hangul': 'kor',
                    'Hiragana': 'jpn',
                    'Katakana': 'jpn',
                }

                detected_lang = script_to_lang.get(script, 'eng')
                return detected_lang, 80  # Confidence

            return 'eng', 50

        except Exception as e:
            print(f"Language detection error: {e}")
            return 'eng', 30

    def extract_auto(self, image):
        """
        Automatically detect language and extract text
        """
        if self.settings['auto_detect_language']:
            detected_lang, confidence = self.detect_language(image)
            print(f"Detected language: {detected_lang} (confidence: {confidence}%)")

            return self.extract_with_language(image, detected_lang)

        elif self.settings['multi_language_mode']:
            return self.extract_multi_language(image)

        else:
            return self.extract_with_language(image, self.settings['default_language'])

    def get_language_name(self, code):
        """Get language name from code"""
        if code in self.SUPPORTED_LANGUAGES:
            return self.SUPPORTED_LANGUAGES[code]['name']
        return code

    def validate_language(self, code):
        """Check if language is valid and installed"""
        return code in self.available_languages

    def get_installation_instructions(self, language_code):
        """Get instructions for installing a Tesseract language"""
        lang_name = self.get_language_name(language_code)

        instructions = {
            'ubuntu': f"sudo apt-get install tesseract-ocr-{language_code}",
            'macos': f"brew install tesseract-lang",
            'windows': "Download language data from https://github.com/tesseract-ocr/tessdata",
            'manual': f"Download {language_code}.traineddata and place in Tesseract's tessdata folder"
        }

        return {
            'language': lang_name,
            'code': language_code,
            'instructions': instructions
        }

    def get_config_info(self):
        """Get current OCR configuration"""
        oem_modes = {
            '0': 'Legacy engine only',
            '1': 'Neural nets LSTM engine only',
            '2': 'Legacy + LSTM engines',
            '3': 'Default, based on what is available'
        }

        psm_modes = {
            '0': 'Orientation and script detection (OSD) only',
            '1': 'Automatic page segmentation with OSD',
            '2': 'Automatic page segmentation (no OSD)',
            '3': 'Fully automatic page segmentation (default)',
            '4': 'Assume a single column of text',
            '5': 'Assume a single uniform block of vertically aligned text',
            '6': 'Assume a single uniform block of text',
            '7': 'Treat image as single text line',
            '8': 'Treat image as single word',
            '9': 'Treat image as single word in a circle',
            '10': 'Treat image as single character',
            '11': 'Sparse text (find as much text as possible)',
            '12': 'Sparse text with OSD',
            '13': 'Raw line (treat image as single text line, bypassing hacks)'
        }

        oem = self.settings['ocr_engine_mode']
        psm = self.settings['page_segmentation_mode']

        return {
            'engine_mode': {
                'value': oem,
                'description': oem_modes.get(oem, 'Unknown')
            },
            'segmentation_mode': {
                'value': psm,
                'description': psm_modes.get(psm, 'Unknown')
            },
            'default_language': self.settings['default_language'],
            'auto_detect': self.settings['auto_detect_language'],
            'multi_language': self.settings['multi_language_mode'],
            'active_languages': self.settings['languages']
        }

    def benchmark_languages(self, image, languages=None):
        """
        Test OCR with different languages and return results
        Useful for comparing accuracy
        """
        if languages is None:
            languages = self.available_languages[:5]  # Test first 5

        results = []

        for lang in languages:
            if lang not in self.available_languages:
                continue

            try:
                import time
                start_time = time.time()

                text = self.extract_with_language(image, lang)

                processing_time = time.time() - start_time

                results.append({
                    'language': lang,
                    'language_name': self.get_language_name(lang),
                    'text_length': len(text),
                    'processing_time': processing_time,
                    'preview': text[:200] if len(text) > 200 else text
                })

            except Exception as e:
                results.append({
                    'language': lang,
                    'language_name': self.get_language_name(lang),
                    'error': str(e)
                })

        return results
