from flask import Flask, request, render_template, redirect, session
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = "supersegreto"
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'
SCOPE = "playlist-modify-public"

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=SCOPE
)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload_txt_single', methods=['POST'])
def upload_txt_single():
    playlist_name = request.form['playlist_name']
    righe = request.files['brani'].read().decode("utf-8").splitlines()
    brani = [riga.strip() for riga in righe if riga.strip()]
    session['playlist_name'] = playlist_name
    session['brani'] = brani

    auth_url = sp_oauth.get_authorize_url()
    return f'''
    <h2>Autorizzazione richiesta</h2>
    <p><a href="{auth_url}" target="_blank">Clicca qui per autorizzare su Spotify</a></p>
    <form action="/callback" method="get">
        <label>Codice ottenuto (?code=...):</label><br>
        <input name="code" style="width:400px"><br><br>
        <button type="submit">Invia codice</button>
    </form>
    '''

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    sp = spotipy.Spotify(auth=token_info['access_token'])

    user_id = sp.current_user()["id"]
    playlist = sp.user_playlist_create(user=user_id, name=session['playlist_name'])

    track_uris = []
    for brano in session['brani']:
        result = sp.search(q=brano, type='track', limit=1)
        if result['tracks']['items']:
            uri = result['tracks']['items'][0]['uri']
            track_uris.append(uri)

    for i in range(0, len(track_uris), 100):
        sp.playlist_add_items(playlist['id'], track_uris[i:i+100])

    return f"✅ Playlist '{session['playlist_name']}' creata con {len(track_uris)} brani!"

if __name__ == "__main__":
    app.run(debug=False)
