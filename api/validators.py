"""
Input validation utilities for API endpoints.
"""

import re
from datetime import date, datetime, timedelta
from typing import Optional
from api.constants import CITY_TO_AIRPORT
from api.logger import logger


def validate_airport_code(code: str) -> bool:
    """Validate airport code format (3 uppercase letters)."""
    if not code:
        return False
    return bool(re.match(r'^[A-Z]{3}$', code.upper()))


def validate_date_not_past(test_date: date, field_name: str = "date") -> None:
    """Validate that a date is not in the past."""
    if test_date < date.today():
        raise ValueError(f"{field_name} cannot be in the past")


def validate_date_range(depart_date: date, return_date: Optional[date], field_name: str = "return_date") -> None:
    """Validate that return date is after departure date."""
    if return_date and return_date <= depart_date:
        raise ValueError(f"{field_name} must be after departure date")


def validate_date_reasonable_future(test_date: date, max_days: int = 365, field_name: str = "date") -> None:
    """Validate that a date is not too far in the future (default 1 year)."""
    max_date = date.today() + timedelta(days=max_days)
    if test_date > max_date:
        raise ValueError(f"{field_name} cannot be more than {max_days} days in the future")


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_origin_destination(origin: str, destination: str) -> None:
    """Validate that origin and destination are different."""
    origin_upper = origin.upper().strip()
    destination_upper = destination.upper().strip()
    
    # Check if they're the same airport code
    if origin_upper == destination_upper:
        raise ValueError("Origin and destination cannot be the same")
    
    # Check if they're the same city (after city lookup)
    origin_city = CITY_TO_AIRPORT.get(origin.lower().strip(), origin_upper)
    dest_city = CITY_TO_AIRPORT.get(destination.lower().strip(), destination_upper)
    
    if origin_city == dest_city:
        raise ValueError("Origin and destination cannot be the same")


def validate_passenger_counts(adults: int, children: int, infants_seat: int, infants_lap: int) -> None:
    """Validate passenger counts are reasonable."""
    total = adults + children + infants_seat + infants_lap
    
    if adults < 1:
        raise ValueError("At least 1 adult passenger is required")
    
    if adults > 9:
        raise ValueError("Maximum 9 adult passengers allowed")
    
    if children > 8:
        raise ValueError("Maximum 8 children allowed")
    
    if infants_seat > 4:
        raise ValueError("Maximum 4 infants in seat allowed")
    
    if infants_lap > 4:
        raise ValueError("Maximum 4 infants on lap allowed")
    
    if total > 9:
        raise ValueError("Total passengers cannot exceed 9")


def sanitize_airport_code(code: str) -> str:
    """Sanitize and normalize airport code input."""
    if not code:
        return ""
    
    # Remove whitespace and convert to uppercase
    code = code.strip().upper()
    
    # Extract airport code from strings like "London (LHR)" -> "LHR"
    match = re.search(r'\(([A-Z]{3})\)', code)
    if match:
        return match.group(1)
    
    # If it's already 3 uppercase letters, return as-is
    if re.match(r'^[A-Z]{3}$', code):
        return code
    
    # Otherwise return uppercase (might be invalid, but let validation catch it)
    return code


def sanitize_string_input(input_str: str, max_length: int = 500) -> str:
    """Sanitize string input to prevent injection attacks."""
    if not input_str:
        return ""
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    # Trim whitespace
    input_str = input_str.strip()
    
    # Limit length
    if len(input_str) > max_length:
        logger.warning(f"Input string truncated from {len(input_str)} to {max_length} characters")
        input_str = input_str[:max_length]
    
    return input_str


