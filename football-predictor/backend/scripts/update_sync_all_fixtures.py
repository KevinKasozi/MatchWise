#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
import json
from datetime import datetime

# Configure logging
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fixture_sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from the app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_script(script_name, description):
    """Run a script and log the result"""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    
    if not os.path.exists(script_path):
        logger.error(f"Script {script_name} not found at {script_path}")
        return False
        
    logger.info(f"Running {description}: {script_name}")
    
    try:
        process = subprocess.run(
            ["python", script_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log the output
        for line in process.stdout.splitlines():
            logger.info(f"{script_name} output: {line}")
        
        for line in process.stderr.splitlines():
            if "ERROR" in line or "CRITICAL" in line:
                logger.error(f"{script_name} error: {line}")
            else:
                logger.info(f"{script_name} message: {line}")
        
        logger.info(f"Successfully completed {description}")
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {script_name}: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error output: {e.stderr}")
        return False

def check_assignment_issues():
    """Check if team assignment issues were found and need to be fixed"""
    issues_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "team_assignment_issues.json")
    
    if not os.path.exists(issues_file):
        logger.info("No team assignment issues file found")
        return False
    
    try:
        with open(issues_file, 'r') as f:
            issues = json.load(f)
        
        if not issues:
            logger.info("No team assignment issues found")
            return False
        
        logger.warning(f"Found {len(issues)} team assignment issues that need fixing")
        return True
    
    except Exception as e:
        logger.error(f"Error checking team assignment issues: {e}")
        return False

def main():
    """Main function to coordinate all fixture sync operations"""
    logger.info("="*80)
    logger.info("STARTING COMPLETE FIXTURE SYNCHRONIZATION PROCESS")
    logger.info("="*80)
    
    # Step 1: Synchronize fixtures from raw data
    if not run_script("sync_all_fixtures_from_raw_data.py", "fixture sync from raw data"):
        logger.error("Fixture sync failed, stopping process")
        return
    
    # Step 2: Verify team assignments
    if not run_script("verify_team_assignments.py", "team assignment verification"):
        logger.warning("Team assignment verification failed, continuing with caution")
    
    # Step 3: If issues were found, run the fix scripts
    if check_assignment_issues():
        logger.info("Running fix scripts for league assignments")
        
        # Fix German teams in La Liga
        run_script("fix_league_assignments.py", "fixing incorrect league assignments")
        
        # Fix duplicate fixtures
        run_script("fix_duplicate_fixtures.py", "fixing duplicate fixtures")
        
        # Run verification again to confirm fixes
        run_script("verify_team_assignments.py", "post-fix team assignment verification")
    
    # Step 4: Run the count script to show final fixture counts
    run_script("count_fixtures.py", "counting fixtures")
    
    logger.info("="*80)
    logger.info("FIXTURE SYNCHRONIZATION PROCESS COMPLETED")
    logger.info(f"Log file saved to: {LOG_FILE}")
    logger.info("="*80)

if __name__ == "__main__":
    main() 