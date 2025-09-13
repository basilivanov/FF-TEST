#!/usr/bin/env python3
"""
CI Status API endpoints for handling CI webhooks.
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import time
import logging
import sqlite3
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class CiStatusPayload(BaseModel):
    """CI Status payload model."""
    pr_number: int
    head_sha: str
    context: str  # e.g., "lint", "tests", "build", "smoke"
    state: str    # "success", "failure", "pending", "error"
    description: Optional[str] = None
    target_url: Optional[str] = None


@router.post("/ci/status")
async def post_ci_status(payload: CiStatusPayload, request: Request):
    """Receive CI status updates and trigger merge when all contexts are successful."""
    
    try:
        # Save CI status to database
        conn = sqlite3.connect('./data/test.db')
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mock_ci_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pr_number INTEGER,
                head_sha TEXT,
                context TEXT NOT NULL,
                state TEXT NOT NULL,
                description TEXT,
                target_url TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert CI status
        cursor.execute('''
            INSERT INTO mock_ci_status (pr_number, head_sha, context, state, description, target_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (payload.pr_number, payload.head_sha, payload.context, payload.state, 
              payload.description, payload.target_url))
        
        conn.commit()
        
        logger.info(f"Saved CI status: PR#{payload.pr_number} {payload.context}={payload.state}")
        
        # Check if all required CI contexts are successful
        required_contexts = ['lint', 'tests', 'build', 'smoke']
        successful_contexts = cursor.execute('''
            SELECT DISTINCT context FROM mock_ci_status 
            WHERE pr_number = ? AND head_sha = ? AND state = 'success' AND context IN ('lint', 'tests', 'build', 'smoke')
        ''', [payload.pr_number, payload.head_sha]).fetchall()
        
        successful_context_names = [row[0] for row in successful_contexts]
        all_success = set(successful_context_names) >= set(required_contexts)
        
        logger.info(f"PR#{payload.pr_number}: successful contexts = {successful_context_names}, all_success = {all_success}")
        
        if all_success:
            # Find feature by PR number and create MERGE_PR task
            # First, find feature with this PR
            cursor.execute('''
                SELECT id FROM features 
                WHERE pr_url LIKE ? OR pr_url LIKE ?
            ''', (f'%/pull/{payload.pr_number}%', f'%/pull/{payload.pr_number}'))
            
            feature_row = cursor.fetchone()
            if feature_row:
                feature_id = feature_row[0]
                
                # Check if MERGE_PR task already exists
                cursor.execute('''
                    SELECT COUNT(*) FROM tasks 
                    WHERE feature_id = ? AND role = 'MERGE_PR' AND status IN ('NEW', 'RUNNING')
                ''', (feature_id,))
                
                existing_count = cursor.fetchone()[0]
                
                if existing_count == 0:
                    # Create MERGE_PR task
                    cursor.execute('''
                        INSERT INTO tasks (feature_id, role, status, attempts, payload)
                        VALUES (?, 'MERGE_PR', 'NEW', 0, ?)
                    ''', (feature_id, payload.head_sha))
                    
                    conn.commit()
                    logger.info(f"Created MERGE_PR task for feature #{feature_id}, PR #{payload.pr_number}")
                else:
                    logger.info(f"MERGE_PR task already exists for feature #{feature_id}")
            else:
                logger.warning(f"No feature found for PR #{payload.pr_number}")
        
        conn.close()
        
        return {
            "status": "success",
            "message": f"CI status recorded: {payload.context} = {payload.state}",
            "all_contexts_success": all_success
        }
        
    except Exception as e:
        logger.error(f"Failed to process CI status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process CI status: {str(e)}")