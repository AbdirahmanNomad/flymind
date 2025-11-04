"""
FastAPI application for Google Flights scraper with n8n integration.
Provides REST endpoints, webhooks, and automation features.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
import logging
import json
import os
from datetime import datetime, date, timedelta
import re
import uvicorn
from typing import Optional

# Optional AI functionality
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    genai = None

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Import our flight search functionality
from flights.fast_flights.core import get_flights
from flights.fast_flights.flights_impl import FlightData, Passengers
from typing import Optional, Literal

# Define FlightSearchError for compatibility
class FlightSearchError(Exception):
    """Custom exception for flight search errors"""
    pass

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
    fetch_mode: Literal["common", "fallback", "force-fallback", "local", "bright-data"] = "local"
):
    """Search for flights using the fast_flights library"""
    try:
        # Prepare flight data
        flight_data = [
            FlightData(
                from_airport=origin,
                to_airport=destination,
                date=depart_date
            )
        ]

        # Add return flight if round trip
        trip_type: Literal["round-trip", "one-way", "multi-city"] = "one-way"
        if return_date:
            flight_data.append(FlightData(
                from_airport=destination,
                to_airport=origin,
                date=return_date
            ))
            trip_type = "round-trip"

        # Prepare passengers
        passengers = Passengers(
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )

        # Search flights
        result = get_flights(
            flight_data=flight_data,
            trip=trip_type,
            passengers=passengers,
            seat=seat,
            fetch_mode=fetch_mode,
            max_stops=max_stops
        )

        # Convert result to expected format
        if result and hasattr(result, 'flights'):
            return type('Result', (), {
                'flights': result.flights,
                'current_price': getattr(result, 'current_price', 'unknown')
            })()
        else:
            return type('Result', (), {
                'flights': [],
                'current_price': 'unknown'
            })()

    except Exception as e:
        raise FlightSearchError(f"Flight search failed: {str(e)}")

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# City to airport code mapping
CITY_TO_AIRPORT = {
    "new york": "JFK",
    "nyc": "JFK",
    "los angeles": "LAX",
    "la": "LAX",
    "london": "LHR",
    "paris": "CDG",
    "tokyo": "NRT",
    "berlin": "BER",
    "amsterdam": "AMS",
    "rome": "FCO",
    "barcelona": "BCN",
    "madrid": "MAD",
    "vienna": "VIE",
    "prague": "PRG",
    "budapest": "BUD",
    "warsaw": "WAW",
    "stockholm": "ARN",
    "copenhagen": "CPH",
    "oslo": "OSL",
    "helsinki": "HEL",
    "dublin": "DUB",
    "edinburgh": "EDI",
    "manchester": "MAN",
    "birmingham": "BHX",
    "glasgow": "GLA",
    "dubai": "DXB",
    "abu dhabi": "AUH",
    "sharjah": "SHJ",
    "moscow": "SVO",
    "saint petersburg": "LED",
    "miami": "MIA",
    "chicago": "ORD",
    "san francisco": "SFO",
    "seattle": "SEA",
    "boston": "BOS",
    "washington": "IAD",
    "atlanta": "ATL",
    "denver": "DEN",
    "las vegas": "LAS",
    "orlando": "MCO",
    "houston": "IAH",
    "phoenix": "PHX",
    "salt lake city": "SLC",
    "portland": "PDX",
    "austin": "AUS",
    "nashville": "BNA",
    "charlotte": "CLT",
    "raleigh": "RDU",
    "pittsburgh": "PIT",
    "cleveland": "CLE",
    "cincinnati": "CVG",
    "indianapolis": "IND",
    "columbus": "CMH",
    "detroit": "DTW",
    "milwaukee": "MKE",
    "minneapolis": "MSP",
    "kansas city": "MCI",
    "omaha": "OMA",
    "wichita": "ICT",
    "oklahoma city": "OKC",
    "tulsa": "TUL",
    "albuquerque": "ABQ",
    "el paso": "ELP",
    "san antonio": "SAT",
    "corpus christi": "CRP",
    "lubbock": "LBB",
    "wichita falls": "SPS",
    "amarillo": "AMA",
    "odessa": "MAF",
    "midland": "MAF",
    "san angelo": "SJT",
    "abilene": "ABI",
    "tyler": "TYR",
    "longview": "GGG",
    "texarkana": "TXK",
    "shreveport": "SHV",
    "baton rouge": "BTR",
    "new orleans": "MSY",
    "jackson": "JAN",
    "biloxi": "GPT",
    "mobile": "MOB",
    "pensacola": "PNS",
    "tallahassee": "TLH",
    "savannah": "SAV",
    "charleston": "CHS",
    "myrtle beach": "MYR",
    "wilmington": "ILM",
    "greensboro": "GSO",
    "winston salem": "INT",
    "fayetteville": "FAY",
    "asheville": "AVL",
    "huntsville": "HSV",
    "birmingham al": "BHM",
    "montgomery": "MGM",
    "tucson": "TUS",
    "yuma": "NYL",
    "flagstaff": "FLG",
    "grand canyon": "GCN",
    "page": "PGA",
    "kingman": "IGM",
    "lake havasu city": "HII",
    "bullhead city": "IFP",
    "prescott": "PRC",
    "show low": "SOW",
    "farmington": "FMN",
    "durango": "DRO",
    "cortez": "CEZ",
    "montrose": "MTJ",
    "grand junction": "GJT",
    "glenwood springs": "GWS",
    "aspen": "ASE",
    "vail": "EGE",
    "breckenridge": "QKB",
    "steamboat springs": "HDN",
    "fort collins": "FNL",
    "greeley": "GXY",
    "pueblo": "PUB",
    "colorado springs": "COS",
    "santa fe": "SAF",
    "roswell": "ROW",
    "carlsbad": "CNM",
    "hobbs": "HOB",
    "clovis": "CVN",
    "portales": "PRZ",
    "silver city": "SVC",
    "deming": "DMN",
    "las cruces": "LRU",
    "truth or consequences": "TCS",
    "socorro": "ONM",
    "gallup": "GUP",
    "zuni pueblo": "ZUN",
    "window rock": "RQE",
    "chinle": "E91",
    "crownpoint": "0E8",
    "shiprock": "5V5",
    "casper": "CPR",
    "cheyenne": "CYS",
    "laramie": "LAR",
    "rawlins": "RWL",
    "rock springs": "RKS",
    "evanston": "EVW",
    "heber city": "W103",
    "park city": "W104",
    "midway": "W105",
    "kamas": "W106",
    "roosevelt": "W107",
    "duchesne": "W108",
    "altamont": "W109",
    "tabiona": "W110",
    "fruitland": "W111",
    "neola": "W112",
    "lapoint": "W113",
    "jensen": "W114",
    "vernal": "W115",
    "dutch john": "W116",
    "manila": "W117",
    "cedar city": "CDC",
    "bryce canyon": "BCE",
    "valle": "VLE",
    "taylor": "TYZ",
    "holbrook": "HBK",
    "grants": "GNT",
    "los alamos": "LAM",
    "los lunas": "LUA",
    "double eagle ii": "AEG",
    "conchas lake": "CNX",
    "newkirk": "W148",
    "ponca city": "PNC",
    "blackwell": "BWL",
    "pawhuska": "H76",
    "bartlesville": "BVO",
    "nowata": "H66",
    "coffeeyville": "CFV",
    "independence": "IDP",
    "parsons": "PPF",
    "chanute": "CNU",
    "fort scott": "FSK",
    "garnett": "K68",
    "osage city": "53K",
    "ottawa": "OWI",
    "wellsville": "K68",
    "lawrence": "LWC",
    "topeka": "FOE",
    "gardner": "K34",
    "new century": "JCI",
    "johnson county": "OJC",
    "olathe": "JCI",
    "bonner springs": "W149",
    "de soto": "W150",
    "eudora": "W151",
    "lincolnville": "W152",
    "mc louth": "W153",
    "osawatomie": "W154",
    "paola": "W155",
    "tonganoxie": "W156",
    "troy": "W157",
    "wathena": "W158",
    "weston": "W159",
    "winchester": "W160",
    "basehor": "W161",
    "bendena": "W162",
    "denison": "W163",
    "effingham": "W164",
    "everest": "W165",
    "fairfax": "W166",
    "fanning": "W167",
    "graham": "W168",
    "haden": "W169",
    "helena": "W170",
    "holton": "W171",
    "horton": "W172",
    "lancaster": "W173",
    "leona": "W174",
    "mayetta": "W175",
    "melvern": "W176",
    "netawaka": "W177",
    "norcatur": "W178",
    "onaga": "W179",
    "overbrook": "W180",
    "powhattan": "W181",
    "quenemo": "W182",
    "reserve": "W183",
    "rossville": "W184",
    "sabetha": "W185",
    "seneca": "W186",
    "silver lake": "W187",
    "soldier": "W188",
    "talmage": "W189",
    "verona": "W190",
    "volkland": "W191",
    "wakarusa": "W192",
    "wetmore": "W193",
    "whiting": "W194",
    "williamsburg": "W195",
    "auburn": "W196",
    "burlingame": "W197",
    "bushong": "W198",
    "carbondale": "W199",
    "cassoday": "W200",
    "cedar point": "W201",
    "council grove": "W202",
    "dwight": "W203",
    "emmett": "W204",
    "florence": "W205"
}

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

app = FastAPI(
    title="🧠 FlyMind API",
    description="AI-Powered Flight Analytics & Automation Suite - Intelligent flight search, real-time Google Flights scraping, and automation tools for developers and enterprises",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "System",
            "description": "System health and information endpoints"
        },
        {
            "name": "Flights",
            "description": "Flight search and booking operations"
        },
        {
            "name": "Price Alerts",
            "description": "Price monitoring and alert management"
        },
        {
            "name": "AI Features",
            "description": "AI-powered natural language flight search"
        },
        {
            "name": "Webhooks",
            "description": "Webhook notification management"
        }
    ]
)

# Add CORS middleware for n8n and web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for n8n-compatible responses
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

# Global variables for webhook management
webhook_urls: List[str] = []
search_history: Dict[str, Dict[str, Any]] = {}
price_alerts: Dict[str, Dict[str, Any]] = {}

def parse_flexible_date(date_input: Union[date, str], base_date: Optional[date] = None) -> date:
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

def send_webhook_notification(webhook_url: str, payload: WebhookPayload):
    """Send webhook notification to external service"""
    import requests
    try:
        response = requests.post(webhook_url, json=payload.dict(), timeout=10)
        logger.info(f"Webhook sent to {webhook_url}: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send webhook to {webhook_url}: {e}")

# Global exception handlers for consistent error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "error_code": f"HTTP_{exc.status_code}",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed information"""
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with consistent format"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Google Flights API for Automation",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

