from datetime import datetime, date, timedelta
from typing import Optional, Union, Tuple, List
import re


class DateUtils:
    @staticmethod
    def parse_date(date_str: str, fmt: str = '%Y-%m-%d') -> Optional[date]:
        """
        Parse a date string into a date object with flexible format handling

        Args:
            date_str: String representing a date
            fmt: Format string (default: YYYY-MM-DD)

        Returns:
            date object if parsing succeeds, None otherwise
        """
        try:
            # Try the specified format first
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            # Fallback to common date formats
            for fallback_fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%b %d, %Y', '%B %d, %Y'):
                try:
                    return datetime.strptime(date_str, fallback_fmt).date()
                except (ValueError, TypeError):
                    continue
            return None

    @staticmethod
    def parse_datetime(datetime_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
        """
        Parse a datetime string into a datetime object with flexible format handling

        Args:
            datetime_str: String representing a datetime
            fmt: Format string (default: YYYY-MM-DD HH:MM:SS)

        Returns:
            datetime object if parsing succeeds, None otherwise
        """
        try:
            # Try the specified format first
            return datetime.strptime(datetime_str, fmt)
        except (ValueError, TypeError):
            # Fallback to common datetime formats
            for fallback_fmt in (
                    '%Y-%m-%d %H:%M:%S',
                    '%m/%d/%Y %I:%M %p',
                    '%d-%m-%Y %H:%M',
                    '%b %d, %Y %I:%M%p',
                    '%B %d, %Y %H:%M:%S'
            ):
                try:
                    return datetime.strptime(datetime_str, fallback_fmt)
                except (ValueError, TypeError):
                    continue
            return None

    @staticmethod
    def parse_date_range(date_range_str: str, separator: str = ',') -> Optional[Tuple[date, date]]:
        """
        Parse a date range string into start and end dates

        Args:
            date_range_str: String in format "start_date,end_date"
            separator: Character separating dates (default: comma)

        Returns:
            Tuple of (start_date, end_date) or None if parsing fails
        """
        if not date_range_str:
            return None

        dates = date_range_str.split(separator)
        if len(dates) != 2:
            return None

        start_date = DateUtils.parse_date(dates[0].strip())
        end_date = DateUtils.parse_date(dates[1].strip())

        if start_date and end_date:
            return start_date, end_date
        return None

    @staticmethod
    def format_date(date_obj: Union[date, datetime], fmt: str = '%Y-%m-%d') -> str:
        """
        Format a date/datetime object as a string

        Args:
            date_obj: date or datetime object
            fmt: Format string (default: YYYY-MM-DD)

        Returns:
            Formatted date string or empty string if invalid
        """
        if not isinstance(date_obj, (date, datetime)):
            return ''
        return date_obj.strftime(fmt)

    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """
        Check if a string is a valid date

        Args:
            date_str: String to validate

        Returns:
            True if valid date, False otherwise
        """
        return DateUtils.parse_date(date_str) is not None

    @staticmethod
    def days_between(start: Union[date, datetime], end: Union[date, datetime]) -> int:
        """
        Calculate days between two dates/datetimes

        Args:
            start: Start date/datetime
            end: End date/datetime

        Returns:
            Number of days between dates
        """
        if not all(isinstance(d, (date, datetime)) for d in [start, end]):
            return 0
        return (end - start).days

    @staticmethod
    def add_days_to_date(date_obj: Union[date, datetime], days: int) -> date:
        """
        Add days to a date

        Args:
            date_obj: Starting date/datetime
            days: Number of days to add (can be negative)

        Returns:
            New date object
        """
        if not isinstance(date_obj, (date, datetime)):
            raise ValueError("Invalid date object")
        return (date_obj + timedelta(days=days)).date()

    @staticmethod
    def is_weekday(date_obj: Union[date, datetime]) -> bool:
        """
        Check if a date is a weekday (Monday-Friday)

        Args:
            date_obj: Date to check

        Returns:
            True if weekday, False otherwise
        """
        if not isinstance(date_obj, (date, datetime)):
            return False
        return date_obj.weekday() < 5  # 0-4 = Monday-Friday

    @staticmethod
    def parse_iso_date(iso_date_str: str) -> Optional[datetime]:
        """
        Parse ISO 8601 formatted date string

        Args:
            iso_date_str: String in ISO 8601 format

        Returns:
            datetime object or None if invalid
        """
        try:
            return datetime.fromisoformat(iso_date_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_current_date() -> date:
        """Get current date in local timezone"""
        return datetime.now().date()

    @staticmethod
    def get_current_datetime() -> datetime:
        """Get current datetime in local timezone"""
        return datetime.now()

    @staticmethod
    def parse_natural_language_date(date_str: str) -> Optional[date]:
        """
        Parse natural language date strings (e.g., "tomorrow", "next week")

        Args:
            date_str: Natural language date string

        Returns:
            date object or None if invalid
        """
        date_str = date_str.lower().strip()
        today = DateUtils.get_current_date()

        natural_dates = {
            'today': today,
            'yesterday': today - timedelta(days=1),
            'tomorrow': today + timedelta(days=1),
            'next week': today + timedelta(weeks=1),
            'next month': DateUtils.add_months(today, 1),
            'next year': today.replace(year=today.year + 1)
        }

        return natural_dates.get(date_str)

    @staticmethod
    def add_months(source_date: date, months: int) -> date:
        """
        Add months to a date while handling month boundaries

        Args:
            source_date: Starting date
            months: Number of months to add

        Returns:
            New date object
        """
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day,
                  [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30,
                   31, 30, 31][month - 1])
        return date(year, month, day)

    @staticmethod
    def is_date_in_range(check_date: Union[date, datetime],
                        start_date: Union[date, datetime],
                        end_date: Union[date, datetime]) -> bool:
        """
        Check if a date falls within a specified range (inclusive)

        Args:
            check_date: Date to check
            start_date: Range start date
            end_date: Range end date

        Returns:
            True if check_date is in range, False otherwise
        """
        if not all(isinstance(d, (date, datetime)) for d in [check_date, start_date, end_date]):
            return False
        return start_date <= check_date <= end_date

    @staticmethod
    def extract_dates_from_text(text: str) -> List[date]:
        """
        Extract dates from a text string using pattern matching

        Args:
            text: String containing potential dates

        Returns:
            List of found date objects
        """
        # Common date patterns
        patterns = [
            r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
            r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{2}-\d{2}-\d{4}\b',  # DD-MM-YYYY
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month Day, Year
            r'\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b'  # Day Month Year
        ]

        found_dates = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                date_str = match.group()
                parsed_date = DateUtils.parse_date(date_str)
                if parsed_date:
                    found_dates.append(parsed_date)

        return found_dates