import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Always use the current working directory as the base directory
BASE_DIR = Path.cwd()
logger.info(f"Using current working directory as base: {BASE_DIR}")

# Load .env from the base directory
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"✅ Successfully loaded environment variables from: {env_path}")
else:
    logger.warning(f"⚠️ No .env file found at: {env_path}")
    logger.info("Using default environment variables or system environment variables")

# Validate critical environment variables
critical_env_vars = {
    "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
    "REDIS_HOST": os.getenv("REDIS_HOST"),
    "CELERY_BROKER_URL": os.getenv("CELERY_BROKER_URL"),
    "CELERY_RESULT_BACKEND": os.getenv("CELERY_RESULT_BACKEND"),
    "POSTGRES_USER": os.getenv("POSTGRES_USER"),
    "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
    "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
}

# Add MinIO settings if storage provider is minio
if os.getenv("STORAGE_PROVIDER", "local").lower() == "minio":
    critical_env_vars.update({
        "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT"),
        "MINIO_ACCESS_KEY": os.getenv("MINIO_ACCESS_KEY"),
        "MINIO_SECRET_KEY": os.getenv("MINIO_SECRET_KEY"),
        "MINIO_BUCKET": os.getenv("MINIO_BUCKET"),
    })

for var_name, var_value in critical_env_vars.items():
    if var_value:
        logger.info(f"✅ Environment variable loaded: {var_name}")
    else:
        logger.warning(f"⚠️ Missing environment variable: {var_name}")


class ProjectConfig(BaseModel):
    name: str = "Simba"
    version: str = "1.0.0"
    api_version: str = "/api/v1"


class PathConfig(BaseModel):
    base_dir: Path = Field(default_factory=lambda: BASE_DIR)
    faiss_index_dir: Path = Field(default="vector_stores/faiss_index")
    vector_store_dir: Path = Field(default="vector_stores")
    upload_dir: Path = Field(default="uploads")
    temp_dir: Path = Field(default="temp")

    def __init__(self, **data):
        super().__init__(**data)
        # Resolve all paths relative to base directory
        self.faiss_index_dir = self.base_dir / self.faiss_index_dir
        self.vector_store_dir = self.base_dir / self.vector_store_dir
        self.upload_dir = self.base_dir / self.upload_dir
        self.temp_dir = self.base_dir / self.temp_dir

        # Create directories if they don't exist
        for path in [
            self.faiss_index_dir,
            self.vector_store_dir,
            self.upload_dir,
            self.temp_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {path}")


class LLMConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str = Field(default="openai")
    model_name: str = Field(default="gpt-4")
    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY", ""),
        description="OpenAI API key from environment variables",
    )
    base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for LLM service (e.g., Ollama server)",
    )
    temperature: float = Field(default=0.0)
    streaming: bool = Field(default=True)
    max_tokens: Optional[int] = None
    additional_params: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    provider: str = "openai"
    model_name: str = "text-embedding-3-small"
    device: str = "cpu"

    additional_params: Dict[str, Any] = Field(default_factory=dict)


class VectorStoreConfig(BaseModel):
    provider: str = "faiss"
    collection_name: str = "migi_collection"
    additional_params: Dict[str, Any] = Field(default_factory=dict)


