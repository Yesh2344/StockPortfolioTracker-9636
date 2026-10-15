import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass(frozen=True)
class Config:
    """Application configuration loaded from environment variables."""
    alpha_vantage_api_key: str = os.getenv("ALPHA_VANTAGE_API_KEY", "")

    @property
    def is_valid(self) -> bool:
        """Check whether required configuration values are present."""
        return bool(self.alpha_vantage_api_key)


# Export a singleton configuration instance
config = Config()