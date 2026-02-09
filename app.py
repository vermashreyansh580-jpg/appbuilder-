from flask import Flask, render_template_string, request, jsonify, send_file
import google.generativeai as genai
import requests
import io, re, json, datetime, zipfile, base64

app = Flask(__name__)

# --- 🔑 CONFIGURATION ---
GEMINI_KEY = "AIzaSyCLMcD33glXsaNHw9f094DblYilJI1BxeI"
genai.configure(api_key=GEMINI_KEY)

# Supabase Config
DB_URL = "https://bhswajnmodtdzupedxnk.supabase.co"
DB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoc3dham5tb2R0ZHp1cGVkeG5rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2MzMxNTksImV4cCI6MjA4NjIwOTE1OX0.gYUqTUyrxv36Ognyg7gyfJ991Vum_TqykC393o6i3zY"

HEADERS = {
    "apikey": DB_KEY,
    "Authorization": f"Bearer {DB_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

WHATSAPP = "917704843966"
RAZORPAY = "https://rzp.io/rzp/KkySIH1U"
PRICE = 259
FREE_LIMIT = 20

# --- DATABASE LOGIC ---
def get_user(ip):
    try:
        url = f"{DB_URL}/rest/v1/user_credits?user_id=eq.{ip}&select=*"
        res = requests.get(url, headers=HEADERS)
        data = res.json()
        if not data:
            requests.post(f"{DB_URL}/rest/v1/user_credits", headers=HEADERS, json={
                "user_id": ip, "credits": FREE_LIMIT, "is_premium": False
            })
            return FREE_LIMIT, False
        return data[0]['credits'], data[0]['is_premium']
    except: return FREE_LIMIT, False

def deduct(ip):
    try:
        c, p = get_user(ip)
        if not p and c > 0:
            requests.patch(f"{DB_URL}/rest/v1/user_credits?user_id=eq.{ip}", headers=HEADERS, json={"credits": c-1})
    except: pass

def upgrade(ip):
    try:
        requests.patch(f"{DB_URL}/rest/v1/user_credits?user_id=eq.{ip}", headers=HEADERS, json={"is_premium": True, "credits": 99999})
    except: pass

# --- UI TEMPLATE ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AppifyGo4H</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { font-family: sans-serif; background-color: #020617; color: white; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; background: #334155; }
        .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border-right: 1px solid rgba(255,255,255,0.05); }
        .msg-user { background: #2563eb; color: white; border-radius: 12px 12px 2px 12px; margin-left: auto; }
        .msg-ai { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; border-radius: 12px 12px 12px 2px; }
    </style>
</head>
<body class="flex h-screen w-full">
    <div class="w-72 glass flex flex-col z-20 h-full border-r border-slate-800">
        <div class="p-6 border-b border-slate-800"><h1 class="text-xl font-bold text-blue-400">AppifyGo4H</h1></div>
        <div class="p-5">
            <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div class="flex justify-between mb-2"><span class="text-xs text-slate-400">CREDITS</span><span id="credit-val" class="font-bold">--</span></div>
                <button onclick="document.getElementById('modal').classList.remove('hidden')" class="w-full py-2 bg-yellow-500 text-black text-xs font-bold rounded">UPGRADE</button>
            </div>
        </div>
    </div>
    <div class="flex-1 flex flex-col relative bg-black">
        <div class="h-14 border-b border-slate-800 bg-slate-950 flex items-center justify-between px-6">
            <span class="text-xs text-green-400">● ONLINE</span>
            <button onclick="downloadCode()" class="px-3 py-1 bg-slate-800 text-xs text-white rounded">Download</button>
        </div>
        <div class="flex-1 flex overflow-hidden">
            <div class="w-[400px] flex flex-col border-r border-slate-800 bg-slate-900/30">
                <div id="chat-box" class="flex-1 overflow-y-auto p-4 space-y-4"></div>
                <div class="p-4 bg-black border-t border-slate-800">
                    <div class="flex gap-2">
                        <input id="prompt" type="text" placeholder="Describe app..." class="flex-1 bg-slate-900 border border-slate-800 rounded p-2 text-sm text-white">
                        <button onclick="generate()" class="bg-blue-600 px-4 rounded text-white">GO</button>
                    </div>
                </div>
            </div>
            <div class="flex-1 bg-[#050505] relative"><iframe id="preview" class="w-full h-full border-none bg-white"></iframe></div>
        </div>
    </div>
    
    <div id="modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4">
        <div class="bg-slate-900 border border-yellow-500/30 w-full max-w-sm rounded-xl p-6 relative">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-3 right-3 text-white">✕</button>
            <h2 class="text-xl font-bold text-white mb-4">Upgrade Plan</h2>
            <a href="{{ razorpay }}" target="_blank" class="block w-full py-2 bg-yellow-600 text-black font-bold rounded text-center mb-4">Pay ₹{{ price }}</a>
            <input type="file" id="proof" class="w-full text-xs text-slate-400 mb-2">
            <button onclick="verify()" class="w-full py-2 bg-green-600 text-white font-bold rounded">Verify</button>
            <p id="v-msg" class="text-center text-xs mt-2"></p>
        </div>
    </div>

    <script>
        const FREE = {{ free }};
        let code = "";
        window.onload = updateStats;
        function updateStats() {
            fetch('/get_status').then(r=>r.json()).then(d=>{
                document.getElementById('credit-val').innerText = d.premium ? "UNLIMITED" : d.credits;
            });
        }
        async function generate() {
            const p = document.getElementById('prompt').value;
            if(!p) return;
            addMsg(p, 'user');
            document.getElementById('prompt').value = "";
            const res = await fetch('/generate', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({prompt:p}) });
            const data = await res.json();
            if(data.error === "NO_CREDITS") document.getElementById('modal').classList.remove('hidden');
            else if(data.html) {
                code = data.html;
                document.getElementById('preview').srcdoc = data.html;
                addMsg("App Generated!", 'ai');
                updateStats();
            } else addMsg("Error: " + data.error, 'ai');
        }
        async function verify() {
            const f = document.getElementById('proof').files[0];
            if(!f) return;
            document.getElementById('v-msg').innerText = "Verifying...";
            const reader = new FileReader();
            reader.readAsDataURL(f);
            reader.onload = async function() {
                const res = await fetch('/verify', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({img: reader.result.split(',')[1]}) });
                const d = await res.json();
                if(d.success) { document.getElementById('v-msg').innerText = "Verified!"; setTimeout(()=>location.reload(), 1500); }
                else document.getElementById('v-msg').innerText = "Failed";
            }
        }
        function addMsg(txt, type) {
            const d = document.createElement('div');
            d.className = type==='user'?"msg-user p-3 text-sm":"msg-ai p-3 text-sm";
            d.innerText = txt;
            document.getElementById('chat-box').appendChild(d);
        }
        function downloadCode() {
            if(!code) return alert("Generate first!");
            fetch('/download', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({html:code}) })
            .then(r=>r.blob()).then(b=>{
                const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = "project.zip"; a.click();
            });
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_UI, whatsapp=WHATSAPP, razorpay=RAZORPAY, price=PRICE, free=FREE_LIMIT)

