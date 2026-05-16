from flask import Flask, render_template, request, jsonify
import anthropic
import os
import json
import uuid
import resend

app = Flask(__name__)

resend.api_key = os.getenv('RESEND_API_KEY')
THIERRY_EMAIL = "lavitrine.agency@gmail.com"

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/')
def index():
    new_uuid = str(uuid.uuid4())
    return f'''<h2>La Vitrine</h2>
    <p>Lien client : <a href="/client/{new_uuid}">/client/{new_uuid}</a></p>'''

@app.route('/client/<client_uuid>')
def client_form(client_uuid):
    return render_template('index.html', client_uuid=client_uuid)

@app.route('/api/test-visuel/<client_uuid>', methods=['POST'])
def test_visuel(client_uuid):
    try:
        data = request.json
        client_email = data.get('email', '')
        client_nom = data.get('nom', '')
        secteur = data.get('secteur', '')
        offre = data.get('offre', '')
        style = data.get('style', '')
        couleurs = data.get('couleurs', '')
        intention = data.get('intention', '')

        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"Genere un prompt detaille pour Runway ML pour creer un visuel LinkedIn professionnel. Client: {client_nom}. Secteur: {secteur}. Offre: {offre}. Style visuel: {style}. Couleurs: {couleurs}. Intention: {intention}. Le prompt doit etre en anglais, ultra detaille, inclure composition, eclairage, ambiance, palette, style photographique, texte a integrer. Retourne UNIQUEMENT le prompt."
            }]
        )
        prompt_runway = message.content[0].text

        resend.Emails.send({
            "from": "La Vitrine <onboarding@resend.dev>",
            "to": client_email,
            "subject": "Votre visuel de test est en cours de creation",
            "html": f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px'><h2>Bonjour {client_nom}</h2><p>Votre visuel de test La Vitrine est en cours de creation.</p><p>Vous le recevrez sous 24h.</p><p>L'equipe La Vitrine</p></div>"
        })

        resend.Emails.send({
            "from": "La Vitrine <onboarding@resend.dev>",
            "to": THIERRY_EMAIL,
            "subject": f"Nouveau visuel de test - {client_nom}",
            "html": f"<div style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px'><h2>Nouveau client</h2><p><b>Client:</b> {client_nom}</p><p><b>Email:</b> {client_email}</p><p><b>Secteur:</b> {secteur}</p><p><b>Offre:</b> {offre}</p><p><b>Style:</b> {style}</p><p><b>Couleurs:</b> {couleurs}</p><p><b>Intention:</b> {intention}</p><div style='background:#f5f5f5;padding:16px;border-radius:8px;margin:20px 0'><h3>Prompt Runway ML:</h3><p style='font-family:monospace;font-size:13px'>{prompt_runway}</p></div></div>"
        })

        return jsonify({'success': True, 'message': 'Emails envoyes'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate/<client_uuid>', methods=['POST'])
def generate(client_uuid):
    try:
        data = request.json
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY manquante'}), 400

        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"Genere 16 posts LinkedIn pour : Nom: {data.get('nom', '')}. Secteur: {data.get('secteur', '')}. Offre: {data.get('offre', '')}. Benefices: {data.get('benefices', '')}. Ton: {data.get('ton', '')}. Couleurs: {data.get('couleurs', '')}. Style: {data.get('style', '')}. Intention: {data.get('intention', '')}. 4 posts par ton : Inspirant, Expert, Storytelling, Humour. Pour chaque post retourne JSON avec : post_id, ton, contenu, prompt_image, hashtags. Retourne un tableau JSON de 16 objets UNIQUEMENT."

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text
        import re
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        posts = json.loads(json_match.group()) if json_match else []

        return jsonify({'success': True, 'client_uuid': client_uuid, 'posts': posts})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
