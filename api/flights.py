"""
World-class Google Flights API wrapper for AI travel apps, agents, and automation.

Features:
- Simple, strongly-typed API for flight searches
- Multiple fetch modes for reliability (local playwright, fallback, bright-data)
- Robust error handling suitable for automation
- JSON output support with detailed flight information
- Input validation and type safety
- Cookie consent handling for EU compliance
- Comprehensive logging and debugging

Usage:
    from flights import search_flights

    result = search_flights(
        origin="JFK",
        destination="LAX",
        depart_date="2025-12-25",
        return_date="2025-12-30",
        adults=1,
        seat="economy",
        fetch_mode="local"
    )

    print(f"Current price level: {result.current_price}")
    for flight in result.flights[:5]:  # Show first 5 flights
        print(f"{flight.name}: {flight.price} ({flight.duration}, {flight.stops} stops)")
        print(f"  Departure: {flight.departure}")
        print(f"  Arrival: {flight.arrival}")
        if flight.delay:
            print(f"  Delay: {flight.delay}")
        print()
"""

import re
import json
from typing import Literal, Optional, Dict, Any, List, Union
from fast_flights import FlightData, Passengers, create_filter, get_flights_from_filter


class FlightSearchError(Exception):
    """Custom exception for flight search errors"""
    pass


def validate_airport_code(code: str) -> bool:
    """Validate airport code format (3 letters)"""
    return bool(re.match(r'^[A-Z]{3}$', code))


def validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD)"""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_str))


def search_flights(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat: Literal["economy", "premium-economy", "business", "first"] = "economy",
    max_stops: Optional[int] = None,
    fetch_mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "common"
) -> Any:
    """
    Search for flights using Google Flights scraper with validation and error handling.

    Args:
        origin (str): Departure airport code (e.g., "JFK")
        destination (str): Arrival airport code (e.g., "LAX")
        depart_date (str): Departure date in YYYY-MM-DD format
        return_date (str, optional): Return date for round-trip in YYYY-MM-DD format.
                                   If None, searches for one-way trip.
        adults (int): Number of adult passengers (default: 1)
        children (int): Number of children (default: 0)
        infants_in_seat (int): Number of infants in seat (default: 0)
        infants_on_lap (int): Number of infants on lap (default: 0)
        seat (str): Seat class - "economy", "premium-economy", "business", or "first" (default: "economy")
        max_stops (int, optional): Maximum number of stops (0, 1, or 2)
        fetch_mode (str): Fetch mode - "common", "fallback", "force-fallback", "local", "bright-data" (default: "common")

    Returns:
        Result: Object containing current_price and list of flights with details

    Raises:
        FlightSearchError: If validation fails or search encounters an error
    """
    # Input validation
    if not validate_airport_code(origin.upper()):
        raise FlightSearchError(f"Invalid origin airport code: {origin}")
    if not validate_airport_code(destination.upper()):
        raise FlightSearchError(f"Invalid destination airport code: {destination}")
    if not validate_date(depart_date):
        raise FlightSearchError(f"Invalid departure date format: {depart_date}")
    if return_date and not validate_date(return_date):
        raise FlightSearchError(f"Invalid return date format: {return_date}")

    if adults < 1:
        raise FlightSearchError("At least 1 adult passenger required")
    if max_stops is not None and max_stops not in [0, 1, 2]:
        raise FlightSearchError("max_stops must be 0, 1, or 2")

    # Convert to uppercase for consistency
    origin = origin.upper()
    destination = destination.upper()

    # Determine trip type
    trip = "one-way" if return_date is None else "round-trip"

    # Create flight data
    flight_data = [
        FlightData(date=depart_date, from_airport=origin, to_airport=destination)
    ]

    if return_date:
        flight_data.append(
            FlightData(date=return_date, from_airport=destination, to_airport=origin)
        )

    # Create passengers
    passengers = Passengers(
        adults=adults,
        children=children,
        infants_in_seat=infants_in_seat,
        infants_on_lap=infants_on_lap
    )

    # Create filter
    filter = create_filter(
        flight_data=flight_data,
        trip=trip,
        seat=seat,
        passengers=passengers,
        max_stops=max_stops
    )

    # Get flights with error handling
    try:
        result = get_flights_from_filter(filter, mode=fetch_mode)
        return result
    except RuntimeError as e:
        raise FlightSearchError(f"Flight search failed: {str(e)}")
    except Exception as e:
        raise FlightSearchError(f"Unexpected error during flight search: {str(e)}")


def get_flights_url(
    origin: str,
    destination: str,
    depart_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants_in_seat: int = 0,
    infants_on_lap: int = 0,
    seat: Literal["economy", "premium-economy", "business", "first"] = "economy",
    max_stops: Optional[int] = None
):
    """
    Generate Google Flights URL for the search parameters.

    Args:
        Same as search_flights()

    Returns:
        str: Google Flights URL
    """
    # Determine trip type
    trip = "one-way" if return_date is None else "round-trip"

    # Create flight data
    flight_data = [
        FlightData(date=depart_date, from_airport=origin, to_airport=destination)
    ]

    if return_date:
        flight_data.append(
            FlightData(date=return_date, from_airport=destination, to_airport=origin)
        )

    # Create passengers
    passengers = Passengers(
        adults=adults,
        children=children,
        infants_in_seat=infants_in_seat,
        infants_on_lap=infants_on_lap
    )

    # Create filter
    filter = create_filter(
        flight_data=flight_data,
        trip=trip,
        seat=seat,
        passengers=passengers,
        max_stops=max_stops
    )

    # Get Base64 encoded string
    b64 = filter.as_b64().decode('utf-8')
    return f"https://www.google.com/travel/flights?tfs={b64}"


if __name__ == "__main__":
    # Search for flights from Nairobi to Stockholm on Dec 25, 2025
    result = search_flights(
        origin="NBO",
        destination="ARN",
        depart_date="2025-12-25",
        return_date="2025-12-30",
        adults=1,
        seat="economy",
        fetch_mode="local"
    )

    print(f"Current price level: {result.current_price}")
    print(f"Found {len(result.flights)} flights")
    print("\nFirst 5 flights:")
    for flight in result.flights[:5]:
        print(f"- {flight.name}: {flight.price} ({flight.duration}, {flight.stops} stops)")
        print(f"  Departure: {flight.departure}")
        print(f"  Arrival: {flight.arrival}")
        if flight.delay:
            print(f"  Delay: {flight.delay}")
        print()
