import hashlib
import logging
from app.core.redis import redis_cache

logger = logging.getLogger(__name__)

async def get_demo_message_count(ip: str, session_id: str) -> int:
    """
    Retrieves the maximum message count between the IP and Session ID.
    """
    try:
        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()
        ip_key = f"demo:ip:{ip_hash}"
        session_key = f"demo:session:{session_id}"
        
        ip_val_str = await redis_cache.get(ip_key)
        session_val_str = await redis_cache.get(session_key)
        
        ip_val = int(ip_val_str) if ip_val_str else 0
        session_val = int(session_val_str) if session_val_str else 0
        
        return max(ip_val, session_val)
    except Exception as e:
        logger.error(f"Error checking demo message count: {e}")
        return 0

async def check_and_increment_demo_limits(ip: str, session_id: str) -> tuple[bool, int]:
    """
    Checks if the IP or session limit of 5 messages per 24 hours has been exceeded.
    If not exceeded, increments both counters and returns (True, current_max_count).
    If exceeded, returns (False, current_max_count).
    """
    try:
        ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()
        ip_key = f"demo:ip:{ip_hash}"
        session_key = f"demo:session:{session_id}"
        
        ip_val_str = await redis_cache.get(ip_key)
        session_val_str = await redis_cache.get(session_key)
        
        ip_val = int(ip_val_str) if ip_val_str else 0
        session_val = int(session_val_str) if session_val_str else 0
        
        max_val = max(ip_val, session_val)
        
        if max_val >= 5:
            return False, max_val
        
        # Increment both counters. expire=86400 (24h)
        new_ip_val = await redis_cache.incr(ip_key, expire=86400)
        new_session_val = await redis_cache.incr(session_key, expire=86400)
        
        curr_ip = new_ip_val if new_ip_val is not None else (ip_val + 1)
        curr_session = new_session_val if new_session_val is not None else (session_val + 1)
        
        return True, max(curr_ip, curr_session)
    except Exception as e:
        logger.error(f"Error in rate limiting check/increment: {e}")
        # Default to safe fallback or pass through. Let's allow but count as 0.
        return True, 0
