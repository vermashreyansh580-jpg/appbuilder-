from flask import Flask, render_template, request, jsonify, send_file
import google.generativeai as genai
from supabase import create_client, Client
import io, re, base64, json, datetime, zipfile

app = Flask(__name__)

# --- CONFIG ---
GEMINI_KEY = "AIzaSyCLMcD33glXsaNHw9f094DblYilJI1BxeI"
genai.configure(api_key=GEMINI_KEY)

SUPABASE_URL = "https://bhswajnmodtdzupedxnk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoc3dham5tb2R0ZHp1cGVkeG5rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2MzMxNTksImV4cCI6MjA4NjIwOTE1OX0.gYUqTUyrxv36Ognyg7gyfJ991Vum_TqykC393o6i3zY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

WHATSAPP = "917704843966"
RAZORPAY = "https://rzp.io/rzp/KkySIH1U"
PRICE = 259
FREE_CREDS = 20

# --- DB HELPERS ---
def get_user(ip):
    try:
        res = supabase.table('user_credits').select("*").eq('user_id', ip).execute()
        if not res.data:
            supabase.table('user_credits').insert({"user_id": ip, "credits": FREE_CREDS, "is_premium": False}).execute()
            return FREE_CREDS, False
        return res.data[0]['credits'], res.data[0]['is_premium']
    except: return FREE_CREDS, False

def deduct(ip):
    c, p = get_user(ip)
    if not p and c > 0:
        supabase.table('user_credits').update({"credits": c - 1}).eq('user_id', ip).execute()

def upgrade(ip):
    supabase.table('user_credits').update({"is_premium": True, "credits": 999999}).eq('user_id', ip).execute()

# --- ROUTES ---
@app.route('/')
def index():
    # Load HTML from templates folder
    return render_template('index.html', whatsapp=WHATSAPP, razorpay=RAZORPAY, price=PRICE, free=FREE_CREDS)

@app.route('/get_status')
def status():
    c, p = get_user(request.remote_addr)
    return jsonify({'credits': c, 'premium': p})

@app.route('/generate', methods=['POST'])
def generate():
    ip = request.remote_addr
    c, p = get_user(ip)
    if not p and c <= 0: return jsonify({'error': 'NO_CREDITS'})

    prompt = request.json.get('prompt')
    sys = "You are an AI Developer. Output ONLY raw HTML+Tailwind code using localStorage. No markdown."
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content([sys, f"Build: {prompt}"])
        
        # Clean Code
        code = res.text.replace('```html', '').replace('```', '').strip()
        if "|||CODE_START|||" in code: code = code.split("|||CODE_START|||")[1]
        
        if not p: deduct(ip)
        return jsonify({'html': code, 'explanation': "App generated successfully!"})
    except Exception as e: return jsonify({'error': str(e)})

@app.route('/verify', methods=['POST'])
def verify():
    try:
        img = base64.b64decode(request.json.get('img'))
        # Upload
        path = f"{request.remote_addr}_{datetime.datetime.now().timestamp()}.jpg"
        supabase.storage.from_("payment_proofs").upload(path, img, {"content-type": "image/jpeg"})
        
        # Verify
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(["Is this a valid payment receipt of approx 259? JSON {valid: bool, reason: str}", {"mime_type": "image/jpeg", "data": img}])
        data = json.loads(res.text.replace('```json','').replace('```',''))
        
        if data.get('valid'): upgrade(request.remote_addr)
        return jsonify({'success': data.get('valid'), 'reason': data.get('reason')})
    except: return jsonify({'success': False})

@app.route('/download', methods=['POST'])
def download():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', request.json.get('html', ''))
    mem.seek(0)
    return send_file(mem, mimetype='application/zip', as_attachment=True, download_name='project.zip')

if __name__ == '__main__':

    app.run(debug=True, port=5000)
