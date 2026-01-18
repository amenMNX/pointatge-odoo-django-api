from django.urls import path
from .views import pointage_view  # ✅ Import the correct function

urlpatterns = [
    path('api/pointage/', pointage_view),  # ✅ Use the correct function name
]