"""
Recurring Schedule Helpers

Convenience functions for common recurring schedules.
"""

from datetime import datetime, timedelta


class RecurringSchedule:
    """
    Helper class for creating common recurring schedules

    Provides easy-to-use methods for common patterns without
    needing to write cron expressions.
    """

    @staticmethod
    def every_minute() -> str:
        """Every minute"""
        return "* * * * *"

    @staticmethod
    def every_n_minutes(n: int) -> str:
        """Every N minutes"""
        return f"*/{n} * * * *"

    @staticmethod
    def every_hour() -> str:
        """Every hour at minute 0"""
        return "0 * * * *"

    @staticmethod
    def every_n_hours(n: int) -> str:
        """Every N hours"""
        return f"0 */{n} * * *"

    @staticmethod
    def daily(hour: int = 0, minute: int = 0) -> str:
        """
        Daily at specific time

        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        return f"{minute} {hour} * * *"

    @staticmethod
    def twice_daily(hours: tuple = (9, 21)) -> str:
        """
        Twice daily at specified hours

        Args:
            hours: Tuple of two hours (default: 9 AM and 9 PM)
        """
        return f"0 {hours[0]},{hours[1]} * * *"

    @staticmethod
    def weekly(day: int = 0, hour: int = 0, minute: int = 0) -> str:
        """
        Weekly on specific day

        Args:
            day: Day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        return f"{minute} {hour} * * {day}"

    @staticmethod
    def weekly_monday(hour: int = 0, minute: int = 0) -> str:
        """Weekly on Monday"""
        return RecurringSchedule.weekly(1, hour, minute)

    @staticmethod
    def weekly_friday(hour: int = 0, minute: int = 0) -> str:
        """Weekly on Friday"""
        return RecurringSchedule.weekly(5, hour, minute)

    @staticmethod
    def monthly(day: int = 1, hour: int = 0, minute: int = 0) -> str:
        """
        Monthly on specific day

        Args:
            day: Day of month (1-31)
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        return f"{minute} {hour} {day} * *"

    @staticmethod
    def monthly_first_monday(hour: int = 0, minute: int = 0) -> str:
        """
        Monthly on the first Monday
        Uses a workaround since pure cron can't express this
        """
        # This runs every Monday, but you'd need additional logic
        # to only execute on the first Monday of the month
        return f"{minute} {hour} * * 1"

    @staticmethod
    def weekdays(hour: int = 0, minute: int = 0) -> str:
        """
        Every weekday (Monday-Friday)

        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        return f"{minute} {hour} * * 1-5"

    @staticmethod
    def weekends(hour: int = 0, minute: int = 0) -> str:
        """
        Every weekend (Saturday-Sunday)

        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
        """
        return f"{minute} {hour} * * 0,6"

    @staticmethod
    def business_hours() -> str:
        """
        Every hour during business hours (9 AM - 5 PM, weekdays)
        """
        return "0 9-17 * * 1-5"

    @staticmethod
    def startup_delay(minutes: int = 5) -> datetime:
        """
        Get datetime for job to run after system startup

        Args:
            minutes: Minutes after startup

        Returns:
            Datetime for one-time execution
        """
        return datetime.utcnow() + timedelta(minutes=minutes)

    @staticmethod
    def next_weekday(hour: int = 0, minute: int = 0) -> datetime:
        """
        Get datetime for the next weekday

        Args:
            hour: Hour to run
            minute: Minute to run

        Returns:
            Datetime for next weekday
        """
        now = datetime.utcnow()
        days_ahead = 1

        # If today is Friday (4), next weekday is Monday (add 3 days)
        # If today is Saturday (5), next weekday is Monday (add 2 days)
        # If today is Sunday (6), next weekday is Monday (add 1 day)
        if now.weekday() == 4:  # Friday
            days_ahead = 3
        elif now.weekday() == 5:  # Saturday
            days_ahead = 2
        elif now.weekday() == 6:  # Sunday
            days_ahead = 1

        next_day = now + timedelta(days=days_ahead)
        return next_day.replace(hour=hour, minute=minute, second=0, microsecond=0)

    @staticmethod
    def end_of_month(hour: int = 23, minute: int = 0) -> str:
        """
        Last day of every month
        Note: Cron doesn't handle variable month lengths well
        This runs on the 28th, 29th, 30th, and 31st
        """
        return f"{minute} {hour} 28-31 * *"

    @staticmethod
    def quarter_end(hour: int = 0, minute: int = 0) -> str:
        """
        Last day of every quarter (March, June, September, December)
        """
        return f"{minute} {hour} 31 3,6,9,12 *"

    @staticmethod
    def year_end(hour: int = 0, minute: int = 0) -> str:
        """Last day of the year"""
        return f"{minute} {hour} 31 12 *"


def calculate_next_occurrence(base_time: datetime, interval_minutes: int) -> datetime:
    """
    Calculate next occurrence based on interval

    Args:
        base_time: Starting time
        interval_minutes: Interval in minutes

    Returns:
        Next occurrence datetime
    """
    now = datetime.utcnow()

    # Calculate how many intervals have passed
    elapsed = (now - base_time).total_seconds() / 60
    intervals_passed = int(elapsed / interval_minutes)

    # Calculate next occurrence
    next_occurrence = base_time + timedelta(minutes=(intervals_passed + 1) * interval_minutes)

    return next_occurrence


class SchedulePresets:
    """
    Common schedule presets for penetration testing workflows
    """

    @staticmethod
    def daily_vulnerability_scan(hour: int = 2) -> str:
        """
        Daily vulnerability scan (recommended: during off-hours)

        Args:
            hour: Hour to run (default: 2 AM)
        """
        return RecurringSchedule.daily(hour, 0)

    @staticmethod
    def weekly_deep_scan(day: int = 0, hour: int = 3) -> str:
        """
        Weekly comprehensive scan

        Args:
            day: Day of week (0=Sunday, default)
            hour: Hour to run (default: 3 AM)
        """
        return RecurringSchedule.weekly(day, hour, 0)

    @staticmethod
    def subdomain_monitoring() -> str:
        """
        Frequent subdomain monitoring (every 4 hours)
        """
        return RecurringSchedule.every_n_hours(4)

    @staticmethod
    def certificate_expiry_check() -> str:
        """
        Daily SSL certificate expiry check
        """
        return RecurringSchedule.daily(6, 0)

    @staticmethod
    def threat_intelligence_update() -> str:
        """
        Threat intelligence feed update (every 6 hours)
        """
        return RecurringSchedule.every_n_hours(6)

    @staticmethod
    def weekly_report() -> str:
        """
        Weekly executive report (Monday 9 AM)
        """
        return RecurringSchedule.weekly_monday(9, 0)

    @staticmethod
    def monthly_compliance_audit() -> str:
        """
        Monthly compliance audit (1st of month)
        """
        return RecurringSchedule.monthly(1, 2, 0)
