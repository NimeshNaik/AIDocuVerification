from supabase import create_client, Client

from app.core.config import get_settings

settings = get_settings()

# Supabase client singleton
_supabase_client: Client = None


def get_supabase() -> Client:
    """Get or create Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(settings.supabase_url, settings.supabase_key)
    return _supabase_client


# Supabase service role client singleton (bypasses RLS)
_supabase_service_client: Client = None


def get_supabase_service_client() -> Client:
    """Get or create Supabase service role client instance."""
    global _supabase_service_client
    if _supabase_service_client is None:
        _supabase_service_client = create_client(
            settings.supabase_url, 
            settings.supabase_service_role_key
        )
    return _supabase_service_client
