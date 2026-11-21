from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://hospital_admin:dev@localhost:5433/carisehat"
    fuseki_url: str = "http://localhost:3030/hospital"
    base_uri: str = "http://localhost:8000"          # dasar URI sumber daya (/rs/{id}, dst.)
    onto_ns: str = "http://carisehat.id/ontology/"
    auto_load_rdf: bool = True                        # muat semantic/rdf/* ke Fuseki bila dataset kosong
    rdf_dir: str = "/semantic/rdf"
    frontend_dir: str = "/frontend"
    migrations_dir: str = "/database/migrations"      # folder migrasi SQL (di-mount oleh docker-compose)

    # --- API Keys Eksternal ---
    google_maps_api_key: str = ""   # Google Maps JavaScript API key
    booking_access_key: str = ""  # Server-side operator key; never expose in frontend

    # --- Sistem Admin (MSBD) ---
    admin_username: str = "admin"            # akun admin awal (dibuat otomatis bila tabel admin kosong)
    admin_password: str = "admin12345"       # GANTI di .env untuk selain demo lokal
    admin_session_hours: int = 8             # masa berlaku token login admin
    admin_max_failed_logins: int = 5         # percobaan gagal sebelum akun dikunci sementara
    admin_lock_minutes: int = 15
    # Blueprint: Idempotency-Key yang sama -> 409. Default False = replay (kembalikan booking
    # asli) agar retry jaringan di frontend aman. Set True untuk perilaku 409 ketat.
    idempotency_replay_as_409: bool = False


settings = Settings()
