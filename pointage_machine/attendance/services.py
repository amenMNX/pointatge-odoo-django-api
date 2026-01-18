from django.utils.timezone import now, make_aware
from datetime import datetime, timedelta, time
from .models import Employee, Pointage, Leave

# Enterprise constants
OPENING_TIME = time(8, 30)
CLOSING_TIME = time(18, 0)
LUNCH_START = time(12, 0)
LUNCH_END = time(15, 0)
MAX_SESSION_HOURS = 8


def process_pointage(pin):
    current_time = now()

    try:
        employee = Employee.objects.get(pin=pin)
    except Employee.DoesNotExist:
        return {"error": "employee not found"}, 404

    def create_pointage(state, check_time=None, anomaly=False, note=""):
        if not check_time:
            check_time = current_time
        p = Pointage.objects.create(
            employee=employee,
            state=state,
            check_time=check_time,
            anomaly=anomaly,
            note=note
        )
        return {
            "action": state,
            "anomaly": anomaly,
            "time": p.check_time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": note
        }

    def adjust_to_working_hours(dt):
        if dt.time() < OPENING_TIME:
            return dt.replace(hour=OPENING_TIME.hour, minute=OPENING_TIME.minute)
        if dt.time() > CLOSING_TIME:
            return dt.replace(hour=CLOSING_TIME.hour, minute=CLOSING_TIME.minute)
        return dt

    # --- Leave check ---
    if Leave.objects.filter(
        employee=employee,
        date_from__lte=current_time.date(),
        date_to__gte=current_time.date()
    ).exists():
        return {
            "action": "NONE",
            "anomaly": False,
            "time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "note": "Today is approved leave"
        }, 200

    # --- Get last pointage ---
    last = Pointage.objects.filter(employee=employee).order_by('-check_time').first()
    days_skipped = 0  # ⭐ Initialize here to avoid NameError

    # --- Auto close previous days ---
    if last and last.state == 'IN':
        days_skipped = (current_time.date() - last.check_time.date()).days
        
        if days_skipped > 0:
            # auto close previous day (FIXED INDENTATION)
            out_time = make_aware(datetime.combine(last.check_time.date(), CLOSING_TIME))
            create_pointage('OUT', out_time, True, 'Auto close previous day IN')
            
            # Update last after auto-close (CRITICAL FIX)
            last = Pointage.objects.filter(employee=employee).order_by('-check_time').first()

            for d in range(1, days_skipped):
                skipped_day = last.check_time.date() + timedelta(days=d)
                if not Leave.objects.filter(
                    employee=employee,
                    date_from__lte=skipped_day,
                    date_to__gte=skipped_day
                ).exists():
                    # Create both IN and OUT for skipped working days
                    skipped_in = make_aware(datetime.combine(skipped_day, OPENING_TIME))
                    skipped_out = make_aware(datetime.combine(skipped_day, CLOSING_TIME))
                    create_pointage('IN', skipped_in, True, 'Skipped day auto IN')
                    create_pointage('OUT', skipped_out, True, 'Skipped day auto OUT')

    # --- Normal flow ---
    if not last or last.state == 'OUT':
        adjusted = adjust_to_working_hours(current_time)
        if LUNCH_START <= adjusted.time() < LUNCH_END:
            adjusted = adjusted.replace(hour=LUNCH_END.hour, minute=LUNCH_END.minute)
            return create_pointage('IN', adjusted, True, 'IN after lunch break'), 200
        return create_pointage('IN', adjusted), 200

    # --- Last state IN ---
    if LUNCH_START <= current_time.time() < LUNCH_END:
        lunch_out = make_aware(datetime.combine(current_time.date(), LUNCH_START))
        # FIXED: Only create OUT, not OUT+IN
        return create_pointage('OUT', lunch_out, True, 'Lunch break start'), 200

    if current_time - last.check_time > timedelta(hours=MAX_SESSION_HOURS):
        # FIXED: Only auto-close, don't auto-reopen
        return create_pointage('OUT', anomaly=True, note='Auto close timeout'), 200

    if current_time.time() > CLOSING_TIME and last.state == 'IN':
        # FIXED: Guard against duplicate OUT
        closing = make_aware(datetime.combine(current_time.date(), CLOSING_TIME))
        return create_pointage('OUT', closing, True, 'After closing time'), 200

    return create_pointage('OUT'), 200