from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/obtener_musica', methods=['GET'])
def obtener_musica():
    video_id = request.args.get('id')
    if not video_id: return jsonify({"error": "Falta el ID"}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            
            # --- 1. BUSCAMOS EL MEJOR AUDIO SOLO ---
            mejor_audio = next(f['url'] for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none')
            
            # --- 2. BUSCAMOS EL 360P COMBINADO (PARA EL DEFAULT) ---
            url_360 = next((f['url'] for f in info['formats'] if f.get('height') == 360 and f.get('acodec') != 'none'), info.get('url'))

            formatos = []
            resoluciones_vistas = set()
            for f in info.get('formats', []):
                res = f.get('height')
                if res and res not in resoluciones_vistas and f.get('vcodec') != 'none':
                    formatos.append({
                        "res": f"{res}p",
                        "url_video": f.get('url'),
                        "url_audio": mejor_audio # Siempre le mandamos el mejor audio
                    })
                    resoluciones_vistas.add(res)

            formatos.sort(key=lambda x: int(x['res'].replace('p','')), reverse=True)

            return jsonify({
                "url_default": url_360,
                "formatos": formatos
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, threaded=True)