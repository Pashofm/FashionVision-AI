import pytz
from datetime import datetime, timezone
from typing import Optional

SERVER_TIMEZONE = pytz.timezone('America/Mazatlan')

def get_current_utc_time() -> datetime:
    return datetime.now(timezone.utc)

def get_server_time() -> datetime:
    return datetime.now(SERVER_TIMEZONE)

def utc_to_local(utc_dt: datetime, client_tz: str = None) -> datetime:
    if utc_dt is None:
        return None
    if not utc_dt.tzinfo:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    if client_tz:
        try:
            client_timezone = pytz.timezone(client_tz)
            return utc_dt.astimezone(client_timezone)
        except Exception:
            pass
    return utc_dt.astimezone(SERVER_TIMEZONE)

def local_to_utc(local_dt: datetime, timezone_str: str = None) -> datetime:
    if local_dt is None:
        return None
    if timezone_str:
        try:
            tz = pytz.timezone(timezone_str)
            if local_dt.tzinfo is None:
                local_dt = tz.localize(local_dt)
            return local_dt.astimezone(timezone.utc)
        except Exception:
            pass
    if local_dt.tzinfo is None:
        return local_dt.replace(tzinfo=SERVER_TIMEZONE).astimezone(timezone.utc)
    return local_dt.astimezone(timezone.utc)

def get_timezone_from_request(accept_language: str = None, timezone_header: str = None) -> Optional[str]:
    if timezone_header:
        return timezone_header
    if accept_language:
        try:
            lang = accept_language.split(',')[0]
            if '-' in lang:
                parts = lang.split('-')
                if len(parts) >= 2:
                    country_code = parts[-1].upper()
                    timezone_map = {
                        'MX': 'America/Mexico_City',
                        'US': 'America/New_York',
                        'ES': 'Europe/Madrid',
                        'AR': 'America/Buenos_Aires',
                        'CO': 'America/Bogota',
                        'CL': 'America/Santiago',
                        'PE': 'America/Lima',
                    }
                    if country_code in timezone_map:
                        return timezone_map[country_code]
        except Exception:
            pass
    return None

def format_datetime_for_response(dt: datetime, client_tz: str = None) -> str:
    local_dt = utc_to_local(dt, client_tz)
    return local_dt.isoformat()

def get_all_timezones() -> list:
    return pytz.all_timezones