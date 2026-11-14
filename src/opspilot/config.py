from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="OPSPILOT_")

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "llama3.2:3b"

    # USD per 1 million tokens. Local models are free; set real prices for a hosted provider.
    llm_input_price_per_mtok: float = 0.0
    llm_output_price_per_mtok: float = 0.0


settings = Settings()