@app.get("/version", tags=["System"])
async def get_version():
    """Get API version and deployment information"""
    return {
        "version": "2.0.0",
        "name": "Google Flights API",
        "description": "World-class Google Flights scraper API for automation",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/search", response_model=SearchResponse, tags=["Flights"])
async def search_flights_endpoint(
    request: FlightSearchRequest,
    background_tasks: BackgroundTasks
):
    """
    Search for flights with n8n-compatible response format.

    This endpoint is optimized for n8n HTTP Request nodes and returns
    structured JSON responses that work well with n8n workflows.
    """
    try:
        # Convert city names to airport codes
        if hasattr(request, 'origin') and request.origin:
            request.origin = convert_city_to_airport(request.origin)
        if hasattr(request, 'destination') and request.destination:
            request.destination = convert_city_to_airport(request.destination)

        # Get flight segments based on trip type
        segments = request.get_segments()

        # For now, handle only single segment searches (backward compatibility)
        # Multi-city support will be implemented in the next step
        if len(segments) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multi-city searches not yet implemented"
            )

        segment = segments[0]

        # Convert request to search parameters
        search_params = {
            "origin": segment.origin.upper(),
            "destination": segment.destination.upper(),
            "depart_date": segment.depart_date.isoformat(),
            "return_date": segments[1].depart_date.isoformat() if len(segments) > 1 else None,
            "adults": request.adults,
            "children": request.children,
            "infants_in_seat": request.infants_seat,
            "infants_on_lap": request.infants_lap,
            "seat": request.seat_class,
            "max_stops": request.max_stops,
            "fetch_mode": request.fetch_mode
        }

        # Perform search in a separate thread to avoid asyncio conflicts
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(search_flights, **search_params)
            result = future.result()

        # Generate search URL
        search_url = get_flights_url(
            origin=search_params["origin"],
            destination=search_params["destination"],
            depart_date=search_params["depart_date"],
            return_date=search_params["return_date"],
            adults=search_params["adults"],
            children=search_params["children"],
            infants_in_seat=search_params["infants_in_seat"],
            infants_on_lap=search_params["infants_on_lap"],
            seat=search_params["seat"],
            max_stops=search_params["max_stops"]
        )

        # Format flights for n8n compatibility
        formatted_flights = []
        for flight in result.flights:
            formatted_flights.append({
                "name": getattr(flight, 'name', 'Unknown'),
                "departure": getattr(flight, 'departure', ''),
                "arrival": getattr(flight, 'arrival', ''),
                "duration": getattr(flight, 'duration', ''),
                "stops": getattr(flight, 'stops', 0),
                "price": getattr(flight, 'price', ''),
                "delay": getattr(flight, 'delay', None)
            })

        # Create search ID for tracking
        search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{request.origin}_{request.destination}"

        # Store in history
        search_history[search_id] = {
            "request": request.dict(),
            "result": {
                "current_price": getattr(result, 'current_price', 'unknown'),
                "total_flights": len(result.flights),
                "flights": formatted_flights
            },
            "timestamp": datetime.now().isoformat()
        }

        # Send webhooks in background
        if webhook_urls:
            webhook_payload = WebhookPayload(
                event="flight_search_completed",
                search_id=search_id,
                data={
                    "current_price": getattr(result, 'current_price', 'unknown'),
                    "total_flights": len(result.flights),
                    "flights": formatted_flights[:10]  # Send first 10 flights
                },
                timestamp=datetime.now().isoformat()
            )

            for webhook_url in webhook_urls:
                background_tasks.add_task(send_webhook_notification, webhook_url, webhook_payload)

        return SearchResponse(
            success=True,
            current_price=getattr(result, 'current_price', 'unknown'),
            total_flights=len(result.flights),
            flights=formatted_flights,
            search_url=search_url,
            timestamp=datetime.now().isoformat()
        )

    except FlightSearchError as e:
        logger.error(f"Flight search error: {e}")
        error_response = ErrorResponse(
            error=str(e),
            error_code="SEARCH_ERROR",
            timestamp=datetime.now().isoformat()
        )
        raise HTTPException(
            status_code=400,
            detail=error_response.dict()
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=f"Internal server error: {str(e)}",
                error_code="INTERNAL_ERROR",
                timestamp=datetime.now().isoformat()
            ).dict()
        )

