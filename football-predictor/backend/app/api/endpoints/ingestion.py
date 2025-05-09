from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from typing import Dict, Any, Optional
import subprocess
import os
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.models.models import IngestionAudit

router = APIRouter()

@router.post("/run")
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    force: bool = False,
    league: Optional[str] = None
) -> Dict[str, Any]:
    """
    Trigger football data ingestion in the background.
    
    Parameters:
    - force: Force reprocessing of all files
    - league: Optionally specify a specific league to process
    """
    
    def run_ingestion(force: bool, league: Optional[str] = None):
        try:
            script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "run_full_ingestion.sh"
            
            # Make sure the script is executable
            os.chmod(script_path, 0o755)
            
            cmd = [str(script_path)]
            if force:
                cmd.append("--force")
            if league:
                cmd.append("--league")
                cmd.append(league)
                
            logging.info(f"Running ingestion with command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"Ingestion failed: {result.stderr}")
            else:
                logging.info("Ingestion completed successfully")
        
        except Exception as e:
            logging.error(f"Error running ingestion: {e}")
    
    # Run in background to not block the API response
    background_tasks.add_task(run_ingestion, force, league)
    
    return {
        "status": "started",
        "message": "Data ingestion started in the background"
    }

@router.get("/status")
async def get_ingestion_status(db = Depends(get_db)) -> Dict[str, Any]:
    """
    Get the status of recent ingestion operations
    """
    # Get the 10 most recent ingestion audit records
    recent_audits = db.query(IngestionAudit).order_by(
        IngestionAudit.ingested_at.desc()
    ).limit(10).all()
    
    # Calculate summary stats
    total_records_added = sum(audit.records_added for audit in recent_audits)
    total_records_updated = sum(audit.records_updated for audit in recent_audits)
    
    # Group by repo
    repo_stats = {}
    for audit in recent_audits:
        if audit.repo not in repo_stats:
            repo_stats[audit.repo] = {
                "added": 0,
                "updated": 0
            }
        repo_stats[audit.repo]["added"] += audit.records_added
        repo_stats[audit.repo]["updated"] += audit.records_updated
    
    return {
        "most_recent": recent_audits[0].ingested_at if recent_audits else None,
        "total_records_added": total_records_added,
        "total_records_updated": total_records_updated,
        "repo_stats": repo_stats,
        "recent_ingestions": [
            {
                "repo": audit.repo,
                "file_path": audit.file_path,
                "ingested_at": audit.ingested_at,
                "records_added": audit.records_added,
                "records_updated": audit.records_updated
            } for audit in recent_audits
        ]
    } 