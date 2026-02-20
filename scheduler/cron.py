"""
Cron Expression Parser

Parses and evaluates cron expressions for scheduling.
Supports standard cron syntax with extensions.
"""

from datetime import datetime, timedelta
from typing import Optional, Set


class CronExpression:
    """Represents a parsed cron expression"""

    def __init__(self, expression: str):
        self.expression = expression
        self.parts = expression.split()

        if len(self.parts) != 5:
            raise ValueError(
                f"Invalid cron expression: '{expression}'. " "Expected 5 fields: minute hour day month day_of_week"
            )

        self.minutes = self._parse_field(self.parts[0], 0, 59)
        self.hours = self._parse_field(self.parts[1], 0, 23)
        self.days_of_month = self._parse_field(self.parts[2], 1, 31)
        self.months = self._parse_field(self.parts[3], 1, 12)
        self.days_of_week = self._parse_field(self.parts[4], 0, 6)

    def _parse_field(self, field: str, min_val: int, max_val: int) -> Set[int]:
        """Parse a single cron field"""
        values = set()

        # Handle special characters
        if field == "*":
            return set(range(min_val, max_val + 1))

        if field == "?":
            return set(range(min_val, max_val + 1))

        # Split by comma for multiple values
        for part in field.split(","):
            values.update(self._parse_part(part, min_val, max_val))

        return values

    def _parse_part(self, part: str, min_val: int, max_val: int) -> Set[int]:
        """Parse a single part of a field"""
        # Handle step values (e.g., */5, 1-10/2)
        if "/" in part:
            range_part, step = part.split("/")
            step = int(step)

            if range_part == "*":
                start, end = min_val, max_val
            elif "-" in range_part:
                start, end = map(int, range_part.split("-"))
            else:
                start = int(range_part)
                end = max_val

            return set(range(start, end + 1, step))

        # Handle ranges (e.g., 1-5)
        if "-" in part:
            start, end = map(int, part.split("-"))
            return set(range(start, end + 1))

        # Single value
        return {int(part)}

    def matches(self, dt: datetime) -> bool:
        """Check if the datetime matches this cron expression"""
        return (
            dt.minute in self.minutes
            and dt.hour in self.hours
            and dt.day in self.days_of_month
            and dt.month in self.months
            and dt.weekday() in self.days_of_week
        )

    def next_occurrence(self, from_time: Optional[datetime] = None) -> datetime:
        """Get the next occurrence after the given time"""
        if from_time is None:
            from_time = datetime.utcnow()

        # Start from the next minute
        current = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Search for next match (max 4 years to avoid infinite loop)
        for _ in range(366 * 24 * 60 * 4):
            if self.matches(current):
                return current
            current += timedelta(minutes=1)

        raise RuntimeError("Could not find next occurrence")

    def previous_occurrence(self, from_time: Optional[datetime] = None) -> datetime:
        """Get the previous occurrence before the given time"""
        if from_time is None:
            from_time = datetime.utcnow()

        # Start from the previous minute
        current = from_time.replace(second=0, microsecond=0) - timedelta(minutes=1)

        # Search for previous match (max 4 years)
        for _ in range(366 * 24 * 60 * 4):
            if self.matches(current):
                return current
            current -= timedelta(minutes=1)

        raise RuntimeError("Could not find previous occurrence")


class CronParser:
    """
    Cron expression parser with preset support

    Presets:
    - @yearly / @annually: Once per year (0 0 1 1 *)
    - @monthly: Once per month (0 0 1 * *)
    - @weekly: Once per week (0 0 * * 0)
    - @daily / @midnight: Once per day (0 0 * * *)
    - @hourly: Once per hour (0 * * * *)
    - @minutely: Once per minute (* * * * *)
    """

    PRESETS = {
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *",
        "@monthly": "0 0 1 * *",
        "@weekly": "0 0 * * 0",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@hourly": "0 * * * *",
        "@minutely": "* * * * *",
    }

    @classmethod
    def parse(cls, expression: str) -> CronExpression:
        """
        Parse a cron expression or preset

        Args:
            expression: Cron expression or preset (@daily, @hourly, etc.)

        Returns:
            CronExpression object
        """
        # Check for preset
        if expression in cls.PRESETS:
            expression = cls.PRESETS[expression]

        return CronExpression(expression)

    @classmethod
    def is_valid(cls, expression: str) -> bool:
        """Check if expression is valid"""
        try:
            cls.parse(expression)
            return True
        except ValueError:
            return False

    @classmethod
    def get_next_run(cls, expression: str, from_time: Optional[datetime] = None) -> datetime:
        """Get next run time for a cron expression"""
        cron = cls.parse(expression)
        return cron.next_occurrence(from_time)

    @classmethod
    def describe(cls, expression: str) -> str:
        """Get human-readable description of cron expression"""
        try:
            cron = cls.parse(expression)
        except ValueError as e:
            return f"Invalid: {e}"

        # Simple descriptions for common patterns
        if expression == "0 0 * * *":
            return "Daily at midnight"
        elif expression == "0 2 * * *":
            return "Daily at 2:00 AM"
        elif expression == "0 * * * *":
            return "Every hour"
        elif expression == "*/5 * * * *":
            return "Every 5 minutes"
        elif expression == "0 0 * * 0":
            return "Weekly on Sunday at midnight"
        elif expression == "0 0 1 * *":
            return "Monthly on the 1st at midnight"

        # Build generic description
        parts = []

        # Minutes
        if len(cron.minutes) == 60:
            parts.append("every minute")
        elif len(cron.minutes) == 1:
            parts.append(f"at minute {list(cron.minutes)[0]}")
        else:
            parts.append(f"at minutes {sorted(cron.minutes)}")

        # Hours
        if len(cron.hours) == 24:
            parts.append("every hour")
        elif len(cron.hours) == 1:
            parts.append(f"at hour {list(cron.hours)[0]}")
        else:
            parts.append(f"at hours {sorted(cron.hours)}")

        # Days
        if len(cron.days_of_month) == 31:
            parts.append("every day")
        elif len(cron.days_of_month) == 1:
            parts.append(f"on day {list(cron.days_of_month)[0]}")

        return " ".join(parts)


# Common cron patterns
CRON_PATTERNS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "hourly": "0 * * * *",
    "every_2_hours": "0 */2 * * *",
    "daily": "0 0 * * *",
    "daily_morning": "0 9 * * *",
    "daily_evening": "0 18 * * *",
    "weekly": "0 0 * * 0",
    "weekly_monday": "0 0 * * 1",
    "monthly": "0 0 1 * *",
    "monthly_first_monday": "0 0 * * 1",
    "yearly": "0 0 1 1 *",
}
