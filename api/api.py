"""
FastAPI application for Google Flights scraper with n8n integration.
Provides REST endpoints, webhooks, and automation features.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import List, Optional, Dict, Any, Union
import json
import os
from datetime import datetime, date
import uvicorn
import asyncio
from dotenv import load_dotenv
from api.config import (
    ENVIRONMENT, ALLOWED_ORIGINS, API_KEY, REQUIRE_API_KEY,
    API_KEY_HEADER, RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
)
from api.middleware import APIKeyMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from api.database import init_db, get_db, SearchHistory
from api.models import (
    FlightResult, SearchResponse, ErrorResponse, FlightSegment,
    FlightSearchRequest, WebhookPayload, PriceAlertRequest,
    PriceAlertResponse, NaturalLanguageQuery
)
from api.services import (
    parse_flexible_date, convert_city_to_airport,
    get_flights_url, send_webhook_notification
)
from api.logger import setup_logging, logger
from api.cache import get_cached, set_cached, generate_cache_key
from api.validators import (
    validate_airport_code, validate_date_not_past, validate_date_range,
    validate_date_reasonable_future, validate_email, validate_origin_destination,
    validate_passenger_counts, sanitize_airport_code, sanitize_string_input
)
from sqlalchemy.orm import Session

# Load environment variables from .env file
load_dotenv()

# Configure structured logging
setup_logging()

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
try:
    from flights.fast_flights.core import get_flights
    from flights.fast_flights.flights_impl import FlightData, Passengers
    from typing import Optional, Literal

    # Define FlightSearchError for compatibility
    class FlightSearchError(Exception):
        """Custom exception for flight search errors"""
        pass

    FLIGHTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Flight search module not available: {e}")
    FLIGHTS_AVAILABLE = False
    # Define dummy classes for when flights module is not available
    class FlightData:
        pass
    class Passengers:
        pass
    class FlightSearchError(Exception):
        pass
    def get_flights(*args, **kwargs):
        raise FlightSearchError("Flight search not available")

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

# Note: get_flights_url is now in api.services
# Import city mapping and utilities from separate modules  
from api.constants import CITY_TO_AIRPORT

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

# Add security middleware (order matters - first added is last executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(APIKeyMiddleware)

# Add CORS middleware for n8n and web integrations
# Configuration loaded from api.config module
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database imports for persistent storage
from api.database import (
    create_search_history, get_search_history,
    create_price_alert as db_create_price_alert, get_price_alert, get_all_active_alerts,
    create_webhook, get_webhook, get_all_webhooks
)

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
    logger.error(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": str(request.url),
            "method": request.method,
            "client_ip": request.client.host if request.client else None,
        },
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "message": "An unexpected error occurred. Please try again later."
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

@app.post("/search", tags=["Flights"])
async def search_flights_endpoint(
    request: FlightSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Search for flights with n8n-compatible response format.

    This endpoint is optimized for n8n HTTP Request nodes and returns
    structured JSON responses that work well with n8n workflows.
    """
    try:
        # Sanitize and validate inputs
        if hasattr(request, 'origin') and request.origin:
            request.origin = sanitize_string_input(request.origin, max_length=100)
            request.origin = convert_city_to_airport(request.origin)
        if hasattr(request, 'destination') and request.destination:
            request.destination = sanitize_string_input(request.destination, max_length=100)
            request.destination = convert_city_to_airport(request.destination)
        
        # Validate origin and destination are different
        if request.origin and request.destination:
            try:
                validate_origin_destination(request.origin, request.destination)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        # Validate passenger counts
        try:
            validate_passenger_counts(
                request.adults, request.children,
                request.infants_seat, request.infants_lap
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Get flight segments based on trip type
        segments = request.get_segments()

        # Handle multi-city searches
        if len(segments) > 1:
            # For multi-city, we'll search each segment separately and combine results
            # This is a simplified approach - in production, you'd want to search all segments together
            all_flights = []
            combined_price = 0
            
            for i, segment in enumerate(segments):
                # Validate each segment
                try:
                    validate_date_not_past(segment.depart_date, f"Segment {i+1} departure date")
                    validate_date_reasonable_future(segment.depart_date, max_days=365, field_name=f"Segment {i+1} departure date")
                except HTTPException:
                    raise
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Invalid date in segment {i+1}: {str(e)}")
                
                # Convert city names to airport codes for each segment
                origin_code = convert_city_to_airport(segment.origin)
                dest_code = convert_city_to_airport(segment.destination)
                origin_code = sanitize_airport_code(origin_code)
                dest_code = sanitize_airport_code(dest_code)
                
                if not validate_airport_code(origin_code):
                    raise HTTPException(status_code=400, detail=f"Invalid origin airport code in segment {i+1}: {segment.origin}")
                if not validate_airport_code(dest_code):
                    raise HTTPException(status_code=400, detail=f"Invalid destination airport code in segment {i+1}: {segment.destination}")
                
                # Search this segment
                segment_params = {
                    "origin": origin_code,
                    "destination": dest_code,
                    "depart_date": segment.depart_date.isoformat(),
                    "return_date": None,
                    "adults": request.adults,
                    "children": request.children,
                    "infants_in_seat": request.infants_seat,
                    "infants_on_lap": request.infants_lap,
                    "seat": request.seat_class,
                    "max_stops": request.max_stops,
                    "fetch_mode": request.fetch_mode
                }
                
                segment_result = await asyncio.to_thread(search_flights, **segment_params)
                
                if segment_result and hasattr(segment_result, 'flights') and segment_result.flights:
                    # Add segment info to flights
                    for flight in segment_result.flights[:5]:  # Limit to top 5 per segment
                        flight.segment_index = i
                        flight.segment_route = f"{origin_code} → {dest_code}"
                        all_flights.append(flight)
            
            # Create combined result
            result = type('Result', (), {
                'flights': all_flights,
                'current_price': 'multi-city'
            })()
            
            # Generate combined search URL
            search_url = f"https://www.google.com/travel/flights?q=flights"
            for segment in segments:
                seg_origin = convert_city_to_airport(segment.origin)
                seg_dest = convert_city_to_airport(segment.destination)
                seg_origin = sanitize_airport_code(seg_origin)
                seg_dest = sanitize_airport_code(seg_dest)
                search_url += f"&origin={seg_origin}&destination={seg_dest}&departure_date={segment.depart_date.isoformat()}"
            
            # For multi-city, skip the single segment logic below
            # Store search in history
            search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{abs(hash(str(request.dict())))}"
            # Convert request dict to JSON-serializable format
            request_dict = request.dict()
            # Convert date objects to strings
            for key, value in request_dict.items():
                if isinstance(value, date):
                    request_dict[key] = value.isoformat()
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            for k, v in item.items():
                                if isinstance(v, date):
                                    item[k] = v.isoformat()
            
            # For multi-city, extract origin from first segment and destination from last segment
            if not segments:
                raise HTTPException(status_code=400, detail="Multi-city search requires at least one segment")
            
            first_segment = segments[0]
            last_segment = segments[-1]
            origin_for_db = convert_city_to_airport(first_segment.origin)
            destination_for_db = convert_city_to_airport(last_segment.destination)
            origin_for_db = sanitize_airport_code(origin_for_db)
            destination_for_db = sanitize_airport_code(destination_for_db)
            
            # Ensure we have valid airport codes
            if not origin_for_db or not destination_for_db:
                raise HTTPException(status_code=400, detail="Could not convert city names to airport codes for multi-city search")
            
            depart_date_for_db = first_segment.depart_date.isoformat() if isinstance(first_segment.depart_date, date) else str(first_segment.depart_date)
            
            # Create search history with proper fields for multi-city
            search_history_data = {
                "id": search_id,
                "origin": origin_for_db,
                "destination": destination_for_db,
                "depart_date": depart_date_for_db,
                "return_date": None,
                "adults": request.adults,
                "children": request.children,
                "seat_class": request.seat_class,
                "fetch_mode": request.fetch_mode,
                "request_data": request_dict,
                "result_data": {
                    "flights": [{'name': getattr(f, 'name', ''), 'departure': getattr(f, 'departure', ''),
                                'arrival': getattr(f, 'arrival', ''), 'duration': getattr(f, 'duration', ''),
                                'stops': getattr(f, 'stops', 0), 'price': getattr(f, 'price', ''),
                                'delay': getattr(f, 'delay', None), 'segment_index': getattr(f, 'segment_index', None),
                                'segment_route': getattr(f, 'segment_route', None)} for f in all_flights],
                    "current_price": getattr(result, 'current_price', 'multi-city'),
                    "total_flights": len(all_flights)
                },
                "timestamp": datetime.now()
            }
            db_search = SearchHistory(**search_history_data)
            db.add(db_search)
            db.commit()
            db.refresh(db_search)
            
            # Return response for multi-city
            response_data = SearchResponse(
                success=True,
                current_price=getattr(result, 'current_price', 'multi-city'),
                total_flights=len(all_flights),
                flights=[FlightResult(
                    name=getattr(f, 'name', ''),
                    departure=getattr(f, 'departure', ''),
                    arrival=getattr(f, 'arrival', ''),
                    duration=getattr(f, 'duration', ''),
                    stops=getattr(f, 'stops', 0),
                    price=getattr(f, 'price', ''),
                    delay=getattr(f, 'delay', None),
                    segment_index=getattr(f, 'segment_index', None),
                    segment_route=getattr(f, 'segment_route', None)
                ) for f in all_flights[:20]],
                search_url=search_url,
                timestamp=datetime.now().isoformat(),
                search_id=search_id
            )
            return response_data
        else:
            # Single segment search (original logic)
            segment = segments[0]

            # Validate dates
            validate_date_not_past(segment.depart_date, "Departure date")
            validate_date_reasonable_future(segment.depart_date, max_days=365, field_name="Departure date")
            
            # For round-trip, check if there's a second segment (return)
            return_date_obj = None
            if request.trip_type == "round-trip" and request.return_date:
                return_date_obj = parse_flexible_date(request.return_date)
                validate_date_not_past(return_date_obj, "Return date")
                validate_date_range(segment.depart_date, return_date_obj, "Return date")
                validate_date_reasonable_future(return_date_obj, max_days=365, field_name="Return date")

            # Convert city names to airport codes
            origin_code = convert_city_to_airport(segment.origin)
            dest_code = convert_city_to_airport(segment.destination)
            origin_code = sanitize_airport_code(origin_code)
            dest_code = sanitize_airport_code(dest_code)
            
            if not validate_airport_code(origin_code):
                raise HTTPException(status_code=400, detail=f"Invalid origin airport code: {origin_code}")
            if not validate_airport_code(dest_code):
                raise HTTPException(status_code=400, detail=f"Invalid destination airport code: {dest_code}")
            
            # Validate origin and destination are different for single segment
            try:
                validate_origin_destination(origin_code, dest_code)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))

            # Convert request to search parameters
            search_params = {
                "origin": origin_code,
                "destination": dest_code,
                "depart_date": segment.depart_date.isoformat(),
                "return_date": return_date_obj.isoformat() if return_date_obj else None,
                "adults": request.adults,
            "children": request.children,
            "infants_in_seat": request.infants_seat,
            "infants_on_lap": request.infants_lap,
            "seat": request.seat_class,
            "max_stops": request.max_stops,
            "fetch_mode": request.fetch_mode
        }

        # Check cache first (cache for 5 minutes for same searches)
        cache_key = generate_cache_key("flight_search", **search_params)
        cached_result = await get_cached(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for search: {cache_key}")
            result = type('Result', (), cached_result)()
        else:
            # Perform search asynchronously in a thread pool
            result = await asyncio.to_thread(search_flights, **search_params)
            
            # Cache the result (only cache successful searches)
            if result and hasattr(result, 'flights'):
                cache_data = {
                    'flights': [{'name': getattr(f, 'name', ''), 'departure': getattr(f, 'departure', ''),
                                'arrival': getattr(f, 'arrival', ''), 'duration': getattr(f, 'duration', ''),
                                'stops': getattr(f, 'stops', 0), 'price': getattr(f, 'price', ''),
                                'delay': getattr(f, 'delay', None)} for f in result.flights],
                    'current_price': getattr(result, 'current_price', 'unknown')
                }
                await set_cached(cache_key, cache_data, ttl=300)  # 5 minutes

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
        # Use origin and destination from the converted codes, not from request (which might be city names)
        search_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{origin_code}_{dest_code}"

        # Store in database
        request_data = request.dict()
        # Convert date objects to strings for JSON serialization
        for key, value in request_data.items():
            if isinstance(value, date):
                request_data[key] = value.isoformat()
        
        result_data = {
                "current_price": getattr(result, 'current_price', 'unknown'),
                "total_flights": len(result.flights),
                "flights": formatted_flights
        }
        create_search_history(db, search_id, request_data, result_data)

        # Send webhooks in background
        webhooks = get_all_webhooks(db)
        if webhooks:
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

            for webhook in webhooks:
                background_tasks.add_task(send_webhook_notification, webhook.url, webhook_payload.dict())
                # Update last_used_at
                webhook.last_used_at = datetime.utcnow()
                db.commit()

        response_data = SearchResponse(
            success=True,
            current_price=getattr(result, 'current_price', 'unknown'),
            total_flights=len(result.flights),
            flights=formatted_flights,
            search_url=search_url,
            timestamp=datetime.now().isoformat(),
            search_id=search_id
        )
        return response_data

    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors) as-is
        raise
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
async def get_search_result(search_id: str, db: Session = Depends(get_db)):
    """Retrieve previous search results by ID"""
    search = get_search_history(db, search_id)
    if not search:
        raise HTTPException(status_code=404, detail="Search not found")

    return {
        "request": search.request_data,
        "result": search.result_data,
        "timestamp": search.timestamp.isoformat()
    }

