import aiosqlite
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import Counter
from core.hybrid.action_logger import action_logger
from core.security.crypto import decrypt

@dataclass
class SessionSummary:
    session_id: str
    duration_seconds: float
    total_steps: int
    steps_completed: int
    errors_detected: int
    errors_resolved: int
    total_guidance_delivered: int
    avg_confidence: float
    most_common_error_type: str
    task_type: str
    generated_at: str

class SessionSummarizer:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or action_logger.db_path

    async def summarize(self, session_id: str) -> SessionSummary:
        total_steps = 0
        steps_completed = 0
        total_guidance_delivered = 0
        sum_confidence = 0.0
        start_time = None
        end_time = None
        task_type = "unknown"

        # Action Log Aggregation
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT timestamp, type, domain, was_guided, guidance_confidence FROM action_log WHERE session_id = ? ORDER BY timestamp",
                (session_id,)
            ) as cursor:
                async for row in cursor:
                    ts_str = row[0]
                    if ts_str.endswith('Z'):
                        ts_str = ts_str[:-1] + '+00:00'
                    ts = datetime.fromisoformat(ts_str)
                    if start_time is None:
                        start_time = ts
                    end_time = ts
                    
                    total_steps += 1
                    steps_completed += 1
                    
                    was_guided = bool(row[3])
                    confidence = row[4]
                    if was_guided:
                        total_guidance_delivered += 1
                        if confidence is not None:
                            sum_confidence += float(confidence)

            # Error History Aggregation
            errors_detected = 0
            errors_resolved = 0  # We don't have a resolved field in error_history per issue description, defaulting to 0
            most_common_error_type = "none"
            
            # Check if error_history exists
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='error_history'") as cursor:
                if await cursor.fetchone():
                    async with db.execute("SELECT error FROM error_history WHERE session_id = ?", (session_id,)) as cursor:
                        errors = []
                        async for row in cursor:
                            errors_detected += 1
                            encrypted_error = row[0]
                            if encrypted_error:
                                try:
                                    decrypted = decrypt(encrypted_error)
                                    errors.append(decrypted)
                                except Exception:
                                    errors.append("unknown_error")
                        
                        if errors:
                            error_types = [err.split(':')[0] if ':' in err else err for err in errors]
                            most_common_error_type = Counter(error_types).most_common(1)[0][0]

        duration_seconds = 0.0
        if start_time and end_time:
            duration_seconds = (end_time - start_time).total_seconds()
            
        avg_confidence = 0.0
        if total_guidance_delivered > 0:
            avg_confidence = sum_confidence / total_guidance_delivered

        return SessionSummary(
            session_id=session_id,
            duration_seconds=round(duration_seconds, 2),
            total_steps=total_steps,
            steps_completed=steps_completed,
            errors_detected=errors_detected,
            errors_resolved=errors_resolved,
            total_guidance_delivered=total_guidance_delivered,
            avg_confidence=round(avg_confidence, 2),
            most_common_error_type=most_common_error_type,
            task_type=task_type,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
