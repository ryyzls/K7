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


settings = Settings()
