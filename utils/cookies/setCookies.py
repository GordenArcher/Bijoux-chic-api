def set_jwt_cookies(response, refresh, access):
    """Attach JWT tokens to cookies."""
    response.set_cookie(
        key="at",
        value=str(access),
        httponly=True,
        secure=True,
        samesite="None",
        max_age=60 * 15
    )
    
    response.set_cookie(
        key="rt",
        value=str(refresh),
        httponly=True,
        secure=True,
        samesite="None",
        max_age=60 * 60 * 24 * 7
    )

    response.set_cookie(
        key="loggedin",
        value=bool(True),
        httponly=True,
        secure=True,
        samesite="None",
        max_age=60 * 60 * 24  
    )
    
    return response