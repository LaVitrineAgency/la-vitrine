from flask import Flask, render_template, request, jsonify
import anthropic
import os
import json
import uuid
import re

app = Flask(__name__)

@app.route('/')
def index():
    new_uuid = str(uuid.uuid4())
    return f'''<h2>La Vitrine</h2>
    <p>Lien client : <a href="/client/{new_uuid}">/client/{new_uuid}</a></p>'''

@app.route('/client/<client_uuid>')
def client_form(client_uuid):
    return render_template('index.html', client_uuid=client_uuid)

@app.route('/api/generate/<client_uuid>', methods=['POST'])
def generate(client_uuid):
    try:
        data = request.json
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
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
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = message.content[0].text
        # Extraction du JSON dans la réponse
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        posts = json.loads(json_match.group()) if json_match else []
        
        return jsonify({
            'success': True,
            'client_uuid': client_uuid,
            'posts': posts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
