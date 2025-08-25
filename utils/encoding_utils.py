#!/usr/bin/env python3
"""
UTF-8 Encoding Utility Module

A simple utility module for detecting and configuring UTF-8 encoding.
"""

import os
import sys
import locale
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

logger = logging.getLogger(__name__)


class EncodingError(Exception):
    """Exception raised for encoding-related errors."""
    pass

class UTF8Encoder:
    """Simple UTF-8 encoding utility."""
    
    def __init__(self):
        self.original_encoding = sys.getdefaultencoding()
        self.original_locale = locale.getpreferredencoding()
        self.utf8_detected = False
        self.encoding_issues = []
        self._detect_current_encoding()
    
    def _detect_current_encoding(self) -> Dict[str, Any]:
        """Detect current system encoding."""
        detection_results = {
            'file_encoding': sys.getdefaultencoding(),
            'locale_encoding': locale.getpreferredencoding(),
            'stdout_encoding': sys.stdout.encoding,
            'stderr_encoding': sys.stderr.encoding,
            'filesystem_encoding': sys.getfilesystemencoding(),
            'utf8_compatible': True,
            'issues': []
        }
        
        encodings_to_check = [
            ('file_encoding', detection_results['file_encoding']),
            ('locale_encoding', detection_results['locale_encoding']),
            ('stdout_encoding', detection_results['stdout_encoding']),
            ('stderr_encoding', detection_results['stderr_encoding']),
            ('filesystem_encoding', detection_results['filesystem_encoding'])
        ]
        
        for encoding_type, encoding in encodings_to_check:
            if encoding and 'utf' not in encoding.lower():
                detection_results['utf8_compatible'] = False
                detection_results['issues'].append(
                    f"{encoding_type}: {encoding} (not UTF-8 compatible)"
                )
                self.encoding_issues.append(f"{encoding_type}: {encoding}")
        
        if detection_results['utf8_compatible']:
            logger.info("[OK] All encodings are UTF-8 compatible")
        else:
            logger.warning("[WARN] Encoding compatibility issues detected:")
            for issue in detection_results['issues']:
                logger.warning(f"   {issue}")
        
        return detection_results
    
    def configure_utf8_environment(self) -> bool:
        """Configure environment to use UTF-8 encoding."""
        logger.info("Configuring UTF-8 environment...")
        
        success = True
        actions_taken = []
        
        try:
            env_vars = {
                'PYTHONIOENCODING': 'utf-8',
                'LANG': 'en_US.UTF-8',
                'LC_ALL': 'en_US.UTF-8'
            }
            
            for var, value in env_vars.items():
                old_value = os.environ.get(var)
                os.environ[var] = value
                actions_taken.append(f"Set {var}={value}")
                if old_value:
                    logger.info(f"Updated {var}: {old_value} -> {value}")
                else:
                    logger.info(f"Set {var}: {value}")
            
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
                actions_taken.append("Set locale to en_US.UTF-8")
                logger.info("Locale set to en_US.UTF-8")
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
                    actions_taken.append("Set locale to C.UTF-8")
                    logger.info("Locale set to C.UTF-8")
                except locale.Error:
                    logger.warning("Could not set UTF-8 locale, continuing with system default")
            
            self.utf8_detected = True
            logger.info("[OK] UTF-8 environment configured successfully")
            
            for action in actions_taken:
                logger.info(f"   {action}")
                
        except Exception as e:
            logger.error(f"[FAIL] Failed to configure UTF-8 environment: {e}")
            success = False
        
        return success
    
    def safe_open(self, file_path: Union[str, Path], mode: str = 'r', 
                  encoding: str = 'utf-8', errors: str = 'replace', **kwargs):
        """Safely open a file with UTF-8 encoding."""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            return open(file_path, mode=mode, encoding=encoding, errors=errors, **kwargs)
        except UnicodeDecodeError as e:
            logger.warning(f"UTF-8 decode failed for {file_path}: {e}")
            
            fallback_encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            
            for fallback_encoding in fallback_encodings:
                try:
                    logger.info(f"Trying fallback encoding: {fallback_encoding}")
                    return open(file_path, mode=mode, encoding=fallback_encoding, **kwargs)
                except UnicodeDecodeError:
                    continue
            
            raise UnicodeError(f"Failed to decode {file_path} with any encoding")
    
    def safe_read_text(self, file_path: Union[str, Path], 
                      encoding: str = 'utf-8', errors: str = 'replace') -> str:
        """Safely read text from a file."""
        with self.safe_open(file_path, 'r', encoding, errors) as f:
            return f.read()
    
    def safe_write_text(self, file_path: Union[str, Path], content: str,
                       encoding: str = 'utf-8', errors: str = 'replace', **kwargs) -> None:
        """Safely write text to a file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'w', encoding=encoding, errors=errors, **kwargs) as f:
                f.write(content)
        except UnicodeEncodeError as e:
            raise EncodingError(f"Failed to write text to {file_path} with encoding {encoding}: {e}")
        except Exception as e:
            raise EncodingError(f"Failed to write text to {file_path}: {e}")
    
    def safe_write_bytes(self, file_path: Union[str, Path], content: bytes, **kwargs) -> None:
        """
        Safely write bytes to a file.
        
        Args:
            file_path: Path to the file
            content: Bytes content to write
            **kwargs: Additional arguments for open()
            
        Raises:
            EncodingError: If writing fails
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(file_path, 'wb', **kwargs) as f:
                f.write(content)
        except Exception as e:
            raise EncodingError(f"Failed to write bytes to {file_path}: {e}")
    
    def safe_json_load(self, file_path: Union[str, Path], 
                      encoding: str = 'utf-8', **kwargs) -> Any:
        """Safely load JSON from a file."""
        with self.safe_open(file_path, 'r', encoding) as f:
            import json
            return json.load(f, **kwargs)
    
    def safe_json_dump(self, data: Any, file_path: Union[str, Path],
                      encoding: str = 'utf-8', indent: int = 2, **kwargs) -> None:
        """Safely dump JSON to a file."""
        self.safe_write_text(file_path, '', encoding)
        with self.safe_open(file_path, 'w', encoding) as f:
            import json
            json.dump(data, f, indent=indent, ensure_ascii=False, **kwargs)
    
    def ascii_safe_print(self, *args, **kwargs) -> None:
        """Print with ASCII-safe characters."""
        # Simple ASCII replacements for common Unicode symbols
        replacements = {
            '✅': '[OK]',
            '❌': '[FAIL]',
            '⚠️': '[WARN]',
            '🎉': '[SUCCESS]',
            '🚨': '[CRITICAL]',
            '💡': '[INFO]',
            '📄': '[FILE]',
            '🔍': '[CHECK]',
            '⚙️': '[CONFIG]',
            '📊': '[DATA]',
            '🔧': '[TOOL]',
            '📁': '[DIR]',
            '📝': '[NOTE]',
            '🎯': '[TARGET]',
            '🔗': '[LINK]',
            '📋': '[LIST]',
        }
        
        # Convert args to strings and replace Unicode symbols
        converted_args = []
        for arg in args:
            arg_str = str(arg)
            for unicode_char, ascii_replacement in replacements.items():
                arg_str = arg_str.replace(unicode_char, ascii_replacement)
            converted_args.append(arg_str)
        
        # Print with converted arguments and handle encoding errors
        try:
            print(*converted_args, **kwargs)
        except UnicodeEncodeError:
            # If encoding fails, try to encode with ASCII and ignore errors
            ascii_args = []
            for arg in converted_args:
                if isinstance(arg, str):
                    ascii_args.append(arg.encode('ascii', errors='ignore').decode('ascii'))
                else:
                    ascii_args.append(str(arg))
            print(*ascii_args, **kwargs)

