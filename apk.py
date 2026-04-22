from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

@app.route('/obtener_musica', methods=['GET'])
def obtener_musica():
    video_id = request.args.get('id')
    if not video_id: 
        return jsonify({"error": "Falta el ID del video"}), 400

    # Opciones optimizadas para rapidez y evitar bloqueos
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'format': 'best',
        'skip_download': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # --- 1. BUSCAMOS EL MEJOR AUDIO SOLO ---
            # Usamos None como default para evitar StopIteration si no hay formatos de solo audio
            mejor_audio = next((f['url'] for f in info['formats'] 
                               if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
            
            # Si no hay "solo audio", tomamos la URL base de la info
            if not mejor_audio:
                mejor_audio = info.get('url')
            
            # --- 2. BUSCAMOS EL 360P COMBINADO (PARA EL DEFAULT) ---
            url_360 = next((f['url'] for f in info['formats'] 
                           if f.get('height') == 360 and f.get('acodec') != 'none'), info.get('url'))

            formatos = []
            resoluciones_vistas = set()
            
            for f in info.get('formats', []):
                res = f.get('height')
                # Solo tomamos formatos de video con resolución clara y que no hayamos procesado
                if res and res not in resoluciones_vistas and f.get('vcodec') != 'none':
                    formatos.append({
                        "res": f"{res}p",
                        "url_video": f.get('url'),
                        "url_audio": mejor_audio
                    })
                    resoluciones_vistas.add(res)

            # Ordenar de mayor a menor resolución
            formatos.sort(key=lambda x: int(x['res'].replace('p','')), reverse=True)

            return jsonify({
                "titulo": info.get('title'),
                "duracion": info.get('duration'),
                "url_default": url_360,
                "formatos": formatos
            })
            
    except Exception as e:
        return jsonify({"error": f"Error al procesar video: {str(e)}"}), 500

if __name__ == '__main__':
    # CRITICAL: Render requiere leer la variable PORT
    port = int(os.environ.get("PORT", 7860))
    app.run(host='0.0.0.0', port=port, threaded=True)