@app.post("/webhooks", tags=["Webhooks"])
async def register_webhook(request: Request, db: Session = Depends(get_db)):
    """Register a webhook URL for notifications (supports both Form and JSON)"""
    try:
        # Try to get from JSON body first
        try:
            body = await request.json()
            webhook_url = body.get("webhook_url")
        except:
            # Fall back to form data
            form_data = await request.form()
            webhook_url = form_data.get("webhook_url")
        
        if not webhook_url:
            raise HTTPException(status_code=400, detail="webhook_url parameter required")
        
        # Sanitize webhook URL
        webhook_url = sanitize_string_input(webhook_url, max_length=500)
        
        # Basic URL validation
        if not webhook_url.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid webhook URL format")
        
        existing = get_webhook(db, webhook_url)
        if existing:
            return {"message": "Webhook already registered"}
        
        # Create webhook with ID = URL (for uniqueness)
        webhook_id = webhook_url[:200]  # Limit ID length
        create_webhook(db, webhook_id, webhook_url)
        logger.info(f"Registered webhook: {webhook_url}")
        return {"message": "Webhook registered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register webhook: {str(e)}")

@app.delete("/webhooks", tags=["Webhooks"])
async def unregister_webhook(webhook_url: str, db: Session = Depends(get_db)):
    """Unregister a webhook URL"""
    webhook = get_webhook(db, webhook_url)
    if not webhook:
        return {"message": "Webhook not found"}
    
    webhook.active = False
    db.commit()
    logger.info(f"Unregistered webhook: {webhook_url}")
    return {"message": "Webhook unregistered successfully"}