@app.get("/search/{search_id}", tags=["Flights"])
async def get_search_result(search_id: str):
    """Retrieve previous search results by ID"""
    if search_id not in search_history:
        raise HTTPException(status_code=404, detail="Search not found")

    return search_history[search_id]

@app.post("/webhooks", tags=["Webhooks"])
async def register_webhook(webhook_url: str = Form(...)):
    """Register a webhook URL for notifications"""
    if webhook_url not in webhook_urls:
        webhook_urls.append(webhook_url)
        logger.info(f"Registered webhook: {webhook_url}")
        return {"message": "Webhook registered successfully"}
    else:
        return {"message": "Webhook already registered"}

@app.delete("/webhooks", tags=["Webhooks"])
async def unregister_webhook(webhook_url: str):
    """Unregister a webhook URL"""
    if webhook_url in webhook_urls:
        webhook_urls.remove(webhook_url)
        logger.info(f"Unregistered webhook: {webhook_url}")
        return {"message": "Webhook unregistered successfully"}
    else:
        return {"message": "Webhook not found"}

@app.get("/webhooks", tags=["Webhooks"])
async def list_webhooks():
    """List all registered webhooks"""
    return {"webhooks": webhook_urls}

@app.post("/alerts", response_model=PriceAlertResponse, tags=["Price Alerts"])
async def create_price_alert(request: PriceAlertRequest):
    """Create a new price alert for flight monitoring"""
    try:
        # Convert city names to airport codes
        origin_code = convert_city_to_airport(request.origin)
        destination_code = convert_city_to_airport(request.destination)

        # Parse the departure date
        depart_date_parsed = parse_flexible_date(request.depart_date)

        # Parse return date if provided
        return_date_parsed = None
        if request.return_date:
            return_date_parsed = parse_flexible_date(request.return_date)

        # Generate unique alert ID
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{origin_code}_{destination_code}"

        # Create alert data
        alert_data = {
            "alert_id": alert_id,
            "trip_type": request.trip_type,
            "origin": origin_code,
            "destination": destination_code,
            "depart_date": depart_date_parsed.isoformat(),
            "return_date": return_date_parsed.isoformat() if return_date_parsed else None,
            "target_price": request.target_price,
            "currency": request.currency,
            "email": request.email,
            "notification_channels": request.notification_channels,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }

        # Store the alert
        price_alerts[alert_id] = alert_data

        logger.info(f"Created {request.trip_type} price alert: {alert_id} for {origin_code} → {destination_code}")

        return PriceAlertResponse(**alert_data)

    except Exception as e:
        logger.error(f"Error creating price alert: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create price alert: {str(e)}"
        )

