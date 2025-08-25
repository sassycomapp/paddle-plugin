"""
Default Settings Module

This module provides default configuration settings for the PNG to Markdown converter.
It includes environment-specific settings and user customization options.

Author: Kilo Code
Version: 1.0.0
"""

import os
from typing import Dict, Any, List, Optional

# Default configuration
DEFAULT_CONFIG = {
    "_description": "PNG to Markdown Converter Default Configuration",
    "_version": "1.0.0",
    "_generated_by": "ConfigurationManager",
    "_timestamp": "2025-01-01T00:00:00Z",
    
    "tesseract": {
        "path": None,
        "languages": ["eng"],
        "psm": 3,
        "oem": 3,
        "config": ""
    },
    
    "preprocessing": {
        "enabled": True,
        "max_size": 3000,
        "enhance_contrast": True,
        "remove_noise": True,
        "binarize": True,
        "sharpen": True,
        "deskew": True,
        "contrast_factor": 1.5,
        "brightness_factor": 1.1,
        "sharpen_factor": 1.0,
        "noise_reduction_radius": 1,
        "binarization_threshold": 128
    },
    
    "formatting": {
        "preserve_layout": True,
        "include_metadata": True,
        "include_statistics": True,
        "confidence_threshold": 0,
        "table_detection_threshold": 0.7,
        "column_detection_threshold": 0.6,
        "heading_detection_threshold": 0.8,
        "max_line_length": 80,
        "paragraph_spacing": 2,
        "table_alignment": "left"
    },
    
    "batch": {
        "size": 10,
        "timeout": 30,
        "retry_count": 3
    },
    
    "output": {
        "directory": "./output",
        "filename_pattern": "{original_name}_OCR.md",
        "include_backup": True
    },
    
    "logging": {
        "level": "INFO",
        "file": "./logs/converter.log",
        "max_size": "10MB",
        "backup_count": 5
    },
    
    "metadata": {
        "include_detailed_stats": True,
        "include_quality_metrics": True,
        "include_performance_metrics": True,
        "include_file_info": True,
        "include_processing_info": True
    },
    
    "validation": {
        "max_file_size": 104857600,
        "min_file_size": 1024,
        "max_image_width": 10000,
        "max_image_height": 10000,
        "supported_formats": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]
    }
}

# Production configuration
PRODUCTION_CONFIG = {
    "_description": "PNG to Markdown Converter Production Configuration",
    "_version": "1.0.0",
    "_generated_by": "ConfigurationManager",
    "_timestamp": "2025-01-01T00:00:00Z",
    
    "tesseract": {
        "path": "/usr/bin/tesseract",
        "languages": ["eng"],
        "psm": 3,
        "oem": 3,
        "config": "--oem 3 --psm 3"
    },
    
    "preprocessing": {
        "enabled": True,
        "max_size": 4000,
        "enhance_contrast": True,
        "remove_noise": True,
        "binarize": True,
        "sharpen": True,
        "deskew": True,
        "contrast_factor": 1.5,
        "brightness_factor": 1.1,
        "sharpen_factor": 1.0,
        "noise_reduction_radius": 1,
        "binarization_threshold": 128
    },
    
    "formatting": {
        "preserve_layout": True,
        "include_metadata": True,
        "include_statistics": True,
        "confidence_threshold": 70,
        "table_detection_threshold": 0.7,
        "column_detection_threshold": 0.6,
        "heading_detection_threshold": 0.8,
        "max_line_length": 80,
        "paragraph_spacing": 2,
        "table_alignment": "left"
    },
    
    "batch": {
        "size": 50,
        "timeout": 60,
        "retry_count": 5
    },
    
    "output": {
        "directory": "/data/output",
        "filename_pattern": "{original_name}_{timestamp}_converted.md",
        "include_backup": True
    },
    
    "logging": {
        "level": "WARNING",
        "file": "/var/log/png_to_markdown/converter.log",
        "max_size": "50MB",
        "backup_count": 10
    },
    
    "metadata": {
        "include_detailed_stats": True,
        "include_quality_metrics": True,
        "include_performance_metrics": True,
        "include_file_info": True,
        "include_processing_info": True
    },
    
    "validation": {
        "max_file_size": 524288000,  # 500MB
        "min_file_size": 1024,
        "max_image_width": 20000,
        "max_image_height": 20000,
        "supported_formats": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]
    }
}

