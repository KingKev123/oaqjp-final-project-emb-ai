"""
Flask application for emotion detection.
This module provides a web interface for detecting emotions in text using Watson NLP.
"""

import logging
import json
from flask import Flask, render_template, request
from flask_cors import CORS
from markupsafe import escape
from EmotionDetection import emotion_detector
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


class StructuredLogger:
    """Structured JSON logger for production observability."""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
    
    def _log(self, level, message, **context):
        log_entry = {
            'level': level,
            'message': message,
            **context
        }
        getattr(self.logger, level)(json.dumps(log_entry))
    
    def info(self, message, **context):
        self._log('info', message, **context)
    
    def error(self, message, **context):
        self._log('error', message, **context)
    
    def warning(self, message, **context):
        self._log('warning', message, **context)


logger = StructuredLogger('emotion-detection')

sentry_sdk.init(
    // Health check endpoint
    if (req.url === "/health" && req.method === "GET") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok", timestamp: new Date().toISOString(), uptime: process.uptime() }));
      return;
    }

    dsn=os.environ.get('SENTRY_DSN', ''),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0 if os.environ.get('SENTRY_TRACES_SAMPLE_RATE') is None else float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
    environment=os.environ.get('ENVIRONMENT', 'development'),
    release=os.environ.get('APP_VERSION', 'unknown'),
    send_default_pii=False
)

app = Flask(__name__)
CORS(app, origins="*")

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


@app.route("/")
def render_index_page():
    """
    Render the main index page.
    
    Returns:
        str: Rendered HTML template for the index page
    """
    logger.info('Rendering index page')
    return render_template('index.html')


@app.route("/emotionDetector")
def emotion_detector_app():
    """
    Handle emotion detection requests.
    
    Gets text from query parameters, analyzes emotions, and returns formatted response.
    For invalid input, returns error message.
    
    Returns:
        str: Formatted emotion analysis result or error message
    """
    if (!request.body || typeof request.body !== "object") {
      return reply.code(400).send({ error: "Invalid request body" });
    }
    text_to_analyze = request.args.get('textToAnalyze')
    
    logger.info('Emotion detection request received', text_length=len(text_to_analyze) if text_to_analyze else 0)

    response = emotion_detector(text_to_analyze)

    if response['dominant_emotion'] is None:
        logger.warning('Invalid text provided for emotion detection', text=text_to_analyze)
        return "Invalid text! Please try again!"

    logger.info('Emotion detection completed', dominant_emotion=response['dominant_emotion'])
    
    formatted_response = (
        f"For the given statement, the system response is "
        f"'anger': {escape(response['anger'])}, 'disgust': {escape(response['disgust'])}, "
        f"'fear': {escape(response['fear'])}, 'joy': {escape(response['joy'])} and "
        f"'sadness': {escape(response['sadness'])}. "
        f"The dominant emotion is <b>{escape(response['dominant_emotion'])}</b>."
    )

    return formatted_response


@app.errorhandler(Exception)
def handle_exception(e):
    """Capture unhandled exceptions in Sentry."""
    logger.error('Unhandled exception occurred', error=str(e), error_type=type(e).__name__)
    sentry_sdk.capture_exception(e)
    return "An error occurred. Our team has been notified.", 500


if __name__ == "__main__":
    import os
    import signal
    import sys
    import threading
    
    port = int(os.environ.get('PORT', 5000))
    is_production = any([
        os.environ.get('FLASK_ENV') == 'production',
        os.environ.get('ENV') == 'production',
        os.environ.get('ENVIRONMENT') == 'production',
        os.environ.get('PYTHON_ENV') == 'production'
    ])
    if is_production:
        debug_mode = False
    else:
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    def shutdown_handler(signum, frame):
        """Handle graceful shutdown on SIGTERM and SIGINT."""
        sig_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
        logger.info('Shutdown signal received', signal=sig_name)
        
        def force_exit():
            logger.error('Forcing shutdown after timeout')
            os._exit(1)
        
        timer = threading.Timer(30.0, force_exit)
        timer.daemon = True
        timer.start()
        
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info('Starting Flask application', port=port, debug=debug_mode, environment='production' if is_production else 'development')
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
