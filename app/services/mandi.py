import json
import subprocess
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Union
from ..config import settings

# API Configuration
BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

def get_mandi_prices(
    state: Optional[str] = None,
    district: Optional[str] = None,
    commodity: Optional[str] = None,
    arrival_date: Optional[str] = None,
    api_key: str = None,
    format: str = "json",
    offset: int = 0,
    limit: int = 10,
    sort_by: Optional[str] = "Arrival_Date",
) -> Union[Dict[str, Any], str, None]:
    """
    Fetch agricultural market prices from the Mandi API.
    
    Parameters:
    - state: Filter by state
    - district: Filter by district
    - commodity: Filter by commodity (crop)
    - arrival_date: Filter by arrival date
    - api_key: API key for authentication
    - format: Output format (json, xml, csv)
    - offset: Number of records to skip
    - limit: Maximum number of records to return
    - sort_by: Field name to sort descending (default: Arrival_Date)
    Returns:
    - The API response in the specified format
    """
    # Use the API key from settings if not provided
    if api_key is None:
        api_key = settings.MANDI_API_KEY
        
    params = {
        "api-key": api_key,
        "format": format,
        "offset": offset,
    }
    
    # Add filters if provided
    if state:
        params["filters[State]"] = state
    if district:
        params["filters[District]"] = district
    if commodity:
        params["filters[Commodity]"] = commodity
    if arrival_date:
        params["filters[Arrival_Date]"] = arrival_date
    
    try:
        curl_command = [
            "curl.exe",
            "-sS",
            "-G",
            BASE_URL,
            "--data-urlencode",
            f"api-key={api_key}",
            "--data-urlencode",
            f"format={format}",
            "--data-urlencode",
            f"offset={offset}",
            "--data-urlencode",
            f"limit={limit}",
        ]

        if state:
            curl_command.extend(["--data-urlencode", f"filters[State]={state}"])
        if district:
            curl_command.extend(["--data-urlencode", f"filters[District]={district}"])
        if commodity:
            curl_command.extend(["--data-urlencode", f"filters[Commodity]={commodity}"])
        if arrival_date:
            curl_command.extend(["--data-urlencode", f"filters[Arrival_Date]={arrival_date}"])
        if sort_by:
            curl_command.extend(["--data-urlencode", f"sort[{sort_by}]=desc"])

        print(f"Prepared request URL: {BASE_URL}?api-key={api_key}&format={format}&offset={offset}&limit={limit}")

        completed = subprocess.run(
            curl_command,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )

        if completed.returncode != 0:
            error_message = completed.stderr.strip() or completed.stdout.strip() or f"curl exited with code {completed.returncode}"
            print(f"Error fetching mandi data: {error_message}")
            return None

        if format == "json":
            return json.loads(completed.stdout)
        return completed.stdout
    except subprocess.TimeoutExpired as e:
        print(f"Error fetching mandi data (timeout): {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing mandi JSON: {e}")
        return None

def process_mandi_data(data: Dict[str, Any], max_records: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Process the mandi API response and return structured data.
    
    Parameters:
    - data: The API response data (in JSON format)
    - max_records: Maximum number of records to process
    
    Returns:
    - List of processed market price records sorted by date descending
    """
    processed_data = []
    
    # Check if data is valid
    if not data or not isinstance(data, dict):
        return processed_data
    
    # Check for error in the API response
    if "error" in data:
        print(f"API Error: {data.get('error', {}).get('message', 'Unknown error')}")
        return processed_data
    
    # Check if records exist in the data
    records = data.get("records", [])
    if not records:
        return processed_data
    
    # Sort all records by arrival date (newest first) before processing
    sorted_all_records = sorted(
        records,
        key=lambda x: datetime.strptime(x.get("Arrival_Date", "01/01/2000"), "%d/%m/%Y"),
        reverse=True
    )
    
    # Limit the number of records to process
    if max_records and max_records < len(sorted_all_records):
        records_to_process = sorted_all_records[:max_records]
    else:
        records_to_process = sorted_all_records
    
    # Group records by Market and Commodity for better organization
    market_commodity_groups = {}
    for record in records_to_process:
        market = record.get("Market", "Unknown Market")
        commodity = record.get("Commodity", "Unknown Commodity")
        key = f"{market}|{commodity}"
        
        if key not in market_commodity_groups:
            market_commodity_groups[key] = []
        
        market_commodity_groups[key].append(record)
    
    # Process each group
    for key, group_records in market_commodity_groups.items():
        parts = key.split("|", 1)
        market = parts[0]
        commodity = parts[1] if len(parts) > 1 else "Unknown"
        
        group_data = {
            "market": market,
            "commodity": commodity,
            "prices": []
        }
        
        for record in group_records:
            # Format date for better readability
            arrival_date = record.get("Arrival_Date", "N/A")
            try:
                date_obj = datetime.strptime(arrival_date, "%d/%m/%Y")
                formatted_date = date_obj.strftime("%d %b %Y")
            except:
                formatted_date = arrival_date
            
            price_data = {
                "date": formatted_date,
                "raw_date": arrival_date,
                "variety": record.get("Variety", "N/A"),
                "grade": record.get("Grade", "N/A"),
                "min_price": record.get("Min_Price", "N/A"),
                "max_price": record.get("Max_Price", "N/A"),
                "modal_price": record.get("Modal_Price", "N/A"),
                "state": record.get("State", "N/A"),
                "district": record.get("District", "N/A")
            }
            group_data["prices"].append(price_data)
        
        processed_data.append(group_data)
    
    return processed_data

async def get_crop_prices(
    state: Optional[str] = None,
    district: Optional[str] = None,
    crop: Optional[str] = None,
    arrival_date: Optional[str] = None,
    limit_days: int = 1,
    limit: int = 15,
) -> Dict[str, Any]:
    """
    Get crop prices from the Mandi API as a service for the FastAPI backend.
    Simple single-call approach matching the curl logic.
    
    Parameters:
    - state: Filter by state
    - district: Filter by district
    - crop: Filter by crop name (commodity)
    - arrival_date: Optional specific arrival date in dd/mm/YYYY format
    - limit_days: Ignored (kept for backward compatibility)
    - limit: Maximum number of records to return (default: 15)
    
    Returns:
    - Dictionary containing processed market price data and metadata
    """
    result = {
        "success": False,
        "data": [],
        "metadata": {
            "total_records": 0,
            "fetched_records": 0,
            "updated_date": None,
            "state": state,
            "district": district,
            "crop": crop,
        },
    }
    
    # Simple single API call with provided filters
    data = get_mandi_prices(
        state=state,
        district=district,
        commodity=crop,
        arrival_date=arrival_date,
        limit=limit,
        sort_by="Arrival_Date",
    )
    
    # Check if we got valid data
    if data and isinstance(data, dict) and data.get("records") and not data.get("error"):
        result["success"] = True
        result["metadata"]["total_records"] = data.get("total", 0)
        result["metadata"]["fetched_records"] = len(data.get("records", []))
        result["metadata"]["updated_date"] = data.get("updated_date", None)
        # Process with limit
        result["data"] = process_mandi_data(data, max_records=limit)
    
    return result
