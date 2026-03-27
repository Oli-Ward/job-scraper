"""
Job data validators to ensure data quality and prevent blank rows.
"""
import logging

logger = logging.getLogger("JobScraper.Validators")

def validate_job(job_data):
    """
    Validate a job dictionary before adding to results.
    
    Args:
        job_data: Dictionary with job information
        
    Returns:
        bool: True if job is valid, False otherwise
    """
    # Required fields
    required_fields = ["site", "title", "job_url"]
    
    for field in required_fields:
        if field not in job_data:
            logger.debug(f"Missing required field '{field}' in job data")
            return False
        
        value = job_data[field]
        
        # Check if value is None or empty string
        if value is None:
            logger.debug(f"Field '{field}' is None")
            return False
        
        if isinstance(value, str) and not value.strip():
            logger.debug(f"Field '{field}' is empty or whitespace")
            return False
    
    # Validate job_url is a valid URL format
    job_url = job_data["job_url"]
    if not job_url.startswith("http://") and not job_url.startswith("https://"):
        logger.debug(f"Invalid job_url format: {job_url}")
        return False
    
    return True

def validate_and_clean_job(job_data):
    """
    Validate and clean a job dictionary.
    Strips whitespace from string fields and validates required fields.
    
    Args:
        job_data: Dictionary with job information
        
    Returns:
        dict or None: Cleaned job data if valid, None otherwise
    """
    # Create a copy to avoid modifying original
    cleaned = job_data.copy()
    
    # Strip whitespace from string fields
    for key, value in cleaned.items():
        if isinstance(value, str):
            cleaned[key] = value.strip()
    
    # Validate
    if not validate_job(cleaned):
        return None
    
    return cleaned
