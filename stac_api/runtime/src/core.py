"""CoreCrudClient extensions for the VEDA STAC API."""
from datetime import datetime
from typing import Any, List, Optional, Union

import orjson
from asyncpg.exceptions import InvalidDatetimeFormatError
from buildpg import render
from pydantic import ValidationError
from pygeofilter.backends.cql2_json import to_cql2
from pygeofilter.parsers.cql2_text import parse as parse_cql2_text

from fastapi import HTTPException
from stac_fastapi.pgstac.core import CoreCrudClient
from stac_fastapi.types.errors import InvalidQueryParameter
from starlette.requests import Request

from .search import CollectionSearchPost

NumType = Union[float, int]


class VedaCrudClient(CoreCrudClient):
    """Veda STAC API Client."""

    async def _collection_id_search_base(
        self,
        search_request: CollectionSearchPost,
        **kwargs: Any,
    ) -> List[str]:
        """Cross catalog search (POST).
        Called with `POST /search`.
        Args:
            search_request: search request parameters.
        Returns:
            ItemCollection containing items which match the search criteria.
        """
        request: Request = kwargs["request"]
        pool = request.app.state.readpool

        search_request.conf = search_request.conf or {}
        req = search_request.json(exclude_none=True, by_alias=True)

        try:
            async with pool.acquire() as conn:
                q, p = render(
                    """
                    SELECT * FROM collection_id_search(:req::text::jsonb);
                    """,
                    req=req,
                )
                collections = await conn.fetch(q, *p)
        except InvalidDatetimeFormatError:
            raise InvalidQueryParameter(
                f"Datetime parameter {search_request.datetime} is invalid."
            )

        return [collection["collection_id_search"] for collection in collections]

    async def collection_id_post_search(
        self, search_request: CollectionSearchPost, **kwargs
    ) -> List[str]:
        """Cross catalog search (POST).
        Called with `POST /collection-id-search`.
        Args:
            search_request: search request parameters.
        Returns:
            A list of collection IDs which match the search criteria.
        """
        collection_ids = await self._collection_id_search_base(search_request, **kwargs)
        return collection_ids

    async def collection_id_get_search(
        self,
        bbox: Optional[List[NumType]] = None,
        datetime: Optional[Union[str, datetime]] = None,
        filter: Optional[str] = None,
        **kwargs,
    ) -> List[str]:
        """Cross catalog search (GET).
        Called with `GET /collection-id-search`.
        Returns:
            A list of collection IDs which match the search criteria.
        """
        # Parse request parameters
        base_args = {"bbox": bbox}

        if filter:
            ast = parse_cql2_text(filter)
            base_args["filter"] = orjson.loads(to_cql2(ast))
            base_args["filter-lang"] = "cql2-json"  # type: ignore

        if datetime:
            base_args["datetime"] = datetime  # type: ignore

        # Remove None values from dict
        clean = {}
        for k, v in base_args.items():
            if v is not None and v != []:
                clean[k] = v

        # Do the request
        try:
            search_request = CollectionSearchPost(**clean)
        except ValidationError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid parameters provided {e}"
            )
        return await self.collection_id_post_search(
            search_request, request=kwargs["request"]
        )
