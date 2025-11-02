"""Checkpoint cleanup service for managing LangGraph checkpoints.

This service provides functionality to clean up old checkpoints to prevent
database bloat while optionally archiving them to S3 for compliance.
"""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List, Dict, Any
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class CheckpointCleanupService:
    """Service for cleaning up old LangGraph checkpoints."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.retention_days = settings.CHECKPOINT_RETENTION_DAYS
        self.checkpoint_tables = settings.CHECKPOINT_TABLES
    
    async def cleanup_old_checkpoints(
        self,
        retention_days: Optional[int] = None,
        archive_to_s3: bool = False
    ) -> Dict[str, int]:
        """
        Clean up old checkpoints older than retention period.
        
        Args:
            retention_days: Number of days to retain checkpoints (default: from settings)
            archive_to_s3: Whether to archive to S3 before deletion (not implemented yet)
        
        Returns:
            Dict with deletion counts per table
        """
        retention_days = retention_days or self.retention_days
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        logger.info(
            "checkpoint_cleanup_started",
            retention_days=retention_days,
            cutoff_date=cutoff_date.isoformat(),
            archive_enabled=archive_to_s3
        )
        
        deletion_counts = {}
        
        try:
            # Optional: Archive to S3 before deletion
            if archive_to_s3:
                archived_count = await self._archive_to_s3(cutoff_date)
                logger.info(
                    "checkpoints_archived",
                    count=archived_count,
                    cutoff_date=cutoff_date.isoformat()
                )
            
            # Delete from checkpoint tables
            for table in self.checkpoint_tables:
                try:
                    # Checkpoints table has 'ts' timestamp field
                    if table == "checkpoints":
                        result = await self.session.execute(
                            text(f"""
                                DELETE FROM {table}
                                WHERE (checkpoint->>'ts')::timestamp < :cutoff
                            """),
                            {"cutoff": cutoff_date}
                        )
                    else:
                        # Related tables: delete by thread_id from deleted checkpoints
                        # This is handled by CASCADE in most cases, but explicit for clarity
                        result = await self.session.execute(
                            text(f"""
                                DELETE FROM {table}
                                WHERE thread_id NOT IN (
                                    SELECT DISTINCT thread_id FROM checkpoints
                                )
                            """)
                        )
                    
                    deleted_count = result.rowcount
                    deletion_counts[table] = deleted_count
                    
                    logger.info(
                        "checkpoint_table_cleaned",
                        table=table,
                        deleted_count=deleted_count
                    )
                    
                except Exception as e:
                    logger.error(
                        "checkpoint_table_cleanup_failed",
                        table=table,
                        error=str(e)
                    )
                    deletion_counts[table] = 0
            
            await self.session.commit()
            
            total_deleted = sum(deletion_counts.values())
            logger.info(
                "checkpoint_cleanup_completed",
                total_deleted=total_deleted,
                breakdown=deletion_counts
            )
            
            return deletion_counts
            
        except Exception as e:
            await self.session.rollback()
            logger.error(
                "checkpoint_cleanup_failed",
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _archive_to_s3(self, cutoff_date: datetime) -> int:
        """
        Archive old checkpoints to S3 before deletion.
        
        Future feature: Implement S3 archiving for compliance/audit requirements.
        
        Args:
            cutoff_date: Cutoff date for archiving
        
        Returns:
            Number of archived checkpoints (currently 0)
        """
        logger.warning("s3_archiving_not_implemented")
        return 0
    
    async def get_checkpoint_stats(self) -> Dict[str, Any]:
        """
        Get statistics about checkpoints in the database.
        
        Returns:
            Dict with checkpoint statistics
        """
        stats = {}
        
        try:
            # Total checkpoints
            result = await self.session.execute(
                text("SELECT COUNT(*) FROM checkpoints")
            )
            stats["total_checkpoints"] = result.scalar()
            
            # Checkpoints by age
            result = await self.session.execute(
                text("""
                    SELECT 
                        COUNT(*) FILTER (WHERE (checkpoint->>'ts')::timestamp > NOW() - INTERVAL '7 days') as last_7_days,
                        COUNT(*) FILTER (WHERE (checkpoint->>'ts')::timestamp > NOW() - INTERVAL '30 days') as last_30_days,
                        COUNT(*) FILTER (WHERE (checkpoint->>'ts')::timestamp <= NOW() - INTERVAL '30 days') as older_than_30_days
                    FROM checkpoints
                """)
            )
            age_stats = result.fetchone()
            stats["by_age"] = {
                "last_7_days": age_stats[0],
                "last_30_days": age_stats[1],
                "older_than_30_days": age_stats[2]
            }
            
            # Unique threads
            result = await self.session.execute(
                text("SELECT COUNT(DISTINCT thread_id) FROM checkpoints")
            )
            stats["unique_threads"] = result.scalar()
            
            # Checkpoint writes count
            result = await self.session.execute(
                text("SELECT COUNT(*) FROM checkpoint_writes")
            )
            stats["total_checkpoint_writes"] = result.scalar()
            
            # Checkpoint blobs count
            result = await self.session.execute(
                text("SELECT COUNT(*) FROM checkpoint_blobs")
            )
            stats["total_checkpoint_blobs"] = result.scalar()
            
            logger.info("checkpoint_stats_retrieved", stats=stats)
            return stats
            
        except Exception as e:
            logger.error(
                "get_checkpoint_stats_failed",
                error=str(e)
            )
            return {"error": str(e)}


async def cleanup_old_checkpoints_cron():
    """
    Cron job function to cleanup old checkpoints.
    
    This should be called by a scheduler (e.g., APScheduler, Celery, cron).
    
    Example with APScheduler:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            cleanup_old_checkpoints_cron,
            'cron',
            hour=2,  # Run at 2 AM
            minute=0
        )
        scheduler.start()
    """
    from ..database.session import async_session
    
    async with async_session() as session:
        service = CheckpointCleanupService(session)
        try:
            results = await service.cleanup_old_checkpoints()
            logger.info(
                "cron_checkpoint_cleanup_success",
                results=results
            )
        except Exception as e:
            logger.error(
                "cron_checkpoint_cleanup_failed",
                error=str(e),
                exc_info=True
            )
