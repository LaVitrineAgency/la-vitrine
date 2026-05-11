from flask import Flask, render_template, request, jsonify
import anthropic
import os
import json

app = Flask(__name__)

SYSTEM_PROMPT = """Tu es un expert en création d'images pour réseaux sociaux.
Tu génères des prompts DÉTAILLÉS et COMPLETS pour Runway ML / DALL-E / Midjourney.

Les prompts doivent INCLURE le texte directement dans la description visuelle.
L'IA génératrice doit pouvoir créer l'image AVEC le texte positionné dessus.

Format de sortie JSON UNIQUEMENT:
{
  "post_id": 1,
  "platform": "Instagram",
  "post_text": "Texte du post (avec émojis et hashtags)",
  "image_prompt": "Prompt COMPLET et DÉTAILLÉ pour générer l'image AVEC le texte intégré",
  "image_dimensions": "1080x1080 (Instagram) ou 1200x627 (LinkedIn)",
  "style_notes": "Style visuel général",
  "text_placement": "Description où le texte doit apparaître"
}

Important:
- Le prompt image doit décrire le TEXTE comme faisant PARTIE de l'image visuelle
- Inclure : composition, éclairage, ambiance, palette de couleurs, style photographique
- Être très descriptif et précis
- Format qui fonctionne bien avec Runway ML / DALL-E / Midjourney
- Retourner VALIDE JSON UNIQUEMENT"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        
        # Récupérer la clé API
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY non définie'}), 400
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construire le prompt utilisateur
        business_name = data.get('business_name', 'Mon Entreprise')
        sector = data.get('sector', 'Général')
        brand_values = data.get('brand_values', 'Qualité')
        brand_colors = data.get('brand_colors', 'Neutre')
        
        user_prompt = f"""Génère 1 post Instagram COMPLET pour:
- Entreprise: {business_name}
- Secteur: {sector}
- Valeurs: {brand_values}
- Couleurs: {brand_colors}

Crée un POST ACCUEILLANT et PROFESSIONNEL.

Le prompt image doit être ULTRA DÉTAILLÉ et inclure le texte comme partie de l'image.
Exemple: "...with bold white text reading '[POST_TEXT]' positioned at the top-center in Poppins Bold font..."

Retourne VALIDE JSON UNIQUEMENT, pas de markdown."""
        
        message = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Parser JSON
        try:
            post_data = json.loads(response_text)
        except json.JSONDecodeError:
            # Essayer extraire JSON du texte
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                post_data = json.loads(json_match.group())
            else:
                return jsonify({'error': 'JSON parsing failed', 'raw': response_text}), 400
        
        return jsonify({
            'success': True,
            'message': f'✓ Post généré pour {business_name}',
            'post': post_data
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-prompt', methods=['POST'])
def download_prompt():
    """Télécharger le prompt en JSON"""
    try:
        data = request.json
        post = data.get('post', {})
        
        return jsonify({
            'success': True,
            'filename': f"runway_prompt_{post.get('post_id', 1)}.json",
            'content': post
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