# Development configuration
DEVELOPMENT_CONFIG = {
    "_description": "PNG to Markdown Converter Development Configuration",
    "_version": "1.0.0",
    "_generated_by": "ConfigurationManager",
    "_timestamp": "2025-01-01T00:00:00Z",
    
    "tesseract": {
        "path": None,
        "languages": ["eng"],
        "psm": 3,
        "oem": 3,
        "config": ""
    },
    
    "preprocessing": {
        "enabled": True,
        "max_size": 2000,
        "enhance_contrast": True,
        "remove_noise": True,
        "binarize": True,
        "sharpen": True,
        "deskew": True,
        "contrast_factor": 1.5,
        "brightness_factor": 1.1,
        "sharpen_factor": 1.0,
        "noise_reduction_radius": 1,
        "binarization_threshold": 128
    },
    
    "formatting": {
        "preserve_layout": True,
        "include_metadata": True,
        "include_statistics": True,
        "confidence_threshold": 0,
        "table_detection_threshold": 0.7,
        "column_detection_threshold": 0.6,
        "heading_detection_threshold": 0.8,
        "max_line_length": 80,
        "paragraph_spacing": 2,
        "table_alignment": "left"
    },
    
    "batch": {
        "size": 5,
        "timeout": 30,
        "retry_count": 2
    },
    
    "output": {
        "directory": "./dev_output",
        "filename_pattern": "{original_name}_OCR.md",
        "include_backup": True
    },
    
    "logging": {
        "level": "DEBUG",
        "file": "./dev_logs/converter.log",
        "max_size": "5MB",
        "backup_count": 3
    },
    
    "metadata": {
        "include_detailed_stats": True,
        "include_quality_metrics": True,
        "include_performance_metrics": True,
        "include_file_info": True,
        "include_processing_info": True
    },
    
    "validation": {
        "max_file_size": 52428800,  # 50MB
        "min_file_size": 1024,
        "max_image_width": 5000,
        "max_image_height": 5000,
        "supported_formats": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]
    }
}

