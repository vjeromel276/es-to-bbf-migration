"""
Centralized Credentials Module for ES to BBF Migration
=======================================================

This module loads credentials from .env file to avoid hardcoding
sensitive data in notebooks and scripts.

Usage in notebooks:
-------------------
    from credentials import get_es_credentials, get_bbf_credentials, get_oss_credentials

    # For ES UAT (sandbox)
    es_creds = get_es_credentials(environment='uat')
    es_sf = Salesforce(**es_creds)

    # For ES Production
    es_creds = get_es_credentials(environment='prod')
    es_sf = Salesforce(**es_creds)

    # For BBF
    bbf_creds = get_bbf_credentials()
    bbf_sf = Salesforce(**bbf_creds)

    # For OSS database
    oss_creds = get_oss_credentials()

Usage in Python scripts:
------------------------
    from credentials import (
        ES_UAT_USERNAME, ES_UAT_PASSWORD, ES_UAT_TOKEN, ES_UAT_DOMAIN,
        ES_PROD_USERNAME, ES_PROD_PASSWORD, ES_PROD_TOKEN, ES_PROD_DOMAIN,
        BBF_USERNAME, BBF_PASSWORD, BBF_TOKEN, BBF_DOMAIN,
        OSS_USERNAME, OSS_PASSWORD, OSS_HOST, OSS_DATABASE, OSS_PORT
    )
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find and load .env file from project root
_project_root = Path(__file__).parent
_env_file = _project_root / '.env'

if _env_file.exists():
    load_dotenv(_env_file)
else:
    # Try parent directories
    for parent in _project_root.parents:
        _env_file = parent / '.env'
        if _env_file.exists():
            load_dotenv(_env_file)
            break
    else:
        print("WARNING: .env file not found. Please create one from .env.example")


# ========================================
# ES (EverStream) UAT Sandbox Credentials
# ========================================
ES_UAT_USERNAME = os.getenv('ES_UAT_USERNAME', '')
ES_UAT_PASSWORD = os.getenv('ES_UAT_PASSWORD', '')
ES_UAT_TOKEN = os.getenv('ES_UAT_TOKEN', '')
ES_UAT_DOMAIN = os.getenv('ES_UAT_DOMAIN', 'test')

# ========================================
# ES (EverStream) Production Credentials
# ========================================
ES_PROD_USERNAME = os.getenv('ES_PROD_USERNAME', '')
ES_PROD_PASSWORD = os.getenv('ES_PROD_PASSWORD', '')
ES_PROD_TOKEN = os.getenv('ES_PROD_TOKEN', '')
ES_PROD_DOMAIN = os.getenv('ES_PROD_DOMAIN', 'login')

# ========================================
# BBF (BlueBird Fiber) Credentials
# ========================================
BBF_USERNAME = os.getenv('BBF_USERNAME', '')
BBF_PASSWORD = os.getenv('BBF_PASSWORD', '')
BBF_TOKEN = os.getenv('BBF_TOKEN', '')
BBF_DOMAIN = os.getenv('BBF_DOMAIN', 'test')

# ========================================
# OSS Database Credentials
# ========================================
OSS_USERNAME = os.getenv('OSS_USERNAME', '')
OSS_PASSWORD = os.getenv('OSS_PASSWORD', '')
OSS_HOST = os.getenv('OSS_HOST', '')
OSS_DATABASE = os.getenv('OSS_DATABASE', '')
OSS_PORT = os.getenv('OSS_PORT', '5432')
OSS_API_PASSWORD = os.getenv('OSS_API_PASSWORD', '')


def get_es_credentials(environment='uat'):
    """
    Get ES Salesforce credentials for simple_salesforce.

    Args:
        environment: 'uat' for sandbox, 'prod' for production

    Returns:
        dict: Credentials dict ready for Salesforce() constructor

    Example:
        from simple_salesforce import Salesforce
        from credentials import get_es_credentials

        es_sf = Salesforce(**get_es_credentials('uat'))
    """
    if environment.lower() in ('uat', 'sandbox', 'test'):
        return {
            'username': ES_UAT_USERNAME,
            'password': ES_UAT_PASSWORD,
            'security_token': ES_UAT_TOKEN,
            'domain': ES_UAT_DOMAIN,
        }
    elif environment.lower() in ('prod', 'production', 'login'):
        return {
            'username': ES_PROD_USERNAME,
            'password': ES_PROD_PASSWORD,
            'security_token': ES_PROD_TOKEN,
            'domain': ES_PROD_DOMAIN,
        }
    else:
        raise ValueError(f"Unknown environment: {environment}. Use 'uat' or 'prod'.")


def get_bbf_credentials():
    """
    Get BBF Salesforce credentials for simple_salesforce.

    Returns:
        dict: Credentials dict ready for Salesforce() constructor

    Example:
        from simple_salesforce import Salesforce
        from credentials import get_bbf_credentials

        bbf_sf = Salesforce(**get_bbf_credentials())
    """
    return {
        'username': BBF_USERNAME,
        'password': BBF_PASSWORD,
        'security_token': BBF_TOKEN,
        'domain': BBF_DOMAIN,
    }


def get_oss_credentials():
    """
    Get OSS database credentials for psycopg2.

    Returns:
        dict: Credentials dict ready for psycopg2.connect()

    Example:
        import psycopg2
        from credentials import get_oss_credentials

        conn = psycopg2.connect(**get_oss_credentials())
    """
    return {
        'user': OSS_USERNAME,
        'password': OSS_PASSWORD,
        'host': OSS_HOST,
        'database': OSS_DATABASE,
        'port': OSS_PORT,
    }


def get_oss_api_credentials():
    """
    Get OSS API credentials (if different from database).

    Returns:
        dict: API credentials
    """
    return {
        'username': OSS_USERNAME,
        'password': OSS_API_PASSWORD,
    }


# ========================================
# Heroku Database Credentials
# ========================================
HEROKU_DB_NAME = os.getenv('HEROKU_DB_NAME', '')
HEROKU_DB_USER = os.getenv('HEROKU_DB_USER', '')
HEROKU_DB_PASSWORD = os.getenv('HEROKU_DB_PASSWORD', '')
HEROKU_DB_HOST = os.getenv('HEROKU_DB_HOST', '')
HEROKU_DB_PORT = os.getenv('HEROKU_DB_PORT', '5432')

# ========================================
# GLC OSS Database Credentials
# ========================================
GLC_OSS_DB_NAME = os.getenv('GLC_OSS_DB_NAME', '')
GLC_OSS_DB_USER = os.getenv('GLC_OSS_DB_USER', '')
GLC_OSS_DB_PASSWORD = os.getenv('GLC_OSS_DB_PASSWORD', '')
GLC_OSS_DB_HOST = os.getenv('GLC_OSS_DB_HOST', '')
GLC_OSS_DB_PORT = os.getenv('GLC_OSS_DB_PORT', '5432')


def get_heroku_db_credentials():
    """
    Get Heroku database credentials for psycopg2.

    Returns:
        dict: Credentials dict ready for psycopg2.connect()

    Example:
        import psycopg2
        from credentials import get_heroku_db_credentials

        conn = psycopg2.connect(**get_heroku_db_credentials())
    """
    return {
        'dbname': HEROKU_DB_NAME,
        'user': HEROKU_DB_USER,
        'password': HEROKU_DB_PASSWORD,
        'host': HEROKU_DB_HOST,
        'port': HEROKU_DB_PORT,
    }


def get_glc_oss_credentials():
    """
    Get GLC OSS database credentials for psycopg2.

    Returns:
        dict: Credentials dict ready for psycopg2.connect()

    Example:
        import psycopg2
        from credentials import get_glc_oss_credentials

        conn = psycopg2.connect(**get_glc_oss_credentials())
    """
    return {
        'dbname': GLC_OSS_DB_NAME,
        'user': GLC_OSS_DB_USER,
        'password': GLC_OSS_DB_PASSWORD,
        'host': GLC_OSS_DB_HOST,
        'port': GLC_OSS_DB_PORT,
    }


def validate_credentials():
    """
    Validate that all required credentials are loaded.

    Returns:
        tuple: (is_valid: bool, missing: list)
    """
    missing = []

    # Check ES UAT
    if not ES_UAT_USERNAME:
        missing.append('ES_UAT_USERNAME')
    if not ES_UAT_PASSWORD:
        missing.append('ES_UAT_PASSWORD')
    if not ES_UAT_TOKEN:
        missing.append('ES_UAT_TOKEN')

    # Check ES Prod
    if not ES_PROD_USERNAME:
        missing.append('ES_PROD_USERNAME')
    if not ES_PROD_PASSWORD:
        missing.append('ES_PROD_PASSWORD')
    if not ES_PROD_TOKEN:
        missing.append('ES_PROD_TOKEN')

    # Check BBF
    if not BBF_USERNAME:
        missing.append('BBF_USERNAME')
    if not BBF_PASSWORD:
        missing.append('BBF_PASSWORD')
    if not BBF_TOKEN:
        missing.append('BBF_TOKEN')

    return (len(missing) == 0, missing)


# Validate on import and warn if credentials are missing
_is_valid, _missing = validate_credentials()
if not _is_valid:
    print(f"WARNING: Missing credentials in .env: {', '.join(_missing)}")
    print("Please check your .env file and ensure all required values are set.")
