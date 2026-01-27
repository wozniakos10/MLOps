from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    open_router_api_key: str
    open_weather_api_key: str
    tavily_api_key: str
    guardrails_api_key: str
    openai_api_key: str = "EMPTY"
    gemini_api_key: str
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    gemini_model: str = "gemini-3-flash-preview"

    open_router_base_url: str = "https://openrouter.ai/api/v1"
    open_router_model: str = "gpt-oss-120b"

    openweather_base_url: str = "https://api.openweathermap.org"
    openweather_historic_base_url: str = "https://history.openweathermap.org"

    # local mcp server
    weather_mcp_url: str = "http://localhost:8001/mcp"

    # remote mcp server
    tavily_mcp_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