@app.get("/webhooks", tags=["Webhooks"])
async def list_webhooks(db: Session = Depends(get_db)):
    """List all registered webhooks"""
    webhooks = get_all_webhooks(db)
    return {"webhooks": [webhook.url for webhook in webhooks]}

@app.post("/alerts", response_model=PriceAlertResponse, tags=["Price Alerts"])
async def create_price_alert(request: PriceAlertRequest, db: Session = Depends(get_db)):
    """Create a new price alert for flight monitoring"""
    try:
        # Sanitize inputs
        request.origin = sanitize_string_input(request.origin, max_length=100)
        request.destination = sanitize_string_input(request.destination, max_length=100)
        request.email = sanitize_string_input(request.email, max_length=255)
        
        # Validate email
        if not validate_email(request.email):
            raise HTTPException(status_code=400, detail=f"Invalid email format: {request.email}")
        
        # Convert city names to airport codes
        origin_code = convert_city_to_airport(request.origin)
        destination_code = convert_city_to_airport(request.destination)
        
        # Validate origin and destination are different
        try:
            validate_origin_destination(origin_code, destination_code)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Parse the departure date
        depart_date_parsed = parse_flexible_date(request.depart_date)
        
        # Validate dates
        validate_date_not_past(depart_date_parsed, "Departure date")
        validate_date_reasonable_future(depart_date_parsed, max_days=365, field_name="Departure date")

        # Parse return date if provided
        return_date_parsed = None
        if request.return_date:
            return_date_parsed = parse_flexible_date(request.return_date)
            validate_date_not_past(return_date_parsed, "Return date")
            validate_date_range(depart_date_parsed, return_date_parsed, "Return date")
            validate_date_reasonable_future(return_date_parsed, max_days=365, field_name="Return date")
        
        # Validate airport codes
        if not validate_airport_code(origin_code):
            raise HTTPException(status_code=400, detail=f"Invalid origin airport code: {origin_code}")
        if not validate_airport_code(destination_code):
            raise HTTPException(status_code=400, detail=f"Invalid destination airport code: {destination_code}")

        # Generate unique alert ID
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{origin_code}_{destination_code}"

        # Create alert data
        alert_data = {
            "id": alert_id,
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
            "status": "active"
        }

        # Store the alert in database
        db_alert = db_create_price_alert(db, alert_data)

        logger.info(f"Created {request.trip_type} price alert: {alert_id} for {origin_code} → {destination_code}")

        return PriceAlertResponse(
            alert_id=db_alert.alert_id,
            trip_type=db_alert.trip_type,
            origin=db_alert.origin,
            destination=db_alert.destination,
            depart_date=db_alert.depart_date,
            return_date=db_alert.return_date,
            target_price=db_alert.target_price,
            currency=db_alert.currency,
            email=db_alert.email,
            notification_channels=db_alert.notification_channels,
            status=db_alert.status,
            created_at=db_alert.created_at.isoformat()
        )

    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors) as-is
        raise
    except Exception as e:
        logger.error(f"Error creating price alert: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create price alert: {str(e)}"
        )

