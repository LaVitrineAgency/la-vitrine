from flask import Flask, render_template, request, jsonify
import anthropic
import os
import json
import uuid
import resend

app = Flask(__name__)

resend.api_key = os.getenv('RESEND_API_KEY')
THIERRY_EMAIL = "ton@email.com"  # ← mets ton email ici

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

        # Générer le prompt Runway via Claude
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""Génère un prompt DÉTAILLÉ pour Runway ML pour créer un visuel LinkedIn professionnel.

Client : {client_nom}
Secteur : {secteur}
Offre : {offre}
Style visuel : {style}
Couleurs : {couleurs}
Intention : {intention}

Le prompt doit être en anglais, ultra détaillé, inclure : composition, éclairage, ambiance, palette, style photographique, texte à intégrer.
Retourne UNIQUEMENT le prompt, rien d'autre."""
            }]
        )
        prompt_runway = message.content[0].text

        # Email au client
        resend.Emails.send({
            "from": "La Vitrine <onboarding@resend.dev>",
            "to": client_email,
            "subject": "✨ Votre visuel de test est en cours de création !",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
                <h2 style="color:#1A1714">Bonjour {client_nom} ! 👋</h2>
                <p>Votre visuel de test <strong>La Vitrine</strong> est en cours de création.</p>
                <p>Vous le recevrez dans votre dossier Drive sous <strong>24h</strong>.</p>
                <div style="background:#FDF9F3;border-left:4px solid #C9A96E;padding:16px;margin:20px 0;border-radius:4px">
                    <p style="color:#8C8480;font-size:14px;margin:0">Notre équipe travaille sur un visuel personnalisé basé sur votre brief.</p>
                </div>
                <p>À très vite,<br><strong>L'équipe La Vitrine</strong></p>
            </div>
            """
        })

        # Notification à Thierry
        resend.Emails.send({
            "from": "La Vitrine <onboarding@resend.dev>",
            "to": THIERRY_EMAIL,
            "subject": f"🎨 Nouveau visuel de test demandé — {client_nom}",
            "html": f"""
            <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
                <h2>Nouveau client — Visuel de test à créer !</h2>
                <p><strong>Client :</strong> {client_nom}</p>
                <p><strong>Email :</strong> {client_email}</p>
                <p><strong>Secteur :</strong> {secteur}</p>
                <p><strong>Offre :</strong> {offre}</p>
                <p><strong>Style :</strong> {style}</p>
                <p><strong>Couleurs :</strong> {couleurs}</p>
                <p><strong>Intention :</strong> {intention}</p>
                <div style="background:#f5f5f5;padding:16px;border-radius:8px;margin:20px 0">
                    <h3>🎬 Prompt Runway ML :</h3>
                    <p style="font-family:monospace;font-size:13px">{prompt_runway}</p>
                </div>
                <p>→ Crée le visuel sur Runway et dépose-le dans le Drive du client !</p>
            </div>
            """
        })

        return jsonify({'success': True, 'message': 'Emails envoyés !'})

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

        prompt = f"""Génère 16 posts LinkedIn pour :
- Nom : {data.get('nom', '')}
- Secteur : {data.get('secteur', '')}
- Offres/Services : {data.get('offres', '')}
- Résultats/Promesse : {data.get('resultats', '')}
- Ton : {data.get('ton', '')}
- Couleurs marque : {data.get('couleurs', '')}
- Style : {data.get('style', '')}
- Intention : {data.get('intention', '')}

4 posts par ton : Inspirant, Expert/Autorité, Storytelling, Humour.
Pour chaque post retourne JSON avec : post_id, ton, contenu, prompt_image, hashtags.
