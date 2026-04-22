from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "API de Música Activa - Usa /obtener_musica?id=VIDEO_ID"

@app.route('/obtener_musica', methods=['GET'])
def obtener_musica():
    video_id = request.args.get('id')
    if not video_id: 
        return jsonify({"error": "Falta el ID del video"}), 400

    # Opciones de yt-dlp para ser más flexible y rápido
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'format': 'best',
        'skip_download': True,
        'extract_flat': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            formats = info.get('formats', [])
            
            # --- 1. BUSCAMOS EL MEJOR AUDIO (Con fallback) ---
            # Intentamos buscar solo audio primero
            mejor_audio = next((f['url'] for f in formats 
                               if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
            
            # Si no hay, buscamos cualquiera que tenga audio (aunque tenga video)
            if not mejor_audio:
                mejor_audio = next((f['url'] for f in formats if f.get('acodec') != 'none'), info.get('url'))
            
            # --- 2. BUSCAMOS EL 360P O EL DEFAULT ---
            url_360 = next((f['url'] for f in formats 
                           if f.get('height') == 360 and f.get('acodec') != 'none'), info.get('url'))

            formatos_finales = []
            resoluciones_vistas = set()
            
            for f in formats:
                res = f.get('height')
                # Solo tomamos formatos con video y resolución única
                if res and res not in resoluciones_vistas and f.get('vcodec') != 'none':
                    formatos_finales.append({
                        "res": f"{res}p",
                        "url_video": f.get('url'),
                        "url_audio": mejor_audio
                    })
                    resoluciones_vistas.add(res)

            # Si la lista quedó vacía, enviamos al menos la información base
            if not formatos_finales:
                formatos_finales.append({
                    "res": "default",
                    "url_video": info.get('url'),
                    "url_audio": mejor_audio
                })

            # Ordenar de mayor a menor calidad
            formatos_finales.sort(key=lambda x: int(x['res'].replace('p','')) if 'p' in x['res'] else 0, reverse=True)

            return jsonify({
                "titulo": info.get('title'),
                "url_default": url_360,
                "formatos": formatos_finales
            })
            
    except Exception as e:
        # Esto nos dirá exactamente qué pasó si vuelve a fallar
        return jsonify({"error": f"Error técnico: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, threaded=True)
