"""
Flask web application for Customer Support Pipeline
Provides web interface and API endpoints
"""

from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import orchestrator functions
try:
    from orchestrator import (
        authenticate_gmail, 
        fetch_customer_emails, 
        classify_issue, 
        add_to_notion,
        get_notion_summary,
        send_slack_digest,
        run_full_pipeline
    )
    logger.info("Orchestrator imported successfully")
except ImportError as e:
    logger.error(f"Failed to import orchestrator: {e}")
    # Define dummy functions for development
    def authenticate_gmail(): raise NotImplementedError()
    def fetch_customer_emails(*args): raise NotImplementedError()
    def classify_issue(*args): raise NotImplementedError()
    def add_to_notion(*args): raise NotImplementedError()
    def get_notion_summary(): raise NotImplementedError()
    def send_slack_digest(*args): raise NotImplementedError()
    def run_full_pipeline(*args): raise NotImplementedError()

app = Flask(__name__)

# Store last run info
last_run_info = {
    'timestamp': None,
    'status': 'Never run',
    'emails_processed': 0
}

# ============ SCHEDULER SETUP ============

scheduler = BackgroundScheduler()

def scheduled_job():
    """Job that runs automatically"""
    global last_run_info
    logger.info(f"Running scheduled job at {datetime.now()}")
    try:
        result = run_full_pipeline()
        last_run_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Success (Scheduled)',
            'emails_processed': result.get('emails_processed', 0)
        }
        logger.info(f"Scheduled job completed: {result}")
    except Exception as e:
        last_run_info['status'] = f'Error: {str(e)}'
        logger.error(f"Scheduled job failed: {e}")

# Schedule job to run every day at 9 AM
scheduler.add_job(func=scheduled_job, trigger="cron", hour=9, minute=0, id='daily_job')

# ============ ROUTES ============

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', last_run=last_run_info)


@app.route('/health')
def health():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'scheduler_running': scheduler.running
    }), 200


@app.route('/api/fetch', methods=['POST'])
def fetch_emails():
    """Fetch emails from Gmail"""
    try:
        data = request.get_json() or {}
        hours = data.get('hours', 24)
        
        # Validate input
        if not isinstance(hours, (int, float)) or hours < 1 or hours > 168:
            return jsonify({
                'success': False, 
                'error': 'Hours must be between 1 and 168'
            }), 400
        
        service = authenticate_gmail()
        emails = fetch_customer_emails(service, int(hours))
        
        return jsonify({
            'success': True,
            'count': len(emails),
            'emails': emails[:10]  # Return first 10 for preview
        })
    except NotImplementedError:
        return jsonify({
            'success': False, 
            'error': 'Gmail integration not configured'
        }), 501
    except Exception as e:
        logger.error(f"Error fetching emails: {e}")
        return jsonify({
            'success': False, 
            'error': f'Failed to fetch emails: {str(e)}'
        }), 500


@app.route('/api/classify', methods=['POST'])
def classify_single():
    """Classify a single email"""
    try:
        data = request.get_json()
        
        if not data or 'subject' not in data or 'body' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: subject and body'
            }), 400
        
        result = classify_issue(data['subject'], data['body'])
        return jsonify({'success': True, 'classification': result})
        
    except NotImplementedError:
        return jsonify({
            'success': False,
            'error': 'Classification not configured'
        }), 501
    except Exception as e:
        logger.error(f"Error classifying email: {e}")
        return jsonify({
            'success': False,
            'error': f'Classification failed: {str(e)}'
        }), 500


@app.route('/api/run-pipeline', methods=['POST'])
def run_pipeline():
    """Run the full pipeline"""
    global last_run_info
    try:
        data = request.get_json() or {}
        hours = data.get('hours', 24)
        
        # Validate input
        if not isinstance(hours, (int, float)) or hours < 1 or hours > 168:
            return jsonify({
                'success': False,
                'error': 'Hours must be between 1 and 168'
            }), 400
        
        logger.info(f"Running pipeline for last {hours} hours")
        result = run_full_pipeline(int(hours))
        
        last_run_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Success',
            'emails_processed': result.get('emails_processed', 0)
        }
        
        return jsonify({'success': True, 'result': result})
        
    except NotImplementedError:
        return jsonify({
            'success': False,
            'error': 'Pipeline not configured'
        }), 501
    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        last_run_info['status'] = f'Error: {str(e)}'
        return jsonify({
            'success': False,
            'error': f'Pipeline failed: {str(e)}'
        }), 500


@app.route('/api/send-digest', methods=['POST'])
def send_digest():
    """Send Slack digest manually"""
    try:
        summary = get_notion_summary()
        
        if not summary or 'error' in summary:
            return jsonify({
                'success': False,
                'error': f"Failed to get summary: {summary.get('error', 'Unknown error') if summary else 'No data'}"
            }), 500
        
        success = send_slack_digest(summary)
        
        return jsonify({
            'success': success,
            'summary': summary
        })
        
    except NotImplementedError:
        return jsonify({
            'success': False,
            'error': 'Slack integration not configured'
        }), 501
    except Exception as e:
        logger.error(f"Error sending digest: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to send digest: {str(e)}'
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current status"""
    return jsonify({
        'success': True,
        'last_run': last_run_info,
        'scheduler_running': scheduler.running
    })


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


# ============ START APP ============

if __name__ == '__main__':
    # Start scheduler
    if not scheduler.running:
        try:
            scheduler.start()
            logger.info("Scheduler started - will run daily at 9 AM")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
    
    # Get port from environment or use 5000
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port}, debug={debug_mode}")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug_mode)
    finally:
        # Shutdown scheduler on exit
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler shut down")