@app.get("/alerts", tags=["Price Alerts"])
async def list_price_alerts():
    """List all active price alerts"""
    alerts_list = []
    for alert_id, alert_data in price_alerts.items():
        if alert_data.get("status") == "active":
            alerts_list.append(PriceAlertResponse(**alert_data))

    return {"alerts": [alert.dict() for alert in alerts_list]}

@app.delete("/alerts/{alert_id}", tags=["Price Alerts"])
async def delete_price_alert(alert_id: str):
    """Delete a price alert by ID"""
    if alert_id not in price_alerts:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Mark as inactive instead of deleting (for audit purposes)
    price_alerts[alert_id]["status"] = "inactive"
    price_alerts[alert_id]["deleted_at"] = datetime.now().isoformat()

    logger.info(f"Deleted price alert: {alert_id}")

    return {"message": "Alert deleted successfully"}

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

def call_ai_provider(provider: str, prompt: str, api_key: str, model: Optional[str] = None) -> str:
    """Call the specified AI provider with the given prompt"""
    if provider == "openai":
        if not OPENAI_AVAILABLE:
            raise HTTPException(status_code=503, detail="OpenAI not available. Install with: pip install openai")

        openai.api_key = api_key
        model_name = model or "gpt-4o-mini"

        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a travel search query parser. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()

    elif provider == "google":
        if not GOOGLE_AI_AVAILABLE:
            raise HTTPException(status_code=503, detail="Google AI not available. Install with: pip install google-generativeai")

        genai.configure(api_key=api_key)
        model_name = model or "gemini-pro"

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text.strip()

    elif provider == "deepseek":
        if not REQUESTS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Requests not available")

        model_name = model or "deepseek-chat"
        url = "https://api.deepseek.com/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a travel search query parser. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.1
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
        else:
            raise HTTPException(status_code=503, detail=f"DeepSeek API error: {response.text}")

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {provider}")

