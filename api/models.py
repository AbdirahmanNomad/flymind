"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import date


class FlightResult(BaseModel):
    """Flight result model optimized for n8n workflows"""
    name: str = Field(..., description="Airline and flight number")
    departure: str = Field(..., description="Departure time and date")
    arrival: str = Field(..., description="Arrival time and date")
    duration: str = Field(..., description="Flight duration")
    stops: int = Field(..., description="Number of stops")
    price: str = Field(..., description="Price in local currency")
    delay: Optional[str] = Field(None, description="Delay information if any")


class SearchResponse(BaseModel):
    """Search response model for n8n compatibility"""
    success: bool = Field(..., description="Whether the search was successful")
    current_price: str = Field(..., description="Current price level")
    total_flights: int = Field(..., description="Total number of flights found")
    flights: List[FlightResult] = Field(..., description="List of flight results")
    search_url: str = Field(..., description="Google Flights URL for manual verification")
    timestamp: str = Field(..., description="Search timestamp")
    error: Optional[str] = Field(None, description="Error message if search failed")
    search_id: Optional[str] = Field(None, description="Unique search identifier for history tracking")


class ErrorResponse(BaseModel):
    """Error response model for n8n workflows"""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    timestamp: str = Field(..., description="Error timestamp")


class FlightSegment(BaseModel):
    """Individual flight segment for multi-city searches"""
    origin: str = Field(..., description="Departure city or airport code")
    destination: str = Field(..., description="Arrival city or airport code")
    depart_date: date = Field(..., description="Departure date in YYYY-MM-DD format")


class FlightSearchRequest(BaseModel):
    """Flight search request model with multi-city and flexible dates support"""
    trip_type: str = Field("round-trip", description="Trip type: round-trip, one-way, multi-city")
    segments: Optional[List[FlightSegment]] = Field(None, description="Flight segments for multi-city trips")
    # Legacy fields for backward compatibility
    origin: Optional[str] = Field(None, description="Departure city or airport code")
    destination: Optional[str] = Field(None, description="Arrival city or airport code")
    depart_date: Optional[Union[date, str]] = Field(None, description="Departure date (YYYY-MM-DD) or flexible date")
    return_date: Optional[Union[date, str]] = Field(None, description="Return date (YYYY-MM-DD) or flexible date")
    adults: int = Field(1, description="Number of adult passengers", ge=1, le=9)
    children: int = Field(0, description="Number of children", ge=0, le=8)
    infants_seat: int = Field(0, description="Number of infants in seat", ge=0, le=4)
    infants_lap: int = Field(0, description="Number of infants on lap", ge=0, le=4)
    seat_class: str = Field("economy", description="Seat class")
    max_stops: Optional[int] = Field(None, description="Maximum stops", ge=0, le=2)
    fetch_mode: str = Field("local", description="Fetch mode")

    @validator('trip_type')
    def validate_trip_type(cls, v):
        if v not in ['round-trip', 'one-way', 'multi-city']:
            raise ValueError('Invalid trip type')
        return v

    def get_segments(self) -> List[FlightSegment]:
        """Get flight segments based on trip type"""
        from api.services import parse_flexible_date
        
        if self.trip_type == "multi-city" and self.segments:
            return self.segments
        elif self.trip_type in ["round-trip", "one-way"] and self.origin and self.destination and self.depart_date:
            # Parse flexible dates
            depart_date_parsed = parse_flexible_date(self.depart_date)

            # For backward compatibility, only return the outbound segment
            segments = [FlightSegment(
                origin=self.origin,
                destination=self.destination,
                depart_date=depart_date_parsed
            )]
            return segments
        else:
            raise ValueError("Invalid flight search configuration")


class WebhookPayload(BaseModel):
    """Webhook payload for external integrations"""
    event: str = Field(..., description="Event type")
    search_id: str = Field(..., description="Unique search identifier")
    data: Dict[str, Any] = Field(..., description="Search results or error data")
    timestamp: str = Field(..., description="Event timestamp")


class PriceAlertRequest(BaseModel):
    """Price alert creation request"""
    trip_type: str = Field("one-way", description="Trip type: one-way, round-trip, multi-city")
    origin: str = Field(..., description="Departure city or airport code")
    destination: str = Field(..., description="Arrival city or airport code")
    depart_date: Union[date, str] = Field(..., description="Departure date")
    return_date: Optional[Union[date, str]] = Field(None, description="Return date for round-trip")
    target_price: float = Field(..., description="Target price to alert on", gt=0)
    currency: str = Field("SEK", description="Currency code (SEK, USD, EUR, GBP)")
    email: str = Field(..., description="Email address for notifications")
    notification_channels: List[str] = Field(["email"], description="Notification channels")

    @validator('trip_type')
    def validate_trip_type(cls, v):
        if v not in ['one-way', 'round-trip', 'multi-city']:
            raise ValueError('Invalid trip type')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        if v not in ['SEK', 'USD', 'EUR', 'GBP']:
            raise ValueError('Invalid currency')
        return v


class PriceAlertResponse(BaseModel):
    """Price alert response"""
    alert_id: str = Field(..., description="Unique alert identifier")
    trip_type: str = Field(..., description="Trip type")
    origin: str = Field(..., description="Departure city or airport code")
    destination: str = Field(..., description="Arrival city or airport code")
    depart_date: str = Field(..., description="Departure date")
    return_date: Optional[str] = Field(None, description="Return date for round-trip")
    target_price: float = Field(..., description="Target price to alert on")
    currency: str = Field(..., description="Currency code")
    email: str = Field(..., description="Email address for notifications")
    notification_channels: List[str] = Field(..., description="Notification channels")
    status: str = Field("active", description="Alert status")
    created_at: str = Field(..., description="Creation timestamp")


class NaturalLanguageQuery(BaseModel):
    """Natural language flight search query"""
    query: str = Field(..., description="Natural language flight search query", min_length=3, max_length=500)
    provider: str = Field("openai", description="AI provider: openai, google, deepseek")
    api_key: Optional[str] = Field(None, description="API key (optional if set in environment)")
    model: Optional[str] = Field(None, description="Model name (optional, uses default for provider)")

    @validator('provider')
    def validate_provider(cls, v):
        if v not in ['openai', 'google', 'deepseek']:
            raise ValueError('Invalid AI provider')
        return v

