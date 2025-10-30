def remove_jwt_cookies(response):
    """Remove JWT tokens from cookies."""

    cookie_settings = { "path": "/", "samesite": "None" }

    response.delete_cookie(
        key="at",
        **cookie_settings
    )
    response.delete_cookie(
        key="rt", 
        **cookie_settings
    )
    response.delete_cookie(
        key="loggedin", 
        **cookie_settings
    )
    