# Testing configuration
TESTING_CONFIG = {
    "_description": "PNG to Markdown Converter Testing Configuration",
    "_version": "1.0.0",
    "_generated_by": "ConfigurationManager",
    "_timestamp": "2025-01-01T00:00:00Z",
    
    "tesseract": {
        "path": None,
        "languages": ["eng"],
        "psm": 3,
        "oem": 3,
        "config": ""
    },
    
    "preprocessing": {
        "enabled": True,
        "max_size": 1000,
        "enhance_contrast": True,
        "remove_noise": True,
        "binarize": True,
        "sharpen": True,
        "deskew": True,
        "contrast_factor": 1.5,
        "brightness_factor": 1.1,
        "sharpen_factor": 1.0,
        "noise_reduction_radius": 1,
        "binarization_threshold": 128
    },
    
    "formatting": {
        "preserve_layout": True,
        "include_metadata": True,
        "include_statistics": True,
        "confidence_threshold": 0,
        "table_detection_threshold": 0.7,
        "column_detection_threshold": 0.6,
        "heading_detection_threshold": 0.8,
        "max_line_length": 80,
        "paragraph_spacing": 2,
        "table_alignment": "left"
    },
    
    "batch": {
        "size": 3,
        "timeout": 10,
        "retry_count": 1
    },
    
    "output": {
        "directory": "./test_output",
        "filename_pattern": "{original_name}_OCR.md",
        "include_backup": False
    },
    
    "logging": {
        "level": "DEBUG",
        "file": "./test_logs/converter.log",
        "max_size": "1MB",
        "backup_count": 1
    },
    
    "metadata": {
        "include_detailed_stats": True,
        "include_quality_metrics": True,
        "include_performance_metrics": True,
        "include_file_info": True,
        "include_processing_info": True
    },
    
    "validation": {
        "max_file_size": 10485760,  # 10MB
        "min_file_size": 1024,
        "max_image_width": 2000,
        "max_image_height": 2000,
        "supported_formats": [".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".gif", ".webp"]
    }
}

# Tesseract configuration presets
TESSERACT_PRESETS = {
    "document": {
        "psm": 3,
        "oem": 3,
        "config": "--oem 3 --psm 3",
        "languages": ["eng"]
    },
    "single_column": {
        "psm": 4,
        "oem": 3,
        "config": "--oem 3 --psm 4",
        "languages": ["eng"]
    },
    "single_block": {
        "psm": 6,
        "oem": 3,
        "config": "--oem 3 --psm 6",
        "languages": ["eng"]
    },
    "sparse_text": {
        "psm": 11,
        "oem": 3,
        "config": "--oem 3 --psm 11",
        "languages": ["eng"]
    },
    "raw_line": {
        "psm": 13,
        "oem": 3,
        "config": "--oem 3 --psm 13",
        "languages": ["eng"]
    }
}

# Page segmentation modes
PSM_MODES = {
    0: "OSD Only",
    1: "Automatic page segmentation with OSD",
    2: "Automatic page segmentation, but no OSD, or OCR",
    3: "Fully automatic page segmentation, but no OSD",
    4: "Assume a single column of text of variable sizes",
    5: "Assume a single uniform block of vertically aligned text",
    6: "Assume a single uniform block of text",
    7: "Treat the image as a single text line",
    8: "Treat the image as a single word",
    9: "Treat the image as a single word in a circle",
    10: "Treat the image as a single character",
    11: "Sparse text. Find as much text as possible in no particular order",
    12: "Sparse text with OSD",
    13: "Raw line. Treat the image as a single text line",
    14: "Raw line, but with OSD"
}

# OCR engine modes
OEM_MODES = {
    0: "Legacy engine only",
    1: "Neural nets LSTM engine only",
    2: "Legacy + LSTM engines",
    3: "Default, based on what is available"
}

# Supported image formats
SUPPORTED_FORMATS = {
    ".png": "Portable Network Graphics",
    ".jpg": "Joint Photographic Experts Group",
    ".jpeg": "Joint Photographic Experts Group",
    ".tiff": "Tagged Image File Format",
    ".tif": "Tagged Image File Format",
    ".bmp": "Bitmap Image File",
    ".gif": "Graphics Interchange Format",
    ".webp": "Web Picture Format"
}

# Configuration templates
CONFIG_TEMPLATES = {
    "basic": {
        "tesseract": {
            "languages": ["eng"],
            "psm": 3,
            "oem": 3
        },
        "preprocessing": {
            "enabled": True,
            "max_size": 3000
        },
        "formatting": {
            "preserve_layout": True,
            "include_metadata": True
        }
    },
    "advanced": {
        "tesseract": {
            "languages": ["eng", "spa"],
            "psm": 3,
            "oem": 3,
            "config": "--oem 3 --psm 3"
        },
        "preprocessing": {
            "enabled": True,
            "max_size": 4000,
            "enhance_contrast": True,
            "remove_noise": True,
            "binarize": True,
            "sharpen": True,
            "deskew": True
        },
        "formatting": {
            "preserve_layout": True,
            "include_metadata": True,
            "include_statistics": True,
            "confidence_threshold": 70
        },
        "batch": {
            "size": 20,
            "timeout": 45,
            "retry_count": 3
        }
    },
    "minimal": {
        "tesseract": {
            "languages": ["eng"],
            "psm": 3,
            "oem": 3
        },
        "preprocessing": {
            "enabled": False
        },
        "formatting": {
            "preserve_layout": False,
            "include_metadata": False,
            "include_statistics": False
        }
    }
}

# Environment-specific configurations
ENVIRONMENT_CONFIGS = {
    "development": DEVELOPMENT_CONFIG,
    "dev": DEVELOPMENT_CONFIG,
    "testing": TESTING_CONFIG,
    "test": TESTING_CONFIG,
    "production": PRODUCTION_CONFIG,
    "prod": PRODUCTION_CONFIG,
    "default": DEFAULT_CONFIG
}

# Language codes for Tesseract
LANGUAGE_CODES = {
    "eng": "English",
    "spa": "Spanish",
    "fra": "French",
    "deu": "German",
    "ita": "Italian",
    "por": "Portuguese",
    "rus": "Russian",
    "chi_sim": "Chinese (Simplified)",
    "chi_tra": "Chinese (Traditional)",
    "jpn": "Japanese",
    "kor": "Korean",
    "ara": "Arabic",
    "hin": "Hindi",
    "tha": "Thai",
    "vie": "Vietnamese",
    "nld": "Dutch",
    "pol": "Polish",
    "tur": "Turkish",
    "ell": "Greek",
    "heb": "Hebrew",
    "urd": "Urdu",
    "ind": "Indonesian",
    "msa": "Malay",
    "nob": "Norwegian (Bokmål)",
    "nno": "Norwegian (Nynorsk)",
    "swe": "Swedish",
    "dan": "Danish",
    "fin": "Finnish",
    "isl": "Icelandic",
    "ces": "Czech",
    "slk": "Slovak",
    "bul": "Bulgarian",
    "hrv": "Croatian",
    "ron": "Romanian",
    "hun": "Hungarian",
    "srp": "Serbian",
    "ukr": "Ukrainian",
    "bel": "Belarusian",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "est": "Estonian",
    "gle": "Irish",
    "cym": "Welsh",
    "bre": "Breton",
    "oci": "Occitan",
    "cat": "Catalan",
    "eus": "Basque",
    "glg": "Galician",
    "ast": "Asturian",
    "gl": "Galician",
    "an": "Aragonese",
    "ca": "Catalan",
    "eu": "Basque",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "el": "Greek",
    "he": "Hebrew",
    "ur": "Urdu",
    "id": "Indonesian",
    "ms": "Malay",
    "nb": "Norwegian (Bokmål)",
    "nn": "Norwegian (Nynorsk)",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "is": "Icelandic",
    "cs": "Czech",
    "sk": "Slovak",
    "bg": "Bulgarian",
    "hr": "Croatian",
    "ro": "Romanian",
    "hu": "Hungarian",
    "sr": "Serbian",
    "uk": "Ukrainian",
    "be": "Belarusian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "et": "Estonian",
    "ga": "Irish",
    "cy": "Welsh",
    "br": "Breton",
    "oc": "Occitan"
}

# Configuration validation rules
VALIDATION_RULES = {
    "tesseract": {
        "path": {"type": "string", "required": False},
        "languages": {"type": "list", "required": True, "min_length": 1},
        "psm": {"type": "int", "required": False, "min": 0, "max": 14},
        "oem": {"type": "int", "required": False, "min": 0, "max": 3},
        "config": {"type": "string", "required": False}
    },
    "preprocessing": {
        "enabled": {"type": "bool", "required": False},
        "max_size": {"type": "int", "required": False, "min": 100, "max": 10000},
        "enhance_contrast": {"type": "bool", "required": False},
        "remove_noise": {"type": "bool", "required": False},
        "binarize": {"type": "bool", "required": False},
        "sharpen": {"type": "bool", "required": False},
        "deskew": {"type": "bool", "required": False},
        "contrast_factor": {"type": "float", "required": False, "min": 0.1, "max": 3.0},
        "brightness_factor": {"type": "float", "required": False, "min": 0.1, "max": 3.0},
        "sharpen_factor": {"type": "float", "required": False, "min": 0.1, "max": 3.0},
        "noise_reduction_radius": {"type": "int", "required": False, "min": 0, "max": 5},
        "binarization_threshold": {"type": "int", "required": False, "min": 0, "max": 255}
    },
    "formatting": {
        "preserve_layout": {"type": "bool", "required": False},
        "include_metadata": {"type": "bool", "required": False},
        "include_statistics": {"type": "bool", "required": False},
        "confidence_threshold": {"type": "int", "required": False, "min": 0, "max": 100},
        "table_detection_threshold": {"type": "float", "required": False, "min": 0.0, "max": 1.0},
        "column_detection_threshold": {"type": "float", "required": False, "min": 0.0, "max": 1.0},
        "heading_detection_threshold": {"type": "float", "required": False, "min": 0.0, "max": 1.0},
        "max_line_length": {"type": "int", "required": False, "min": 20, "max": 200},
        "paragraph_spacing": {"type": "int", "required": False, "min": 1, "max": 10},
        "table_alignment": {"type": "string", "required": False, "allowed_values": ["left", "center", "right"]}
    },
    "batch": {
        "size": {"type": "int", "required": False, "min": 1, "max": 1000},
        "timeout": {"type": "int", "required": False, "min": 1, "max": 300},
        "retry_count": {"type": "int", "required": False, "min": 0, "max": 10}
    },
    "output": {
        "directory": {"type": "string", "required": False},
        "filename_pattern": {"type": "string", "required": False},
        "include_backup": {"type": "bool", "required": False}
    },
    "logging": {
        "level": {"type": "string", "required": False, "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
        "file": {"type": "string", "required": False},
        "max_size": {"type": "string", "required", False},
        "backup_count": {"type": "int", "required": False, "min": 1, "max": 20}
    },
    "metadata": {
        "include_detailed_stats": {"type": "bool", "required": False},
        "include_quality_metrics": {"type": "bool", "required": False},
        "include_performance_metrics": {"type": "bool", "required": False},
        "include_file_info": {"type": "bool", "required": False},
        "include_processing_info": {"type": "bool", "required": False}
    },
    "validation": {
        "max_file_size": {"type": "int", "required": False, "min": 1024, "max": 1048576000},
        "min_file_size": {"type": "int", "required": False, "min": 1024, "max": 104857600},
        "max_image_width": {"type": "int", "required": False, "min": 100, "max": 50000},
        "max_image_height": {"type": "int", "required": False, "min": 100, "max": 50000},
        "supported_formats": {"type": "list", "required": False, "min_length": 1}
    }
}

# Utility functions
def get_default_config() -> Dict[str, Any]:
    """Get default configuration."""
    return DEFAULT_CONFIG.copy()

def get_production_config() -> Dict[str, Any]:
    """Get production configuration."""
    return PRODUCTION_CONFIG.copy()

def get_development_config() -> Dict[str, Any]:
    """Get development configuration."""
    return DEVELOPMENT_CONFIG.copy()

def get_testing_config() -> Dict[str, Any]:
    """Get testing configuration."""
    return TESTING_CONFIG.copy()

def get_environment_config(environment: str) -> Dict[str, Any]:
    """Get environment-specific configuration."""
    environment = environment.lower()
    return ENVIRONMENT_CONFIGS.get(environment, DEFAULT_CONFIG).copy()

def get_tesseract_preset(preset_name: str) -> Dict[str, Any]:
    """Get Tesseract configuration preset."""
    return TESSERACT_PRESETS.get(preset_name, TESSERACT_PRESETS["document"]).copy()

def get_psm_description(psm_code: int) -> str:
    """Get PSM description."""
    return PSM_MODES.get(psm_code, "Unknown PSM mode")

def get_oem_description(oem_code: int) -> str:
    """Get OEM description."""
    return OEM_MODES.get(oem_code, "Unknown OEM mode")

def get_supported_formats() -> Dict[str, str]:
    """Get supported image formats."""
    return SUPPORTED_FORMATS.copy()

def get_config_template(template_name: str) -> Dict[str, Any]:
    """Get configuration template."""
    return CONFIG_TEMPLATES.get(template_name, CONFIG_TEMPLATES["basic"]).copy()

def get_validation_rules() -> Dict[str, Any]:
    """Get configuration validation rules."""
    return VALIDATION_RULES.copy()

def get_language_description(language_code: str) -> str:
    """Get language description."""
    return LANGUAGE_CODES.get(language_code, "Unknown language")

def get_available_languages() -> List[str]:
    """Get list of available language codes."""
    return list(LANGUAGE_CODES.keys())

def get_available_presets() -> List[str]:
    """Get list of available Tesseract presets."""
    return list(TESSERACT_PRESETS.keys())

def get_available_templates() -> List[str]:
    """Get list of available configuration templates."""
    return list(CONFIG_TEMPLATES.keys())

def get_available_environments() -> List[str]:
    """Get list of available environment configurations."""
    return list(ENVIRONMENT_CONFIGS.keys())

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two configurations, with override_config taking precedence."""
    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    return deep_merge(base_config, override_config)

def validate_config_section(config: Dict[str, Any], section: str) -> Dict[str, Any]:
    """Validate a specific configuration section."""
    rules = VALIDATION_RULES.get(section, {})
    errors = []
    warnings = []
    
    for key, rule in rules.items():
        if key in config:
            value = config[key]
            
            # Check type
            if rule.get("type") == "int" and not isinstance(value, int):
                errors.append(f"{key} must be an integer")
            elif rule.get("type") == "float" and not isinstance(value, (int, float)):
                errors.append(f"{key} must be a float")
            elif rule.get("type") == "bool" and not isinstance(value, bool):
                errors.append(f"{key} must be a boolean")
            elif rule.get("type") == "string" and not isinstance(value, str):
                errors.append(f"{key} must be a string")
            elif rule.get("type") == "list" and not isinstance(value, list):
                errors.append(f"{key} must be a list")
            
            # Check min/max
            if rule.get("min") is not None and value < rule["min"]:
                errors.append(f"{key} must be at least {rule['min']}")
            if rule.get("max") is not None and value > rule["max"]:
                errors.append(f"{key} must be at most {rule['max']}")
            
            # Check allowed values
            if rule.get("allowed_values") and value not in rule["allowed_values"]:
                errors.append(f"{key} must be one of: {', '.join(rule['allowed_values'])}")
            
            # Check min length for lists
            if rule.get("min_length") and isinstance(value, list) and len(value) < rule["min_length"]:
                errors.append(f"{key} must have at least {rule['min_length']} items")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def get_config_diff(config1: Dict[str, Any], config2: Dict[str, Any]) -> Dict[str, Any]:
    """Get differences between two configurations."""
    def get_changes(base: Dict, override: Dict, path: str = "") -> Dict[str, Any]:
        changes = {}
        
        # Check keys in base
        for key, value in base.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in override:
                changes[current_path] = {'old': value, 'new': None, 'action': 'removed'}
            elif isinstance(value, dict) and isinstance(override[key], dict):
                changes.update(get_changes(value, override[key], current_path))
            elif value != override[key]:
                changes[current_path] = {
                    'old': value, 
                    'new': override[key], 
                    'action': 'modified'
                }
        
        # Check keys in override but not in base
        for key, value in override.items():
            current_path = f"{path}.{key}" if path else key
            
            if key not in base:
                changes[current_path] = {'old': None, 'new': value, 'action': 'added'}
        
        return changes
    
    return get_changes(config1, config2)