from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default for all list endpoints. Clients (the frontend sends page_size=5) may pick a
    smaller page; the cap keeps a single request from returning a large slice of content."""

    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50
