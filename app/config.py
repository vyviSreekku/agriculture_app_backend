import os
from dotenv import load_dotenv
from urllib.parse import quote_plus, urlparse, parse_qsl, urlencode, urlunparse

# Load environment variables from .env file
load_dotenv()

class Settings:
    def __init__(self):
        self.DATABASE_URL = self._build_database_url()
        self.GOOGLE_WEATHER_API_KEY = os.getenv("GOOGLE_WEATHER_API_KEY")
        self.MANDI_API_KEY = os.getenv("MANDI_API_KEY")

    def _build_database_url(self) -> str:
        """Return a SQLAlchemy database URL.

        Priority:
        1) DATABASE_URL (recommended for Azure)
        2) DB_* parts (DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, DB_SCHEME)
        3) PG* parts (PGHOST, PGDATABASE, PGUSER, PGPASSWORD, PGPORT)
        3) SQLITE_URL (fallback) else sqlite:///./app.db
        """

        explicit = (os.getenv("DATABASE_URL") or "").strip()
        if explicit:
            return self._ensure_azure_sslmode(explicit)

        host = (os.getenv("DB_HOST") or "").strip()
        name = (os.getenv("DB_NAME") or "").strip()
        user = (os.getenv("DB_USER") or "").strip()
        password = (os.getenv("DB_PASSWORD") or os.getenv("DB_PASS") or "").strip()
        port = (os.getenv("DB_PORT") or "").strip()

        if host and name and user:
            scheme = (os.getenv("DB_SCHEME") or "postgresql+psycopg2").strip()
            default_port = "5432" if scheme.startswith("postgres") else ""
            port_part = port or default_port

            user_enc = quote_plus(user)
            pwd_enc = quote_plus(password)
            host_enc = host
            name_enc = quote_plus(name)

            auth = user_enc
            if password:
                auth = f"{user_enc}:{pwd_enc}"

            netloc = f"{auth}@{host_enc}"
            if port_part:
                netloc = f"{netloc}:{port_part}"

            url = f"{scheme}://{netloc}/{name_enc}"
            return self._ensure_azure_sslmode(url)

        # Fallback: accept conventional libpq-style environment variables.
        # This is commonly used in Azure App Service configuration.
        pghost = (os.getenv("PGHOST") or "").strip()
        pgdb = (os.getenv("PGDATABASE") or "").strip()
        pguser = (os.getenv("PGUSER") or "").strip()
        pgpassword = (os.getenv("PGPASSWORD") or "").strip()
        pgport = (os.getenv("PGPORT") or "").strip()

        if pghost and pgdb and pguser:
            scheme = (os.getenv("DB_SCHEME") or "postgresql+psycopg2").strip()
            default_port = "5432" if scheme.startswith("postgres") else ""
            port_part = pgport or default_port

            user_enc = quote_plus(pguser)
            pwd_enc = quote_plus(pgpassword)
            name_enc = quote_plus(pgdb)

            auth = user_enc
            if pgpassword:
                auth = f"{user_enc}:{pwd_enc}"

            netloc = f"{auth}@{pghost}"
            if port_part:
                netloc = f"{netloc}:{port_part}"

            url = f"{scheme}://{netloc}/{name_enc}"
            return self._ensure_azure_sslmode(url)

        sqlite_url = (os.getenv("SQLITE_URL") or "sqlite:///./app.db").strip()
        return sqlite_url

    def _ensure_azure_sslmode(self, url: str) -> str:
        """Ensure sslmode=require for Azure Postgres unless already set.

        Azure Database for PostgreSQL typically requires SSL.
        """

        try:
            parsed = urlparse(url)
        except Exception:
            return url

        scheme = (parsed.scheme or "").lower()
        host = (parsed.hostname or "").lower()

        force_ssl = scheme.startswith("postgres") and (
            host.endswith(".postgres.database.azure.com")
            or (os.getenv("DB_SSLMODE") or "").strip().lower() in {"require", "verify-full", "verify-ca"}
        )

        if not force_ssl:
            return url

        query_items = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if "sslmode" in query_items and query_items["sslmode"]:
            return url

        query_items["sslmode"] = (os.getenv("DB_SSLMODE") or "require").strip() or "require"
        new_query = urlencode(query_items)
        return urlunparse(parsed._replace(query=new_query))

settings = Settings()
