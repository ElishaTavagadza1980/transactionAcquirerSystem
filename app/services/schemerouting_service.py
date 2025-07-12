from fastapi import HTTPException
from app.data_access.schemerouting_supabase import (
    dataAddSchemeRouting,
    dataGetSchemeRouting,
    dataGetAllSchemeRoutings,
    dataUpdateSchemeRouting,
)
from app.models.schemerouting_model import SchemeRouting
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class SchemeRoutingService:
    def create_scheme_routing(self, scheme_routing: SchemeRouting) -> SchemeRouting:
        existing = dataGetSchemeRouting(scheme_routing.scheme)
        if existing:
            raise HTTPException(status_code=400, detail="Routing already exists")
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        scheme_routing.created_at = current_timestamp
        scheme_routing.updated_at = current_timestamp
        result = dataAddSchemeRouting(scheme_routing)
        return SchemeRouting(**result)

    def update_scheme_routing(self, scheme: str, routing: str) -> SchemeRouting:
        existing = dataGetSchemeRouting(scheme)
        if not existing:
            raise HTTPException(status_code=404, detail="Routing not found")
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated = SchemeRouting(
            scheme=scheme,
            routing=routing,
            created_at=existing.get("created_at"),
            updated_at=current_timestamp
        )
        result = dataUpdateSchemeRouting(scheme, updated)
        return SchemeRouting(**result)

    def get_scheme_routing(self, scheme: str) -> SchemeRouting:
        result = dataGetSchemeRouting(scheme)
        if not result:
            raise HTTPException(status_code=404, detail="Routing not found")
        return SchemeRouting(**result)

    def get_all_scheme_routings(self) -> list[SchemeRouting]:
        results = dataGetAllSchemeRoutings()
        return [SchemeRouting(**r) for r in results]
