def category_cache_key(category_name: str) -> str:
    """Generate a consistent cache key for a category."""
    return f"products_in_{category_name.lower().replace(' ', '-')}"
