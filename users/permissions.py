from django.http import JsonResponse

ALLOWED_ORIGINS = [
    "https://bijoux-chic.vercel.app",
    "https://admin-bijoux-chic.vercel.app",
    "http://localhost:5173",
]

class IsFromAllowedOrigin:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.META.get("HTTP_ORIGIN")
        referer = request.META.get("HTTP_REFERER")
        
        if not origin and not referer:
            return JsonResponse({"detail": "Access denied"}, status=403)

        if not self._is_allowed(origin, referer):
            return JsonResponse({"detail": "Access denied"}, status=403)

        return self.get_response(request)

    def _is_allowed(self, origin, referer):
        for allowed in ALLOWED_ORIGINS:
            if (origin and origin.startswith(allowed)) or (referer and referer.startswith(allowed)):
                return True
        return False
