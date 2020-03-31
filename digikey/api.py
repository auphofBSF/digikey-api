"""
Top-level API, provides access to the Digikey API
without directly instantiating a client object.
Also wraps the response JSON in types that provide easier access
to various fields.
"""
from digikey import models
from digikey.client import DigikeyClient
import typing as t


def search(query: str,
           start: int = 0,
           limit: int = 10,
           search_options: t.Union[t.List[str], None] = None,
           search_filters: models.Filters = None,
           search_sort: models.Sort = None,
           ) -> models.KeywordSearchResult:
    """
    Search Digikey for a general keyword (and optional filters).
    Args:
        query (str): Free-form keyword query
        start: Ordinal position of first result
        limit: Maximum number of results to return
        search_options: Search Options
        search_filters: Filters to use in the search
        search_sort: Sort Settings for the search
    Returns:
        list of `models.KeywordSearchResult` objects.
    """

    client = DigikeyClient()
    response = client.search(
        query,
        start=start,
        limit=limit,
        search_options=search_options,
        search_filters=search_filters,
        search_sort=search_sort,
    )
    return models.KeywordSearchResult(response)


def part(partnr: str,
         include_associated: bool = False,
         include_for_use_with: bool = False,
         ) -> models.Part:
    """
    Query part by unique ID
    Args:
        partnr (str): Part number. Works best with Digi-Key part numbers.
        include_associated (bool): The option to include all Associated products
        include_for_use_with (bool): The option to include all For Use With product
    Kwargs:
    Returns:
        dict. See `models.Part` for exact fields.
    """
    client = DigikeyClient()
    response = client.part(
        partnr,
        include_associated=include_associated,
        include_for_use_with=include_for_use_with,
    )
    return models.Part(response)
