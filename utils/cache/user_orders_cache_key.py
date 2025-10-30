def user_orders_cache_key(user_id: int) -> str:
    """Generate a consistent cache key for a user's orders"""
    return f"user_orders_{user_id}"