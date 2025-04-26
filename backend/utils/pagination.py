from math import ceil
from typing import Dict, Any, Tuple, List, Optional, TypeVar

from flask import request
from sqlalchemy.orm import Query

T = TypeVar('T')  # Generic type for query results


class Paginator:
    """
    Pagination utility for database queries and API responses
    """

    @staticmethod
    def get_pagination_params(
            default_per_page: int = 20,
            max_per_page: int = 100
    ) -> Tuple[int, int]:
        """
        Get pagination parameters from request
        """
        try:
            page = max(1, int(request.args.get('page', 1)))
        except ValueError:
            page = 1

        try:
            per_page = min(
                max(1, int(request.args.get('per_page', default_per_page))),
                max_per_page
            )
        except ValueError:
            per_page = default_per_page

        return page, per_page

    @staticmethod
    def format_pagination_response(
            items: List[Any],
            pagination_meta: Dict[str, Any],
            schema: Any = None
    ) -> Dict[str, Any]:
        """
        Format a paginated API response
        """
        return {
            'data': schema.dump(items) if schema else items,
            'pagination': pagination_meta
        }


def paginate_query(
        query: Query[T],
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100
) -> Tuple[List[T], Dict[str, Any]]:
    """
    Paginate a SQLAlchemy query
    """
    # Validate and clamp per_page
    per_page = min(per_page, max_per_page) if max_per_page else per_page
    per_page = max(1, per_page)

    # Clamp page number
    page = max(1, page)

    # Execute paginated query
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    total = query.order_by(None).count()  # Fast count without existing ordering

    # Calculate page metadata
    total_pages = ceil(total / per_page) if per_page else 1

    return items, {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }


class CursorPaginator:
    """
    Cursor-based pagination for APIs
    """

    @staticmethod
    def paginate(
            query: Query[T],
            cursor: Optional[Any] = None,
            limit: int = 20,
            cursor_field: str = 'id',
            ascending: bool = True
    ) -> Tuple[List[T], Optional[Any]]:
        """
        Cursor-based pagination
        """
        model_class = query.column_descriptions[0]['type']
        cursor_column = getattr(model_class, cursor_field)

        if cursor is not None:
            if ascending:
                query = query.filter(cursor_column > cursor)
            else:
                query = query.filter(cursor_column < cursor)

        query = query.order_by(
            cursor_column.asc() if ascending else cursor_column.desc()
        )

        items = query.limit(limit + 1).all()  # Get one extra to check for next page

        if len(items) > limit:
            next_cursor = getattr(items[-2], cursor_field)  # Get cursor from last returned item
            items = items[:-1]  # Remove extra item
        else:
            next_cursor = None

        return items, next_cursor