@app.get("/alerts", tags=["Price Alerts"])
async def list_price_alerts(db: Session = Depends(get_db)):
    """List all active price alerts"""
    alerts = get_all_active_alerts(db)
    
    alerts_list = [
        PriceAlertResponse(
            alert_id=alert.alert_id,
            trip_type=alert.trip_type,
            origin=alert.origin,
            destination=alert.destination,
            depart_date=alert.depart_date,
            return_date=alert.return_date,
            target_price=alert.target_price,
            currency=alert.currency,
            email=alert.email,
            notification_channels=alert.notification_channels,
            status=alert.status,
            created_at=alert.created_at.isoformat()
        )
        for alert in alerts
    ]

    return {"alerts": [alert.dict() for alert in alerts_list]}

@app.delete("/alerts/{alert_id}", tags=["Price Alerts"])
async def delete_price_alert(alert_id: str, db: Session = Depends(get_db)):
    """Delete a price alert by ID"""
    alert = get_price_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Mark as inactive instead of deleting (for audit purposes)
    alert.status = "inactive"
    alert.deleted_at = datetime.utcnow()
    db.commit()

    logger.info(f"Deleted price alert: {alert_id}")

    return {"message": "Alert deleted successfully"}

# NaturalLanguageQuery is now in api.models

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
            # Return a graceful error instead of failing
            return ErrorResponse(
                success=False,
                error=f"{request.provider.upper()} API key required. Set {env_var_map.get(request.provider, 'API_KEY')} environment variable or provide in request.",
                error_code="AI_API_KEY_MISSING",
                timestamp=datetime.now().isoformat()
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

        # Perform search asynchronously in a thread pool
        result = await asyncio.to_thread(search_flights, **search_params)

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

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup."""
    init_db()
    logger.info("✅ Database initialized")


if __name__ == "__main__":
    # Simple startup test
    print("🚀 Starting FlyMind API...")
    print(f"📦 Flights module available: {FLIGHTS_AVAILABLE}")
    port = int(os.getenv("PORT", 8001))
    print(f"📡 Listening on port {port}")
    print("🏥 Health check available at: /health")
    print("📖 API docs available at: /docs")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
