from rest_framework.permissions import BasePermission

class IsFromAllowedOrigin(BasePermission):
    def has_permission(self, request, view):
        allowed_origins = [ 
            "http://localhost:5173", 
            "http://localhost:5174"
        ]

        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")

        if not origin and not referer:
            return False

        if origin:
            return any(allowed in origin for allowed in allowed_origins)

        if referer:
            return any(allowed in referer for allowed in allowed_origins)

        return False
