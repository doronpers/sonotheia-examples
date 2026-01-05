"""
Audio processor Lambda function for Sonotheia API.

This function is triggered by S3 uploads and processes audio files through
the Sonotheia API.

Environment Variables:
    DYNAMODB_TABLE: DynamoDB table name for session storage
    S3_BUCKET: S3 bucket name for audio file storage
    API_KEY_SECRET_ARN: Secrets Manager ARN for Sonotheia API key
    SONOTHEIA_API_URL: Sonotheia API base URL
    ENVIRONMENT: Environment name (dev/staging/prod)
"""

import json
import os
import boto3
import requests
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
secretsmanager = boto3.client('secretsmanager')

# Environment variables
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
S3_BUCKET = os.environ['S3_BUCKET']
API_KEY_SECRET_ARN = os.environ['API_KEY_SECRET_ARN']
SONOTHEIA_API_URL = os.environ['SONOTHEIA_API_URL']
ENVIRONMENT = os.environ['ENVIRONMENT']


def lambda_handler(event, context):
    """
    Lambda handler for S3 audio file uploads.
    
    Args:
        event: S3 event notification
        context: Lambda context
        
    Returns:
        dict: Processing results
    """
    try:
        # Get API key from Secrets Manager
        api_key = get_api_key()
        
        results = []
        
        # Process each S3 record
        for record in event.get('Records', []):
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Processing audio file: s3://{bucket}/{key}")
            
            # Download audio file
            audio_data = download_audio(bucket, key)
            
            # Send to Sonotheia API
            result = process_audio(audio_data, api_key)
            
            # Store result in DynamoDB
            store_result(key, result)
            
            # Move processed file to processed/ folder
            move_to_processed(bucket, key)
            
            results.append({
                'file': key,
                'status': 'success',
                'result': result
            })
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': len(results),
                'results': results
            })
        }
        
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'message': str(e)
            })
        }


def get_api_key():
    """Retrieve Sonotheia API key from Secrets Manager."""
    response = secretsmanager.get_secret_value(SecretId=API_KEY_SECRET_ARN)
    return response['SecretString']


def download_audio(bucket, key):
    """Download audio file from S3."""
    response = s3.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()


def process_audio(audio_data, api_key):
    """Send audio to Sonotheia API for processing."""
    url = f"{SONOTHEIA_API_URL}/v1/voice/deepfake"
    
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    files = {
        'audio': ('audio.wav', audio_data, 'audio/wav')
    }
    
    response = requests.post(url, headers=headers, files=files, timeout=30)
    response.raise_for_status()
    
    return response.json()


def store_result(filename, result):
    """Store processing result in DynamoDB."""
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    session_id = result.get('session_id', filename)
    timestamp = int(datetime.utcnow().timestamp())
    
    # Calculate TTL (90 days from now)
    ttl = timestamp + (90 * 24 * 60 * 60)
    
    item = {
        'session_id': session_id,
        'timestamp': timestamp,
        'event_type': 'audio_processed',
        'data': {
            'filename': filename,
            'score': result.get('score'),
            'label': result.get('label'),
            'latency_ms': result.get('latency_ms')
        },
        'ttl': ttl
    }
    
    table.put_item(Item=item)
    print(f"Stored result in DynamoDB: {session_id}")


def move_to_processed(bucket, key):
    """Move processed file to processed/ folder."""
    # Extract filename from key
    filename = key.split('/')[-1]
    new_key = f"processed/{filename}"
    
    # Copy to new location
    s3.copy_object(
        Bucket=bucket,
        CopySource={'Bucket': bucket, 'Key': key},
        Key=new_key
    )
    
    # Delete original
    s3.delete_object(Bucket=bucket, Key=key)
    
    print(f"Moved file to: s3://{bucket}/{new_key}")