@app.route('/get_status')
def status():
    c, p = get_user(request.remote_addr)
    return jsonify({'credits': c, 'premium': p})

@app.route('/generate', methods=['POST'])
def generate():
    ip = request.remote_addr
    c, p = get_user(ip)
    if not p and c <= 0: return jsonify({'error': 'NO_CREDITS'})

    try:
        prompt = request.json.get('prompt')
        # FIX: Changed model to 'gemini-pro' (More stable)
        model = genai.GenerativeModel("gemini-pro") 
        sys = "You are an AI Developer. Output ONLY raw HTML+Tailwind code using localStorage. No markdown."
        res = model.generate_content([sys, f"Build: {prompt}"])
        code = res.text.replace('```html', '').replace('```', '').strip()
        
        if not p: deduct(ip)
        return jsonify({'html': code})
    except Exception as e: return jsonify({'error': str(e)})

@app.route('/verify', methods=['POST'])
def verify():
    try:
        img = base64.b64decode(request.json.get('img'))
        path = f"{request.remote_addr}_{datetime.datetime.now().timestamp()}.jpg"
        requests.post(f"{DB_URL}/storage/v1/object/payment_proofs/{path}", headers=HEADERS, data=img)
        
        # FIX: Changed model to 'gemini-pro-vision' for images (or 'gemini-1.5-flash' if lib updated)
        # But 'gemini-1.5-flash' is best. Let's try flash again, if not, use pro-vision.
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(["Is this a payment receipt? JSON {valid: bool}", {"mime_type": "image/jpeg", "data": img}])
        data = json.loads(res.text.replace('```json','').replace('```',''))
        
        if data.get('valid'): upgrade(request.remote_addr)
        return jsonify({'success': data.get('valid')})
    except: return jsonify({'success': False})

@app.route('/download', methods=['POST'])
def download():
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', request.json.get('html', ''))
    mem.seek(0)
    return send_file(mem, mimetype='application/zip', as_attachment=True, download_name='AppifyGo4H.zip')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
