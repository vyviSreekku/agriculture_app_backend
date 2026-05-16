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