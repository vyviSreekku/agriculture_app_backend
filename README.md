# Agri Advisory Backend

This is the backend service for the Agricultural Advisory application. It provides weather data, market prices, crop recommendations, fertilizer guidance and other agricultural information to the mobile app.

## Environment Setup

The application uses environment variables for configuration. Create a `.env` file in the root directory with the following variables:

```
DATABASE_URL=postgresql://user:password@localhost:5432/agri_advisory
GOOGLE_WEATHER_API_KEY=your_google_api_key
MANDI_API_KEY=your_mandi_api_key
```

### Azure database (App Service)

In Azure App Service, set these under **Configuration → Application settings**.

Option A (recommended): set a single `DATABASE_URL`.

Example for **Azure Database for PostgreSQL (Flexible Server)**:

```
DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@YOURSERVER.postgres.database.azure.com:5432/DATABASE?sslmode=require
```

Notes:
- Azure Postgres typically requires `sslmode=require`.
- The username is often `USERNAME@YOURSERVER`.

Option B: set parts and let the app build the URL:

```
DB_SCHEME=postgresql+psycopg2
DB_HOST=YOURSERVER.postgres.database.azure.com
DB_PORT=5432
DB_NAME=DATABASE
DB_USER=USERNAME@YOURSERVER
DB_PASSWORD=PASSWORD
DB_SSLMODE=require
```

## Available APIs

- Weather API: `/weather/*`
- Market Prices API: `/market/*`
- Community Posts API: `/community/*`
- Crop Recommendation API: `/crops/recommend` (POST)
- Fertilizer Recommendation API: `/fertilizer/recommend` (POST)
- Soil Analysis API: `/soil/analyze` (POST - multipart/form-data with image)

For more details about specific endpoints, refer to the documentation in the `docs/` folder.

## Firebase Phone Auth (OTP) login/signup

This backend supports login/signup using **Firebase Phone Authentication**.

High-level flow:
1. Client (web/mobile) completes Firebase Phone OTP verification.
2. Client obtains a Firebase **ID token**.
3. Client calls the backend endpoint with `Authorization: Bearer <ID_TOKEN>`.
4. Backend verifies the token using **Firebase Admin** and uses the verified `phone_number` claim as the user identity.

Note: OTP is handled by Firebase on the client. The backend does not send SMS OTP itself.

### Backend endpoint

- `POST /users/firebase/login`
	- Header: `Authorization: Bearer <FIREBASE_ID_TOKEN>`
	- Body (optional): `full_name`, `location_name`, `location_state`, `location_district`

### Firebase Admin credentials (required)

The backend must be configured with a **Firebase Admin service account JSON**.
The Firebase *web* config (`apiKey`, `authDomain`, etc.) is **frontend-only** and cannot be used to verify tokens on the backend.

Set one of these environment variables (recommended for Azure App Service: set in **Configuration → Application settings**):

Option A (recommended): point to a JSON file on disk
```
FIREBASE_SERVICE_ACCOUNT_FILE=/home/site/wwwroot/firebase-service-account.json
```

Option B: provide the JSON content as a single-line string
```
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

## Running the Application

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the FastAPI server:
```bash
uvicorn app.main:app --reload
```

3. Access the API documentation:
```
http://localhost:8000/docs
```

## API Documentation

- Weather API: See `docs/WEATHER_API_USAGE.md`
- Market API: See `docs/MARKET_API_USAGE.md`