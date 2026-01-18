from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import process_pointage

@api_view(["POST"])
def pointage_view(request):
    pin = request.data.get("pin")
    if not pin:
        return Response({"success": False, "error": "PIN_REQUIRED"}, status=400)

    result, status_code = process_pointage(pin)
    return Response(result, status=status_code)