class ChunkingConfig(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 50


class RetrievalConfig(BaseModel):
    """Configuration for document retrieval."""

    method: str = "default"  # default, semantic, keyword, hybrid, ensemble, reranked

    # Default parameters for all retrieval methods
    k: int = 5

    # Method-specific parameters
    params: Dict[str, Any] = Field(
        default_factory=lambda: {
            # Semantic retrieval parameters
            "score_threshold": 0.5,
            # Hybrid retrieval parameters
            "prioritize_semantic": True,
            # Ensemble retrieval parameters
            "weights": [0.5, 0.5],  # Default weights for default + semantic
            # Reranking parameters (future implementation)
            "reranker_model": "colbert",
            "reranker_threshold": 0.7,
        }
    )


class DatabaseConfig(BaseModel):
    provider: str = "litedb"  # or "sqlite"
    additional_params: Dict[str, Any] = Field(default_factory=dict)


class CelerySettings(BaseModel):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"


class StorageSettings(BaseSettings):
    """Storage configuration settings"""
    provider: str = Field(
        default="local",
        description="Storage provider type: 'local', 'minio', or 'supabase'"
    )
    minio_endpoint: Optional[str] = Field(
        default=None,
        description="MinIO server endpoint",
        env="MINIO_ENDPOINT"
    )
    minio_access_key: Optional[str] = Field(
        default=None,
        description="MinIO access key",
        env="MINIO_ACCESS_KEY"
    )
    minio_secret_key: Optional[str] = Field(
        default=None,
        description="MinIO secret key",
        env="MINIO_SECRET_KEY"
    )
    minio_bucket: Optional[str] = Field(
        default=None,
        description="MinIO bucket name",
        env="MINIO_BUCKET"
    )
    minio_secure: bool = Field(
        default=False,
        description="Use secure connection to MinIO",
        env="MINIO_SECURE"
    )
    supabase_bucket: Optional[str] = Field(
        default="simba-bucket",
        description="Supabase storage bucket name",
        env="SUPABASE_STORAGE_BUCKET"
    )


class SupabaseSettings(BaseSettings):
    """Supabase configuration settings"""
    url: str = Field(
        default="",
        description="Supabase project URL",
        env="SUPABASE_URL"
    )
    key: str = Field(
        default="",
        description="Supabase anon/public key",
        env="SUPABASE_ANON_KEY,ANON_KEY"  # Try both keys for compatibility
    )
    service_role_key: str = Field(
        default="",
        description="Supabase service role key for admin access",
        env="SERVICE_ROLE_KEY"
    )
    jwt_secret: str = Field(
        default="",
        description="Supabase JWT secret for token verification",
        env="JWT_SECRET"
    )


class PostgresSettings(BaseSettings):
    """PostgreSQL database settings"""
    model_config = ConfigDict(env_prefix="", env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    user: str = Field(
        default="postgres",
        description="PostgreSQL username",
        env="POSTGRES_USER"
    )
    password: str = Field(
        default="",
        description="PostgreSQL password",
        env="POSTGRES_PASSWORD"
    )
    host: str = Field(
        default="localhost",
        description="PostgreSQL host",
        env="POSTGRES_HOST"
    )
    port: str = Field(
        default="5432",
        description="PostgreSQL port",
        env="POSTGRES_PORT"
    )
    db: str = Field(
        default="postgres",
        description="PostgreSQL database name",
        env="POSTGRES_DB"
    )
    connection_string: str = Field(
        default="",
        description="Full PostgreSQL connection string (if set, overrides individual settings)",
        env="POSTGRES_CONNECTION_STRING,SUPABASE_CONNECTION_STRING"
    )
    
    @property
    def get_connection_string(self) -> str:
        """Generate connection string if not explicitly provided"""
        if self.connection_string:
            return self.connection_string
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"
        
    def __init__(self, **kwargs):
        """Initialize with priority to environment variables"""
        # Load from environment first
        env_values = {}
        for field_name, field in self.__class__.model_fields.items():
            env_var = field.json_schema_extra.get("env") if field.json_schema_extra else None
            if isinstance(env_var, str):
                env_vars = [env_var]
            elif isinstance(env_var, (list, tuple)):
                env_vars = env_var
            else:
                env_vars = []
                
            for var in env_vars:
                value = os.getenv(var)
                if value is not None:
                    env_values[field_name] = value
                    break
        
        # Override with kwargs if provided
        env_values.update(kwargs)
        
        # Initialize with combined values
        super().__init__(**env_values)


class Settings(BaseSettings):
    """Application settings"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    paths: PathConfig = Field(default_factory=PathConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    celery: CelerySettings = Field(default_factory=CelerySettings)
    storage: StorageSettings = StorageSettings()
    supabase: SupabaseSettings = SupabaseSettings()
    postgres: PostgresSettings = PostgresSettings()

    @field_validator("celery")
    @classmethod
    def validate_celery(cls, v, values):
        if not v.broker_url:
            raise ValueError("Celery broker URL is required")
        return v

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from config.yaml in the base directory."""
        config_file = BASE_DIR / "config.yaml"

        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found at {config_file}. "
                "Please ensure config.yaml exists in the project root directory."
            )

        logger.info(f"Loading configuration from {config_file}")
        with open(config_file, "r") as f:
            config_data = yaml.safe_load(f) or {}

        # Ensure base_dir is set to BASE_DIR
        if "paths" not in config_data:
            config_data["paths"] = {}
        config_data["paths"]["base_dir"] = str(BASE_DIR)

        return cls(**config_data)


# Create global settings instance
try:
    settings = Settings.load_from_yaml()
except FileNotFoundError as e:
    logger.error(str(e))
    raise
except Exception as e:
    logger.error(f"Failed to load configuration file: {e}")
    raise

# # Ensure directories exist
# def ensure_directories():
#     """Create necessary directories if they don't exist."""
#     directories = [
#         settings.paths.faiss_index_dir,
#         settings.paths.vector_store_dir
#     ]

#     for directory in directories:
#         directory.mkdir(parents=True, exist_ok=True)
#         logger.info(f"Ensured directory exists: {directory}")

# # Create directories on import
# ensure_directories()

if __name__ == "__main__":
    print("\nCurrent Settings:")
    print(f"Base Directory: {settings.paths.base_dir}")
    print(f"Config file location: {Path.cwd() / 'config.yaml'}")
    print(f".env file location: {BASE_DIR / '.env'}")
    print(f"Vector Store Directory: {settings.paths.vector_store_dir}")
    print(f"Vector Store Provider: {settings.vector_store.provider}")

    print("=" * 50)
    print("Starting SIMBA Application")
    print("=" * 50)

    # Project Info
    print(f"Project Name: {settings.project.name}")
    print(f"Version: {settings.project.version}")

    # Model Configurations
    print("\nModel Configurations:")
    print(f"LLM Provider: {settings.llm.provider}")
    print(f"LLM Model: {settings.llm.model_name}")
    print(f"Embedding Provider: {settings.embedding.provider}")
    print(f"Embedding Model: {settings.embedding.model_name}")
    print(f"Embedding Device: {settings.embedding.device}")

    # Vector Store & Database
    print("\nStorage Configurations:")
    print(f"Vector Store Provider: {settings.vector_store.provider}")
    print(f"Database Provider: {settings.database.provider}")

    # Paths
    print("\nPaths:")
    print(f"Base Directory: {settings.paths.base_dir}")
    print(f"Upload Directory: {settings.paths.upload_dir}")
    print(f"Vector Store Directory: {settings.paths.vector_store_dir}")

    print("=" * 50)
