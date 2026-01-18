from django.utils import timezone
from django.db import transaction
from attendance.models import Pointage
import logging

logger = logging.getLogger(__name__)

def process_pointage(employee, source="WEB"):
    """
    Single source of truth for pointage decision.
    Creates a new pointage record with appropriate state (IN/OUT).
    
    Args:
        employee: Employee instance
        source: Source of the pointage (WEB, MOBILE, BIOMETRIC, etc.)
    
    Returns:
        Pointage: The created pointage instance
    
    Raises:
        ValueError: If employee is None
    """
    if not employee:
        raise ValueError("Employee cannot be None")
    
    now = timezone.now()
    
    try:
        # Get the last pointage with atomic transaction to ensure consistency
        with transaction.atomic():
            # Use select_for_update() to prevent race conditions in concurrent environments
            last = (
                Pointage.objects
                .select_for_update()
                .filter(employee=employee)
                .order_by("-check_time")
                .first()
            )
            
            # Determine the new state
            if not last or last.state == "OUT":
                state = "IN"
            else:
                state = "OUT"
            
            # Create the new pointage
            pointage = Pointage.objects.create(
                employee=employee,
                check_time=now,
                state=state,
                source=source,
                synced_to_odoo=False
            )
            
            logger.info(
                f"Pointage created for employee {employee.pin}: "
                f"state={state}, source={source}, time={now}"
            )
            
            return pointage
            
    except Exception as e:
        logger.error(
            f"Failed to process pointage for employee {employee.pin}: {str(e)}",
            exc_info=True
        )
        raise


def get_employee_current_state(employee):
    """
    Helper function to get employee's current attendance state.
    
    Args:
        employee: Employee instance
    
    Returns:
        str: "IN", "OUT", or "UNKNOWN" if no records exist
    """
    if not employee:
        return "UNKNOWN"
    
    last = (
        Pointage.objects
        .filter(employee=employee)
        .order_by("-check_time")
        .first()
    )
    
    if not last:
        return "UNKNOWN"
    
    return last.state