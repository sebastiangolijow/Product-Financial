from rest_framework.pagination import PageNumberPagination

from api.paginations.pagination_generics import NumberInsteadOfLinkPagination


class CashflowPagination(NumberInsteadOfLinkPagination):
    page_size = 2
    max_page_size = 100
