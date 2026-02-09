from flask import Flask, render_template_string, request, jsonify, send_file
import google.generativeai as genai
import requests  # <-- Isse hum Database se baat karenge (No Error)
import io, re, json, datetime, zipfile, base64

app = Flask(__name__)

# --- 🔑 CONFIGURATION ---
# 1. Gemini Key
GEMINI_KEY = "AIzaSyCLMcD33glXsaNHw9f094DblYilJI1BxeI"  # <-- Yahan Key Check kar lena
genai.configure(api_key=GEMINI_KEY)

# 2. Supabase Config (Apne purane wale)
DB_URL = "https://bhswajnmodtdzupedxnk.supabase.co"
DB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJoc3dham5tb2R0ZHp1cGVkeG5rIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA2MzMxNTksImV4cCI6MjA4NjIwOTE1OX0.gYUqTUyrxv36Ognyg7gyfJ991Vum_TqykC393o6i3zY"

# 3. Headers for Database
HEADERS = {
    "apikey": DB_KEY,
    "Authorization": f"Bearer {DB_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# 4. Business Info
WHATSAPP = "917704843966"
RAZORPAY = "https://rzp.io/rzp/KkySIH1U"
PRICE = 259
FREE_LIMIT = 20

# --- 🧠 DATABASE FUNCTIONS (Smart API Way) ---
def get_user(ip):
    try:
        # Check user
        url = f"{DB_URL}/rest/v1/user_credits?user_id=eq.{ip}&select=*"
        res = requests.get(url, headers=HEADERS)
        data = res.json()
        
        if not data:
            # Create new user
            requests.post(f"{DB_URL}/rest/v1/user_credits", headers=HEADERS, json={
                "user_id": ip, "credits": FREE_LIMIT, "is_premium": False
            })
            return FREE_LIMIT, False
        
        return data[0]['credits'], data[0]['is_premium']
    except Exception as e:
        print("DB Error:", e)
        return FREE_LIMIT, False # Fallback

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

# --- 🎨 UI TEMPLATE ---
HTML_UI = """
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AppifyGo4H - AI App Builder</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Outfit', sans-serif; background-color: #020617; color: white; overflow: hidden; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
        .glass { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(12px); border-right: 1px solid rgba(255,255,255,0.05); }
        .msg-user { background: #2563eb; color: white; border-radius: 12px 12px 2px 12px; margin-left: auto; }
        .msg-ai { background: #1e293b; border: 1px solid #334155; color: #e2e8f0; border-radius: 12px 12px 12px 2px; }
    </style>
</head>
<body class="flex h-screen w-full">

    <div class="w-72 glass flex flex-col z-20 h-full border-r border-slate-800">
        <div class="p-6 border-b border-slate-800">
            <h1 class="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                <i class="fa-solid fa-layer-group text-blue-500 mr-2"></i>AppifyGo4H
            </h1>
        </div>

        <div class="p-5">
            <div id="credit-card" class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
                <div class="flex justify-between items-center mb-2">
                    <span class="text-xs font-bold text-slate-400 uppercase">Credits Left</span>
                    <span id="credit-val" class="text-2xl font-bold text-white">--</span>
                </div>
                <div class="w-full bg-slate-800 h-1.5 rounded-full mb-4">
                    <div id="credit-bar" class="bg-blue-500 h-full w-0 transition-all duration-500"></div>
                </div>
                <button onclick="openModal()" class="w-full py-2 bg-gradient-to-r from-yellow-600 to-yellow-500 text-black text-xs font-bold rounded-lg hover:brightness-110 transition">
                    <i class="fa-solid fa-crown mr-1"></i> UPGRADE PLAN
                </button>
            </div>
        </div>

        <div class="mt-auto p-4 border-t border-slate-800">
            <a href="https://wa.me/{{ whatsapp }}" target="_blank" class="flex items-center justify-center gap-2 w-full py-3 bg-slate-800 hover:bg-slate-700 text-green-400 text-sm font-bold rounded-lg transition">
                <i class="fa-brands fa-whatsapp"></i> WhatsApp Support
            </a>
        </div>
    </div>

    <div class="flex-1 flex flex-col relative bg-black">
        <div class="h-14 border-b border-slate-800 bg-slate-950 flex items-center justify-between px-6">
            <span class="text-xs font-mono text-green-400">● SYSTEM ONLINE</span>
            <button onclick="downloadCode()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded text-xs text-white">
                <i class="fa-solid fa-download mr-1"></i> Download
            </button>
        </div>

        <div class="flex-1 flex overflow-hidden">
            <div class="w-[400px] flex flex-col border-r border-slate-800 bg-slate-900/30">
                <div id="chat-box" class="flex-1 overflow-y-auto p-4 space-y-4">
                    <div class="msg-ai p-4 text-sm">
                        <strong class="text-blue-400 block mb-1 text-xs">AI ASSISTANT</strong>
                        Welcome to AppifyGo4H! 🚀<br>
                        I can build secure apps using <b>localStorage</b>.<br>
                        Example: <i>"Build a Personal Finance Tracker"</i>
                    </div>
                </div>
                <div class="p-4 bg-black border-t border-slate-800">
                    <div class="relative">
                        <input id="prompt" type="text" placeholder="Describe your app..." 
                            class="w-full bg-slate-900 text-white border border-slate-800 rounded-lg py-3 pl-4 pr-12 focus:outline-none focus:border-blue-500 text-sm"
                            onkeypress="if(event.key === 'Enter') generate()">
                        <button onclick="generate()" class="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-500 text-white px-3 rounded text-sm">GO</button>
                    </div>
                </div>
            </div>

            <div class="flex-1 bg-[#050505] relative flex flex-col">
                <div class="h-8 bg-slate-900 flex items-center px-4 gap-2 border-b border-slate-800">
                    <div class="flex gap-1.5"><div class="w-2.5 h-2.5 rounded-full bg-red-500/30"></div><div class="w-2.5 h-2.5 rounded-full bg-yellow-500/30"></div><div class="w-2.5 h-2.5 rounded-full bg-green-500/30"></div></div>
                    <div class="ml-4 text-[10px] text-slate-500 font-mono">localhost:3000</div>
                </div>
                <iframe id="preview" class="w-full h-full border-none bg-white"></iframe>
                <div id="loader" class="hidden absolute inset-0 bg-black/80 flex flex-col items-center justify-center z-50">
                    <p class="text-blue-400 font-mono text-xs animate-pulse">GENERATING APP...</p>
                </div>
            </div>
        </div>
    </div>

    <div id="modal" class="hidden fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-4">
        <div class="bg-slate-900 border border-yellow-500/30 w-full max-w-sm rounded-xl p-6 relative">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-3 right-3 text-slate-500 hover:text-white">✕</button>
            <h2 class="text-xl font-bold text-white text-center mb-4">Get Unlimited Access</h2>
            <div class="bg-black p-3 rounded border border-slate-800 mb-4 flex justify-between">
                <span class="text-slate-400 text-sm">Plan Price</span>
                <span class="text-yellow-400 font-bold">₹{{ price }}/mo</span>
            </div>
            <a href="{{ razorpay }}" target="_blank" class="block w-full py-2.5 bg-yellow-600 hover:bg-yellow-500 text-black font-bold rounded-lg text-center text-sm mb-4">Step 1: Pay Now</a>
            <div class="border-t border-slate-800 pt-4">
                <p class="text-xs text-slate-500 mb-2">Step 2: Upload Payment Screenshot</p>
                <input type="file" id="proof" class="w-full text-xs text-slate-400 mb-3">
                <button onclick="verify()" class="w-full py-2 bg-green-600 hover:bg-green-500 text-white font-bold rounded-lg text-sm">Verify & Unlock</button>
                <p id="v-msg" class="text-center text-xs mt-2 h-4"></p>
            </div>
        </div>
    </div>

    <script>
        const FREE = {{ free }};
        let code = "";
        window.onload = updateStats;

        function updateStats() {
            fetch('/get_status').then(r=>r.json()).then(d=>{
                const disp = document.getElementById('credit-val');
                const bar = document.getElementById('credit-bar');
                if(d.premium){
                    disp.innerHTML = "<span class='text-yellow-400 text-sm'>UNLIMITED</span>";
                    bar.style.width = "100%";
                    bar.className = "h-full w-full bg-yellow-500";
                } else {
                    disp.innerText = d.credits;
                    bar.style.width = (d.credits/FREE*100) + "%";
                }
            });
        }

        async function generate() {
            const prompt = document.getElementById('prompt').value;
            if(!prompt) return;
            addMsg(prompt, 'user');
            document.getElementById('prompt').value = "";
            document.getElementById('loader').classList.remove('hidden');

            const res = await fetch('/generate', {
                method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({prompt})
            });
            const data = await res.json();
            document.getElementById('loader').classList.add('hidden');

            if(data.error === "NO_CREDITS") {
                openModal();
            } else if(data.html) {
                code = data.html;
                document.getElementById('preview').srcdoc = data.html;
                addMsg("App Generated Successfully!", 'ai');
                updateStats();
            } else {
                addMsg("Error: " + (data.error || "Unknown"), 'ai');
            }
        }

        async function verify() {
            const f = document.getElementById('proof').files[0];
            if(!f) return;
            document.getElementById('v-msg').innerText = "Verifying...";
            const reader = new FileReader();
            reader.readAsDataURL(f);
            reader.onload = async function() {
                try {
                    const res = await fetch('/verify', {
                        method:'POST', headers:{'Content-Type':'application/json'},
                        body:JSON.stringify({img: reader.result.split(',')[1]})
                    });
                    const d = await res.json();
                    if(d.success) {
                        document.getElementById('v-msg').innerText = "Verified! Refreshing...";
                        setTimeout(()=>location.reload(), 1500);
                    } else {
                        document.getElementById('v-msg').innerText = "Failed: " + (d.reason || "Invalid Proof");
                    }
                } catch(e) { document.getElementById('v-msg').innerText = "Server Error"; }
            }
        }

        function addMsg(txt, type) {
            const d = document.createElement('div');
            d.className = type === 'user' ? "msg-user p-3 text-sm max-w-[85%]" : "msg-ai p-3 text-sm max-w-[90%]";
            d.innerHTML = txt;
            document.getElementById('chat-box').appendChild(d);
            document.getElementById('chat-box').scrollTop = 9999;
        }

        function downloadCode() {
            if(!code) return alert("Generate first!");
            fetch('/download', {
                method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({html:code})
            }).then(r=>r.blob()).then(b=>{
                const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = "AppifyGo4H_Project.zip"; a.click();
            });
        }
        
        function openModal() { document.getElementById('modal').classList.remove('hidden'); }
    </script>
</body>
</html>
"""

# --- ROUTING ---
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
    
    if not p and c <= 0:
        return jsonify({'error': 'NO_CREDITS'})

    try:
        prompt = request.json.get('prompt')
        sys_prompt = "You are an AI Developer. Output ONLY raw HTML+Tailwind code using localStorage. No markdown."
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content([sys_prompt, f"Build: {prompt}"])
        code = res.text.replace('```html', '').replace('```', '').strip()
        
        if not p: deduct(ip)
        return jsonify({'html': code})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/verify', methods=['POST'])
def verify():
    try:
        img = base64.b64decode(request.json.get('img'))
        # 1. Upload Proof
        path = f"{request.remote_addr}_{datetime.datetime.now().timestamp()}.jpg"
        url = f"{DB_URL}/storage/v1/object/payment_proofs/{path}"
        requests.post(url, headers={"apikey": DB_KEY, "Authorization": f"Bearer {DB_KEY}", "Content-Type": "image/jpeg"}, data=img)
        
        # 2. Check with AI
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(["Is this a payment receipt of approx 259? JSON {valid: bool, reason: str}", {"mime_type": "image/jpeg", "data": img}])
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
    return send_file(mem, mimetype='application/zip', as_attachment=True, download_name='AppifyGo4H.zip')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
