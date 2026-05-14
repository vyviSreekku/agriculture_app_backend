# Market API Usage

## Endpoint

`GET /market/prices`

Returns mandi (agricultural market) prices from the Data.gov.in source.

## Query Parameters

- `state` (optional): Filter by state name.
- `district` (optional): Filter by district name.
- `crop` (optional): Filter by crop/commodity name.
- `arrival_date` (optional): Filter by exact arrival date in `dd/mm/YYYY` format.
- `limit_days` (optional, default `1`, range `1-30`): Accepted for backward compatibility in the route. Current service logic performs a single fetch call and does not iterate multiple days.
- `limit` (optional, default `15`, range `1-100`): Maximum number of records returned after processing.

## Response Shape

```json
{
  "success": true,
  "data": [
    {
      "market": "Kuthuparambu",
      "commodity": "Tomato",
      "prices": [
        {
          "date": "31 Aug 2024",
          "raw_date": "31/08/2024",
          "variety": "Tomato",
          "grade": "FAQ",
          "min_price": "2000",
          "max_price": "2400",
          "modal_price": "2200",
          "state": "Kerala",
          "district": "Kannur"
        }
      ]
    }
  ],
  "metadata": {
    "total_records": 1959,
    "fetched_records": 10,
    "updated_date": "2026-04-15T23:24:34Z",
    "state": "Kerala",
    "district": "Kannur",
    "crop": "Tomato"
  }
}
```

## Sorting Behavior

- Records are sorted by `Arrival_Date` in descending order (newest first) before grouping.
- Grouping is done by `Market` + `Commodity`.

## Examples

### PowerShell

```powershell
curl.exe -G "http://127.0.0.1:8000/market/prices" `
  --data-urlencode "state=Kerala" `
  --data-urlencode "district=Kannur" `
  --data-urlencode "crop=Tomato" `
  --data-urlencode "limit=15"
```

### Bash

```bash
curl -G "http://127.0.0.1:8000/market/prices" \
  --data-urlencode "state=Kerala" \
  --data-urlencode "district=Kannur" \
  --data-urlencode "crop=Tomato" \
  --data-urlencode "limit=15"
```

## Notes

- This endpoint depends on Data.gov.in API availability and performance.
- A successful API metadata `updated_date` does not guarantee that underlying market records are from the current date.
- If no records are returned for your filters, broaden the filters (for example, remove `district` first).