@app.post("/ai/search", tags=["AI Features"])
async def ai_flight_search(request: NaturalLanguageQuery):
    """
    AI-powered natural language flight search with multiple provider support.

    Supports OpenAI, Google Gemini, and DeepSeek.

    Parse natural language queries like:
    - "Find me the cheapest flight from Paris to Tokyo next weekend"
    - "Show me flights to London in December"
    - "Book a round trip from NYC to LA for next month"
    """
    try:
        # Get API key based on provider
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_AI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY"
        }

        api_key = request.api_key or os.getenv(env_var_map.get(request.provider, ""))
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=f"{request.provider.upper()} API key required. Set {env_var_map[request.provider]} environment variable or provide in request."
            )

        # Create the parsing prompt
        prompt = f"""
        Extract flight search parameters from this natural language query: "{request.query}"

        Analyze the query carefully and extract ALL relevant flight search information. Consider:
        - Cities/airports mentioned (origin and destination)
        - Dates (specific dates, or relative like "next week", "December", "weekend")
        - Trip type (one-way, round-trip, return, back-and-forth, multi-city)
        - Return dates for round-trip flights (when mentioned)
        - Number of passengers (adults, children, infants)
        - Seat class preferences (economy, business, first class, etc.)
        - Budget constraints (under $X, cheap, affordable, etc.)
        - Airline preferences (specific airlines mentioned)
        - Stop preferences (direct, nonstop, 1 stop, 2 stops, etc.)
        - Any special requirements or filters

        IMPORTANT: For round-trip queries, ALWAYS extract both departure AND return dates when mentioned.
        Words indicating round-trip: round trip, return, back, round-trip, return flight, back and forth, etc.

        Return ONLY a valid JSON object with these exact fields:
        {{
            "origin": "departure city or airport code",
            "destination": "arrival city or airport code",
            "depart_date": "departure date in YYYY-MM-DD format or flexible like 'next weekend'",
            "return_date": "return date in YYYY-MM-DD format or flexible like 'next month', or null for one-way",
            "trip_type": "one-way, round-trip, or multi-city",
            "adults": number of adult passengers (default 1),
            "children": number of children (default 0),
            "seat_class": "economy, premium_economy, business, or first" (default "economy"),
            "max_stops": maximum stops preferred (null for any, 0 for nonstop, 1, 2, etc.),
            "budget_max": maximum budget in local currency (null if not specified),
            "preferred_airlines": array of preferred airline names (empty array if none),
            "flexible_dates": boolean indicating if dates are flexible (default false)
        }}

        Examples:
        Query: "Find cheap flights from New York to London next month under $500"
        Response: {{"origin": "New York", "destination": "London", "depart_date": "next month", "return_date": null, "trip_type": "one-way", "adults": 1, "children": 0, "seat_class": "economy", "max_stops": null, "budget_max": 500, "preferred_airlines": [], "flexible_dates": true}}

        Query: "Book business class round trip from Paris to Tokyo departing next weekend returning next month with Delta or United"
        Response: {{"origin": "Paris", "destination": "Tokyo", "depart_date": "next weekend", "return_date": "next month", "trip_type": "round-trip", "adults": 1, "children": 0, "seat_class": "business", "max_stops": null, "budget_max": null, "preferred_airlines": ["Delta", "United"], "flexible_dates": false}}

        Query: "Direct flights from Chicago to Miami for 2 adults and 1 child in December"
        Response: {{"origin": "Chicago", "destination": "Miami", "depart_date": "2024-12-01", "return_date": null, "trip_type": "one-way", "adults": 2, "children": 1, "seat_class": "economy", "max_stops": 0, "budget_max": null, "preferred_airlines": [], "flexible_dates": true}}

        Query: "Round trip flights from London to New York leaving December 15 returning December 22 under $800"
        Response: {{"origin": "London", "destination": "New York", "depart_date": "2024-12-15", "return_date": "2024-12-22", "trip_type": "round-trip", "adults": 1, "children": 0, "seat_class": "economy", "max_stops": null, "budget_max": 800, "preferred_airlines": [], "flexible_dates": false}}

        Query: "One stop business class return flight from Tokyo to Sydney for next weekend"
        Response: {{"origin": "Tokyo", "destination": "Sydney", "depart_date": "next weekend", "return_date": null, "trip_type": "round-trip", "adults": 1, "children": 0, "seat_class": "business", "max_stops": 1, "budget_max": null, "preferred_airlines": [], "flexible_dates": false}}
        """

        # Call the AI provider
        ai_response = call_ai_provider(request.provider, prompt, api_key, request.model)

        # Clean up the response (remove markdown code blocks if present)
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        if ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]

        ai_response = ai_response.strip()

        try:
            parsed_params = json.loads(ai_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {ai_response}")
            raise HTTPException(
                status_code=500,
                detail=f"AI parsing failed: {str(e)}"
            )

        # Validate required fields
        required_fields = ["origin", "destination", "depart_date", "trip_type"]
        for field in required_fields:
            if field not in parsed_params or not parsed_params[field]:
                raise HTTPException(
                    status_code=400,
                    detail=f"AI parsing incomplete: missing {field}"
                )

        # Set defaults for optional fields
        parsed_params.setdefault("return_date", None)
        parsed_params.setdefault("adults", 1)
        parsed_params.setdefault("seat_class", "economy")

        # Now perform the actual flight search with parsed parameters
        search_request = FlightSearchRequest(
            trip_type=parsed_params["trip_type"],
            segments=None,
            origin=parsed_params["origin"],
            destination=parsed_params["destination"],
            depart_date=parsed_params["depart_date"],
            return_date=parsed_params["return_date"],
            adults=parsed_params.get("adults", 1),
            children=parsed_params.get("children", 0),
            infants_seat=0,
            infants_lap=0,
            seat_class=parsed_params.get("seat_class", "economy"),
            max_stops=parsed_params.get("max_stops"),
            fetch_mode="local"
        )

        # Use the existing search endpoint logic
        # Convert city names to airport codes
        if hasattr(search_request, 'origin') and search_request.origin:
            search_request.origin = convert_city_to_airport(search_request.origin)
        if hasattr(search_request, 'destination') and search_request.destination:
            search_request.destination = convert_city_to_airport(search_request.destination)

        # Get flight segments based on trip type
        segments = search_request.get_segments()

        # For now, handle only single segment searches
        if len(segments) > 1:
            raise HTTPException(
                status_code=400,
                detail="Multi-city searches not yet implemented"
            )

        segment = segments[0]

        # Handle round-trip searches properly
        return_date = None
        if search_request.trip_type == "round-trip" and search_request.return_date:
            return_date_parsed = parse_flexible_date(search_request.return_date)
            return_date = return_date_parsed.isoformat()

        # Convert request to search parameters
        search_params = {
            "origin": segment.origin.upper(),
            "destination": segment.destination.upper(),
            "depart_date": segment.depart_date.isoformat(),
            "return_date": return_date,
            "adults": search_request.adults,
            "children": search_request.children,
            "infants_in_seat": search_request.infants_seat,
            "infants_on_lap": search_request.infants_lap,
            "seat": search_request.seat_class,
            "max_stops": search_request.max_stops,
            "fetch_mode": search_request.fetch_mode
        }

        # Perform search in a separate thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(search_flights, **search_params)
            result = future.result()

        # Generate search URL
        search_url = get_flights_url(
            origin=search_params["origin"],
            destination=search_params["destination"],
            depart_date=search_params["depart_date"],
            return_date=search_params["return_date"],
            adults=search_params["adults"],
            children=search_params["children"],
            infants_in_seat=search_params["infants_in_seat"],
            infants_on_lap=search_params["infants_on_lap"],
            seat=search_params["seat"],
            max_stops=search_params["max_stops"]
        )

        # Format flights for response
        formatted_flights = []
        for flight in result.flights:
            formatted_flights.append({
                "name": getattr(flight, 'name', 'Unknown'),
                "departure": getattr(flight, 'departure', ''),
                "arrival": getattr(flight, 'arrival', ''),
                "duration": getattr(flight, 'duration', ''),
                "stops": getattr(flight, 'stops', 0),
                "price": getattr(flight, 'price', ''),
                "delay": getattr(flight, 'delay', None)
            })

        # Determine model name for response
        model_used = request.model or {
            "openai": "gpt-4o-mini",
            "google": "gemini-pro",
            "deepseek": "deepseek-chat"
        }.get(request.provider, "unknown")

        return {
            "success": True,
            "parsed_query": parsed_params,
            "total_flights": len(result.flights),
            "flights": formatted_flights[:10],  # Return top 10 results
            "search_url": search_url,
            "timestamp": datetime.now().isoformat(),
            "ai_provider": request.provider,
            "ai_model": model_used
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"AI-powered search failed: {str(e)}"
        )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
