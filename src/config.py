from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    DATABASE_URL: str
    DOMAIN: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


# print("DATAURL: ", Setting.DATABASE_URL)
# print("DOMURL: ", Setting.DOMAIN)

Config = Setting()
