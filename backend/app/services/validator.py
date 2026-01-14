"""
Rule-based validation service for extracted document fields.
"""
import re
from typing import List, Dict, Any
from datetime import datetime

from app.schemas.document import DocumentType


def validate_aadhaar(fields: Dict[str, Any]) -> List[str]:
    """Validate Aadhaar card fields."""
    errors = []
    
    id_number = fields.get("id_number", {}).get("value", "")
    # Remove spaces and check format
    clean_id = re.sub(r'\s+', '', id_number)
    
    if not re.match(r'^\d{12}$', clean_id):
        errors.append("Aadhaar number must be exactly 12 digits")
    
    # Verhoeff algorithm check could be added here for production
    
    return errors


def validate_pan(fields: Dict[str, Any]) -> List[str]:
    """Validate PAN card fields."""
    errors = []
    
    id_number = fields.get("id_number", {}).get("value", "")
    clean_id = id_number.upper().strip()
    
    # PAN format: ABCDE1234F
    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', clean_id):
        errors.append("PAN number must be in format ABCDE1234F")
    
    return errors


def validate_voter_id(fields: Dict[str, Any]) -> List[str]:
    """Validate Voter ID fields."""
    errors = []
    
    id_number = fields.get("id_number", {}).get("value", "")
    clean_id = id_number.upper().strip()
    
    # Voter ID format: 3 letters + 7 digits (varies by state)
    if not re.match(r'^[A-Z]{3}\d{7}$', clean_id):
        errors.append("Voter ID format appears invalid")
    
    return errors


def validate_dob(fields: Dict[str, Any]) -> List[str]:
    """Validate date of birth field."""
    errors = []
    
    dob = fields.get("dob", {}).get("value", "")
    if not dob:
        return []
    
    # Try parsing various date formats
    date_formats = ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"]
    parsed_date = None
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(dob, fmt)
            break
        except ValueError:
            continue
    
    if parsed_date is None:
        errors.append(f"Could not parse date of birth: {dob}")
    elif parsed_date > datetime.now():
        errors.append("Date of birth cannot be in the future")
    elif parsed_date.year < 1900:
        errors.append("Date of birth year seems too old")
    
    return errors


def validate_name(fields: Dict[str, Any]) -> List[str]:
    """Validate name field."""
    errors = []
    
    name = fields.get("name", {}).get("value", "")
    
    if not name or len(name.strip()) < 2:
        errors.append("Name field is missing or too short")
    
    # Check for suspicious characters
    if re.search(r'[0-9@#$%^&*()_+=\[\]{}|\\<>]', name):
        errors.append("Name contains suspicious characters")
    
    return errors


def validate_fields(document_type: DocumentType, fields: Dict[str, Any]) -> List[str]:
    """
    Run all validations for the given document type.
    
    Args:
        document_type: Type of document
        fields: Extracted fields dict
    
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Common validations
    errors.extend(validate_name(fields))
    errors.extend(validate_dob(fields))
    
    # Document-specific validations
    if document_type == DocumentType.AADHAAR:
        errors.extend(validate_aadhaar(fields))
    elif document_type == DocumentType.PAN:
        errors.extend(validate_pan(fields))
    elif document_type == DocumentType.VOTER_ID:
        errors.extend(validate_voter_id(fields))
    
    return errors
