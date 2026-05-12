import logging
import sys

# ---------------------------------------------------------------------------
# Logging — configured before any other import so initialisation errors are
# captured and visible in Gunicorn / Railway logs.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

logger.info("Starting la-vitrine app — importing dependencies…")

try:
    from flask import Flask, render_template, request, jsonify
    import traceback
    logger.info("Flask imported successfully")
except Exception as e:
    logger.critical("Failed to import Flask: %s", e, exc_info=True)
    sys.exit(1)

try:
    import anthropic
    logger.info("anthropic imported successfully")
except Exception as e:
    logger.critical("Failed to import anthropic: %s", e, exc_info=True)
    sys.exit(1)

try:
    import os
    import json
    import uuid
    import re
    logger.info("Standard-library imports successful")
except Exception as e:
    logger.critical("Failed to import standard-library modules: %s", e, exc_info=True)
    sys.exit(1)

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------
logger.info("Creating Flask application…")
try:
    app = Flask(__name__)
    logger.info("Flask application created successfully")
except Exception as e:
    logger.critical("Failed to create Flask application: %s", e, exc_info=True)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Global error handler
# ---------------------------------------------------------------------------

@app.errorhandler(Exception)
def handle_exception(e):
    """Catch-all handler — logs every unhandled exception with a full
    traceback so the root cause is always visible in the logs."""
    logger.error(
        "Unhandled exception: %s\n%s",
        e,
        traceback.format_exc(),
    )
    return jsonify({'error': 'Internal server error', 'detail': str(e)}), 500


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/health')
def health():
    """Simple health-check endpoint — confirms the app is up and reachable."""
    logger.debug("Health check requested")
    return jsonify({'status': 'ok', 'service': 'la-vitrine'}), 200


@app.route('/')
def index():
    logger.debug("Index route called")
    try:
        new_uuid = str(uuid.uuid4())
        logger.debug("Generated UUID: %s", new_uuid)
        response = f'''<h2>La Vitrine</h2>
    <p>Lien client : <a href="/client/{new_uuid}">/client/{new_uuid}</a></p>'''
        logger.debug("Index route rendered successfully")
        return response
    except Exception as e:
        logger.error(
            "Exception in index route: %s\n%s",
            e,
            traceback.format_exc(),
        )
        raise


@app.route('/client/<client_uuid>')
def client_form(client_uuid):
    logger.debug("Client form route called for uuid=%s", client_uuid)
    try:
        logger.debug("Attempting to render template 'index.html' for uuid=%s", client_uuid)
        rendered = render_template('index.html', client_uuid=client_uuid)
        logger.debug("Template 'index.html' rendered successfully for uuid=%s", client_uuid)
        return rendered
    except Exception as e:
        logger.error(
            "Exception rendering template for uuid=%s: %s\n%s",
            client_uuid,
            e,
            traceback.format_exc(),
        )
        raise


@app.route('/api/generate/<client_uuid>', methods=['POST'])
def generate(client_uuid):
    logger.info("Generate route called for uuid=%s", client_uuid)
    try:
        data = request.json
        logger.debug("Request payload: %s", data)

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            logger.error("ANTHROPIC_API_KEY environment variable is not set")
            return jsonify({'error': 'ANTHROPIC_API_KEY manquante'}), 400

        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Génère 16 posts LinkedIn pour :
- Nom : {data.get('nom', '')}
- Secteur : {data.get('secteur', '')}
- Offres/Services : {data.get('offres', '')}
- Résultats/Promesse : {data.get('resultats', '')}
- Ton : {data.get('ton', '')}
4 posts par ton : Inspirant, Expert/Autorité, Storytelling, Humour.
Pour chaque post, retourne JSON avec : post_id, ton, contenu, prompt_image, hashtags.
Retourne un tableau JSON de 16 objets UNIQUEMENT."""

        logger.info("Sending request to Anthropic API…")
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info("Anthropic API response received")

        response_text = message.content[0].text
        # Extraction du JSON dans la réponse
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        posts = json.loads(json_match.group()) if json_match else []
        logger.info("Parsed %d posts from API response", len(posts))

        return jsonify({
            'success': True,
            'client_uuid': client_uuid,
            'posts': posts
        })
    except Exception as e:
        logger.exception("Unhandled error in /api/generate/%s: %s", client_uuid, e)
        return jsonify({'error': str(e)}), 500


logger.info("All routes registered — app ready")