# Global instance
_encoder_instance = None

def get_encoder() -> UTF8Encoder:
    """Get or create the global encoder instance."""
    global _encoder_instance
    if _encoder_instance is None:
        _encoder_instance = UTF8Encoder()
    return _encoder_instance

def configure_utf8() -> bool:
    """Configure UTF-8 environment and return success status."""
    encoder = get_encoder()
    return encoder.configure_utf8_environment()

def safe_open(file_path, mode='r', encoding='utf-8', errors='replace', **kwargs):
    """Safely open a file with UTF-8 encoding."""
    encoder = get_encoder()
    return encoder.safe_open(file_path, mode, encoding, errors, **kwargs)

def safe_read_text(file_path, encoding='utf-8', errors='replace') -> str:
    """Safely read text from a file."""
    encoder = get_encoder()
    return encoder.safe_read_text(file_path, encoding, errors)

def safe_write_text(file_path, content, encoding='utf-8', errors='replace', **kwargs) -> None:
    """Safely write text to a file."""
    encoder = get_encoder()
    return encoder.safe_write_text(file_path, content, encoding, errors, **kwargs)

def safe_json_load(file_path, encoding='utf-8', **kwargs) -> Any:
    """Safely load JSON from a file."""
    encoder = get_encoder()
    return encoder.safe_json_load(file_path, encoding, **kwargs)

def safe_json_dump(data, file_path, encoding='utf-8', indent=2, **kwargs) -> None:
    """Safely dump JSON to a file."""
    encoder = get_encoder()
    return encoder.safe_json_dump(data, file_path, encoding, indent, **kwargs)

def safe_write_bytes(file_path, content, **kwargs) -> None:
    """Safely write bytes to a file."""
    encoder = get_encoder()
    return encoder.safe_write_bytes(file_path, content, **kwargs)

def ascii_safe_print(*args, **kwargs) -> None:
    """Print with ASCII-safe characters."""
    encoder = get_encoder()
    return encoder.ascii_safe_print(*args, **kwargs)