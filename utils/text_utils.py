"""
Text Utilities Module

This module provides utility functions for text processing and manipulation.
It includes various text cleaning, formatting, and analysis techniques.

Author: Kilo Code
Version: 1.0.0
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
import unicodedata

# Local imports
from errors.exceptions import TextProcessingError
from errors.handler import ErrorHandler


class TextUtils:
    """
    Utility class for text processing and manipulation.
    Provides various text cleaning, formatting, and analysis techniques.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize text utilities.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.error_handler = ErrorHandler()
        self.config = config or {}
        
        # Default settings
        self.default_settings = {
            'max_line_length': 80,
            'paragraph_spacing': 2,
            'table_alignment': 'left',
            'preserve_whitespace': True,
            'normalize_whitespace': True,
            'remove_extra_newlines': True,
            'clean_special_chars': True,
            'preserve_urls': True,
            'preserve_emails': True,
            'preserve_phone_numbers': True
        }
        
        # Merge with provided config
        if config:
            self.default_settings.update(config)
        
        # Common patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.phone_pattern = re.compile(
            r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        )
        self.table_pattern = re.compile(
            r'^(\|.*\|)\s*$'
        )
        self.header_pattern = re.compile(
            r'^#{1,6}\s+.+'
        )
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text to clean
            
        Returns:
            str: Cleaned text
        """
        try:
            if not text:
                return ""
            
            # Normalize Unicode characters
            text = unicodedata.normalize('NFKD', text)
            
            # Remove extra whitespace if enabled
            if self.default_settings.get('normalize_whitespace', True):
                text = ' '.join(text.split())
            
            # Clean special characters if enabled
            if self.default_settings.get('clean_special_chars', True):
                text = self._clean_special_characters(text)
            
            # Preserve URLs if enabled
            if self.default_settings.get('preserve_urls', True):
                text = self._preserve_urls(text)
            
            # Preserve emails if enabled
            if self.default_settings.get('preserve_emails', True):
                text = self._preserve_emails(text)
            
            # Preserve phone numbers if enabled
            if self.default_settings.get('preserve_phone_numbers', True):
                text = self._preserve_phone_numbers(text)
            
            return text
            
        except Exception as e:
            error_msg = f"Failed to clean text: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def _clean_special_characters(self, text: str) -> str:
        """Clean special characters from text."""
        # Remove control characters except common whitespace
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Replace multiple punctuation with single
        text = re.sub(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?~`]{2,}', ' ', text)
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text
    
    def _preserve_urls(self, text: str) -> str:
        """Preserve URLs in text."""
        def replace_url(match):
            url = match.group(0)
            return f'URL:{url}'
        
        return self.url_pattern.sub(replace_url, text)
    
    def _preserve_emails(self, text: str) -> str:
        """Preserve emails in text."""
        def replace_email(match):
            email = match.group(0)
            return f'EMAIL:{email}'
        
        return self.email_pattern.sub(replace_email, text)
    
    def _preserve_phone_numbers(self, text: str) -> str:
        """Preserve phone numbers in text."""
        def replace_phone(match):
            phone = match.group(0)
            return f'PHONE:{phone}'
        
        return self.phone_pattern.sub(replace_phone, text)
    
    def format_paragraphs(self, text: str) -> str:
        """
        Format text into paragraphs.
        
        Args:
            text: Input text to format
            
        Returns:
            str: Formatted text
        """
        try:
            if not text:
                return ""
            
            # Split into lines
            lines = text.split('\n')
            
            # Process each line
            formatted_lines = []
            current_paragraph = []
            
            for line in lines:
                line = line.strip()
                
                if line:
                    current_paragraph.append(line)
                else:
                    if current_paragraph:
                        paragraph = ' '.join(current_paragraph)
                        formatted_lines.append(paragraph)
                        current_paragraph = []
            
            # Add remaining paragraph
            if current_paragraph:
                paragraph = ' '.join(current_paragraph)
                formatted_lines.append(paragraph)
            
            # Join paragraphs with spacing
            spacing = self.default_settings.get('paragraph_spacing', 2)
            separator = '\n' + '\n' * spacing
            
            return separator.join(formatted_lines)
            
        except Exception as e:
            error_msg = f"Failed to format paragraphs: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def detect_headers(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect headers in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List[Dict]: List of detected headers
        """
        try:
            headers = []
            lines = text.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if self.header_pattern.match(line):
                    # Extract header level and text
                    match = re.match(r'^(#{1,6})\s+(.+)$', line)
                    if match:
                        level = len(match.group(1))
                        text = match.group(2).strip()
                        
                        headers.append({
                            'level': level,
                            'text': text,
                            'line_number': line_num,
                            'original_line': line
                        })
            
            return headers
            
        except Exception as e:
            error_msg = f"Failed to detect headers: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def detect_tables(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect tables in text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            List[Dict]: List of detected tables
        """
        try:
            tables = []
            lines = text.split('\n')
            
            current_table = None
            table_lines = []
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                if self.table_pattern.match(line):
                    if current_table is None:
                        # Start new table
                        current_table = {
                            'start_line': line_num,
                            'lines': [],
                            'rows': []
                        }
                    
                    table_lines.append(line)
                    current_table['lines'].append({
                        'line_number': line_num,
                        'content': line
                    })
                else:
                    if current_table is not None:
                        # End current table
                        current_table['rows'] = self._parse_table_lines(table_lines)
                        tables.append(current_table)
                        current_table = None
                        table_lines = []
            
            # Add any remaining table
            if current_table is not None:
                current_table['rows'] = self._parse_table_lines(table_lines)
                tables.append(current_table)
            
            return tables
            
        except Exception as e:
            error_msg = f"Failed to detect tables: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def _parse_table_lines(self, lines: List[str]) -> List[List[str]]:
        """Parse table lines into rows and columns."""
        rows = []
        
        for line in lines:
            # Remove leading and trailing pipes
            content = line.strip('|').strip()
            
            # Split by pipe and clean
            columns = [col.strip() for col in content.split('|')]
            
            # Remove empty columns
            columns = [col for col in columns if col]
            
            if columns:
                rows.append(columns)
        
        return rows
    
    def format_table(self, table_data: List[List[str]], alignment: str = None) -> str:
        """
        Format table data as markdown table.
        
        Args:
            table_data: Table data as list of rows
            alignment: Table alignment ('left', 'center', 'right')
            
        Returns:
            str: Formatted markdown table
        """
        try:
            if not table_data:
                return ""
            
            if alignment is None:
                alignment = self.default_settings.get('table_alignment', 'left')
            
            # Calculate column widths
            num_columns = max(len(row) for row in table_data)
            column_widths = [0] * num_columns
            
            for row in table_data:
                for i, cell in enumerate(row):
                    if i < num_columns:
                        column_widths[i] = max(column_widths[i], len(cell))
            
            # Format alignment row
            alignment_row = []
            for width in column_widths:
                if alignment == 'left':
                    align_str = ':' + '-' * (width - 1) if width > 1 else ':'
                elif alignment == 'right':
                    align_str = '-' * (width - 1) + ':' if width > 1 else ':'
                else:  # center
                    align_str = ':' + '-' * (width - 2) + ':' if width > 2 else '::'
                alignment_row.append(align_str)
            
            # Format rows
            formatted_rows = []
            
            # Header row
            if table_data:
                header_row = []
                for i, cell in enumerate(table_data[0]):
                    if i < num_columns:
                        header_row.append(cell.ljust(column_widths[i]))
                formatted_rows.append('| ' + ' | '.join(header_row) + ' |')
            
            # Alignment row
            formatted_rows.append('| ' + ' | '.join(alignment_row) + ' |')
            
            # Data rows
            for row in table_data[1:]:
                formatted_row = []
                for i, cell in enumerate(row):
                    if i < num_columns:
                        formatted_row.append(cell.ljust(column_widths[i]))
                formatted_rows.append('| ' + ' | '.join(formatted_row) + ' |')
            
            return '\n'.join(formatted_rows)
            
        except Exception as e:
            error_msg = f"Failed to format table: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def split_into_lines(self, text: str, max_length: int = None) -> List[str]:
        """
        Split text into lines with maximum length.
        
        Args:
            text: Input text to split
            max_length: Maximum line length
            
        Returns:
            List[str]: List of lines
        """
        try:
            if max_length is None:
                max_length = self.default_settings.get('max_line_length', 80)
            
            if not text:
                return []
            
            # Split into words
            words = text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                word_length = len(word)
                
                if current_length + word_length + len(current_line) <= max_length:
                    current_line.append(word)
                    current_length += word_length
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                        current_length = word_length
                    else:
                        # Word is too long, split it
                        lines.append(word[:max_length])
                        remaining = word[max_length:]
                        if remaining:
                            words.insert(words.index(word) + 1, remaining)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            return lines
            
        except Exception as e:
            error_msg = f"Failed to split text into lines: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def extract_keywords(self, text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text.
        
        Args:
            text: Input text to analyze
            min_length: Minimum keyword length
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List[str]: List of keywords
        """
        try:
            if not text:
                return []
            
            # Clean and normalize text
            text = self.clean_text(text)
            
            # Extract words
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            
            # Filter by length
            words = [word for word in words if len(word) >= min_length]
            
            # Count frequency
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Return top keywords
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
            
        except Exception as e:
            error_msg = f"Failed to extract keywords: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def calculate_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Calculate text statistics.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dict: Text statistics
        """
        try:
            if not text:
                return {
                    'character_count': 0,
                    'word_count': 0,
                    'sentence_count': 0,
                    'paragraph_count': 0,
                    'average_word_length': 0,
                    'average_sentence_length': 0,
                    'reading_time_minutes': 0
                }
            
            # Basic counts
            character_count = len(text)
            word_count = len(text.split())
            sentence_count = len(re.findall(r'[.!?]+', text))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
            
            # Calculate averages
            average_word_length = character_count / word_count if word_count > 0 else 0
            average_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
            
            # Estimate reading time (average reading speed: 200 words per minute)
            reading_time_minutes = word_count / 200
            
            return {
                'character_count': character_count,
                'word_count': word_count,
                'sentence_count': sentence_count,
                'paragraph_count': paragraph_count,
                'average_word_length': round(average_word_length, 2),
                'average_sentence_length': round(average_sentence_length, 2),
                'reading_time_minutes': round(reading_time_minutes, 2)
            }
            
        except Exception as e:
            error_msg = f"Failed to calculate text statistics: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Input text to normalize
            
        Returns:
            str: Normalized text
        """
        try:
            if not text:
                return ""
            
            # Replace multiple whitespace characters with single space
            text = re.sub(r'\s+', ' ', text)
            
            # Remove leading and trailing whitespace
            text = text.strip()
            
            return text
            
        except Exception as e:
            error_msg = f"Failed to normalize whitespace: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def remove_extra_newlines(self, text: str) -> str:
        """
        Remove extra newlines from text.
        
        Args:
            text: Input text to clean
            
        Returns:
            str: Cleaned text
        """
        try:
            if not text:
                return ""
            
            # Replace multiple newlines with single newline
            text = re.sub(r'\n\s*\n', '\n', text)
            
            # Remove leading and trailing newlines
            text = text.strip('\n')
            
            return text
            
        except Exception as e:
            error_msg = f"Failed to remove extra newlines: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def capitalize_sentences(self, text: str) -> str:
        """
        Capitalize sentences in text.
        
        Args:
            text: Input text to format
            
        Returns:
            str: Formatted text
        """
        try:
            if not text:
                return ""
            
            # Split into sentences
            sentences = re.split(r'([.!?]+)', text)
            
            # Process each sentence
            formatted_sentences = []
            for i in range(0, len(sentences), 2):
                if i + 1 < len(sentences):
                    sentence = sentences[i].strip()
                    punctuation = sentences[i + 1]
                    
                    if sentence:
                        # Capitalize first letter
                        sentence = sentence[0].upper() + sentence[1:]
                    
                    formatted_sentences.append(sentence + punctuation)
                else:
                    formatted_sentences.append(sentences[i])
            
            return ' '.join(formatted_sentences)
            
        except Exception as e:
            error_msg = f"Failed to capitalize sentences: {e}"
            self.error_handler.handle_text_processing_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update configuration.
        
        Args:
            config: New configuration
        """
        try:
            self.default_settings.update(config)
            self.logger.info("Text utilities configuration updated")
        except Exception as e:
            error_msg = f"Failed to update configuration: {e}"
            self.error_handler.handle_configuration_error(Exception(error_msg))
            raise TextProcessingError(error_msg)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dict: Current configuration
        """
        return self.default_settings.copy()