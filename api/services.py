"""
Business logic services for flight search, alerts, and utilities.
"""

from typing import Optional, Literal, List
from datetime import date, timedelta
import re
from api.logger import logger
from api.constants import CITY_TO_AIRPORT


def parse_flexible_date(date_input: str, base_date: Optional[date] = None) -> date:
    """
    Parse flexible date strings into actual dates.

    Supports formats like:
    - "weekend": Next Saturday
    - "±3 days": ±3 days from base_date
    - "YYYY-MM-DD": Direct date string
    - date object: Pass through
    """
    if isinstance(date_input, date):
        return date_input

    if isinstance(date_input, str):
        # Try to parse as YYYY-MM-DD first
        try:
            return date.fromisoformat(date_input)
        except ValueError:
            pass

        # Handle flexible date strings
        today = base_date or date.today()

        # Weekend (next Saturday)
        if date_input.lower() == "weekend":
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0:
                days_until_saturday = 7  # Next Saturday if today is Saturday
            return today + timedelta(days=days_until_saturday)

        # ±X days format
        match = re.match(r'^([+-])(\d+)\s*days?$', date_input.lower())
        if match:
            sign, days = match.groups()
            days = int(days)
            if sign == '+':
                return today + timedelta(days=days)
            else:
                return today - timedelta(days=days)

        # Month name (e.g., "december", "january")
        month_names = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        if date_input.lower() in month_names:
            month = month_names[date_input.lower()]
            year = today.year if month >= today.month else today.year + 1
            return date(year, month, 1)

        # Default to today if unrecognized
        logger.warning(f"Unrecognized date format: {date_input}, using today")
        return today

    # Fallback
    return date.today()


def convert_city_to_airport(city_name: str) -> str:
    """Convert city name to airport code, or return as-is if already an airport code"""
    if not city_name:
        return city_name

    # If it's already 3 characters and uppercase, assume it's an airport code
    if len(city_name) == 3 and city_name.isupper():
        return city_name

    # Look up in city mapping
    city_lower = city_name.lower().strip()
    airport_code = CITY_TO_AIRPORT.get(city_lower)

    if airport_code:
        return airport_code

    # If not found, try to extract airport code from the string (e.g., "London (LHR)" -> "LHR")
    airport_match = re.search(r'\(([A-Z]{3})\)', city_name.upper())
    if airport_match:
        return airport_match.group(1)

    # If still not found, return the original (might be an airport code already)
    return city_name.upper()


def get_flights_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat: str = "economy",
    max_stops: Optional[int] = None
) -> str:
    """Generate Google Flights URL for search parameters"""
    base_url = "https://www.google.com/travel/flights"

    # Build search parameters
    params = [
        f"q=flights",
        f"origin={origin}",
        f"destination={destination}",
        f"departure_date={depart_date}",
        f"adults={adults}",
        f"children={children}",
        f"infants_in_seat={infants_in_seat}",
        f"infants_on_lap={infants_on_lap}",
        f"seat={seat}"
    ]

    if return_date:
        params.append(f"return_date={return_date}")

    if max_stops is not None:
        if max_stops == 0:
            params.append("stops=nonstop")
        elif max_stops == 1:
            params.append("stops=1")
        elif max_stops == 2:
            params.append("stops=2")

    return f"{base_url}?{'&'.join(params)}"


async def send_webhook_notification(webhook_url: str, payload: dict):
    """Send webhook notification to external service (async)"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            logger.info(f"Webhook sent to {webhook_url}: {response.status_code}")
            return response
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {e}")
        raise

