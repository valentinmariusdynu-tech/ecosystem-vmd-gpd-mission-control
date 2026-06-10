"""
Sync Engine v2.4 — cu conflict detection real și resolution.
"""

from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.models.event_log import EventLogDB
from src.models.conflict import ConflictDB, ConflictCreate
from src.models.audit_log import AuditLogDB


class SyncEngine:

    @classmethod
    def detect_conflict(cls, db: Session, event: Dict[str, Any], device_id: str) -> Optional[Dict[str, Any]]:
        """Detect conflict between local and server state."""
        entity_id = event.get("payload", {}).get("match_id") or event.get("payload", {}).get("incident_id")
        entity_type = event.get("event_type", "unknown")
        base_revision = event.get("base_revision")

        if not entity_id:
            return None

        # Check if server has newer version
        server_event = db.query(EventLogDB).filter(
            EventLogDB.source_device_id != device_id,
            EventLogDB.payload.contains({"match_id": entity_id} if "match" in entity_type else {"incident_id": entity_id})
        ).order_by(EventLogDB.entity_version.desc()).first()

        if not server_event:
            return None

        # If client base revision doesn't match server revision = conflict
        if base_revision and base_revision != server_event.server_revision:
            return {
                "conflict_type": "stale_data",
                "server_version": server_event.entity_version,
                "server_revision": server_event.server_revision,
                "server_timestamp": server_event.event_timestamp,
            }

        # If concurrent edit (same entity, different device, overlapping time)
        concurrent = db.query(EventLogDB).filter(
            EventLogDB.source_device_id != device_id,
            EventLogDB.event_timestamp >= event.get("event_timestamp", datetime.utcnow()),
            EventLogDB.payload.contains({"match_id": entity_id} if "match" in entity_type else {"incident_id": entity_id})
        ).first()

        if concurrent:
            return {
                "conflict_type": "concurrent_edit",
                "server_version": concurrent.entity_version,
                "server_timestamp": concurrent.event_timestamp,
            }

        return None

    @classmethod
    def resolve_conflict(cls, db: Session, event: Dict[str, Any], conflict_info: Dict[str, Any], policy: str = "timestamp_wins") -> Dict[str, Any]:
        """Resolve conflict according to policy."""
        local_ts = datetime.fromisoformat(event.get("event_timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00"))
        server_ts = conflict_info.get("server_timestamp", datetime.utcnow())

        if policy == "timestamp_wins":
            if local_ts >= server_ts:
                resolution = "local_wins"
            else:
                resolution = "server_wins"
        elif policy == "server_wins":
            resolution = "server_wins"
        elif policy == "manual":
            resolution = "pending_manual"
        else:
            resolution = "timestamp_wins"

        # Log conflict
        conflict = ConflictDB(
            conflict_id=f"conf_{datetime.utcnow().timestamp()}",
            entity_type=event.get("event_type", "unknown"),
            entity_id=event.get("payload", {}).get("match_id") or event.get("payload", {}).get("incident_id"),
            local_version=event.get("payload", {}),
            server_version={"version": conflict_info.get("server_version")},
            local_timestamp=local_ts,
            server_timestamp=server_ts,
            conflict_type=conflict_info.get("conflict_type", "unknown"),
            resolution=resolution,
            resolution_policy=policy,
        )
        db.add(conflict)
        db.commit()

        return {
            "resolution": resolution,
            "conflict_id": conflict.conflict_id,
            "policy": policy,
        }

    @classmethod
    def process_batch(cls, db: Session, batch: List[Dict[str, Any]], device_id: str) -> Dict[str, Any]:
        """Process sync batch with conflict detection."""
        processed = 0
        duplicates = 0
        conflicts = 0
        conflict_details = []

        for event in batch:
            # Check idempotency (strict: same key + same payload = duplicate, same key + diff payload = conflict)
            existing = db.query(EventLogDB).filter(
                EventLogDB.idempotency_key == event.get("idempotency_key")
            ).first()

            if existing:
                import hashlib
                new_hash = hashlib.sha256(str(event.get("payload", {})).encode()).hexdigest()
                if existing.payload_hash == new_hash:
                    duplicates += 1
                    continue
                else:
                    # Same key, different payload = conflict
                    conflicts += 1
                    conflict_info = {
                        "conflict_type": "idempotency_mismatch",
                        "server_version": existing.entity_version,
                        "server_timestamp": existing.event_timestamp,
                    }
                    resolution = cls.resolve_conflict(db, event, conflict_info, "server_wins")
                    conflict_details.append(resolution)
                    continue

            # Check for real conflicts
            conflict = cls.detect_conflict(db, event, device_id)
            if conflict:
                conflicts += 1
                resolution = cls.resolve_conflict(db, event, conflict)
                if resolution["resolution"] == "server_wins":
                    continue  # Skip local event
                # If local wins, continue processing

            # Process event
            import hashlib
            event_log = EventLogDB(
                event_id=event.get("event_id", f"evt_{datetime.utcnow().timestamp()}"),
                event_type=event.get("event_type", "unknown"),
                payload=event.get("payload", {}),
                payload_hash=hashlib.sha256(str(event.get("payload", {})).encode()).hexdigest(),
                schema_version=event.get("schema_version", "1.0"),
                entity_version=event.get("entity_version", 1),
                base_revision=event.get("base_revision"),
                source_device_id=device_id,
                source_service="sync_push",
                idempotency_key=event.get("idempotency_key", f"idemp_{datetime.utcnow().timestamp()}"),
                event_timestamp=datetime.fromisoformat(event.get("event_timestamp", datetime.utcnow().isoformat()).replace("Z", "+00:00")),
                partition_key=device_id[:4],
            )
            db.add(event_log)
            processed += 1

        db.commit()

        # Audit log
        db.add(AuditLogDB(
            action="sync_push",
            details={"device_id": device_id, "processed": processed, "duplicates": duplicates, "conflicts": conflicts},
        ))
        db.commit()

        return {
            "processed": processed,
            "duplicates": duplicates,
            "conflicts": conflicts,
            "conflict_details": conflict_details,
            "server_timestamp": datetime.utcnow().isoformat(),
        }
