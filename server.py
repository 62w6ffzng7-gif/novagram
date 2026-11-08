# language: Python, file: server.py, target: Python 3.10+
# *Мессенджер: ЛС, магазин, УЛУЧШЕНИЕ с визуальными эффектами (цвет, фон, узор)*
# *зависимости: fastapi, uvicorn, aiosqlite, websockets*

import json
import aiosqlite
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- КАТАЛОГ ПОДАРКОВ ---
GIFTS_CATALOG = {
    "heart": {"name": "Сердце", "icon": "❤️", "price_stars": 15},
    "bear": {"name": "Мишка", "icon": "🧸", "price_stars": 15},
    "rose": {"name": "Роза", "icon": "🌹", "price_stars": 25},
    "cake": {"name": "Торт", "icon": "🎂", "price_stars": 50},
    "rocket": {"name": "Ракета", "icon": "🚀", "price_stars": 75},
    "trophy": {"name": "Трофей", "icon": "🏆", "price_stars": 100},
    "crown": {"name": "Корона", "icon": "👑", "price_stars": 500},
}

# --- ХАРАКТЕРИСТИКИ ДЛЯ УЛУЧШЕНИЯ ---
# В реальном TG их сотни, мы берем самые популярные
MODELS = ["Circus Bear", "Zebra", "Panda", "Polar", "Bifrost", "Gold"]
PATTERNS = ["Diamond", "Fire", "Star", "Stripes", "Bishop", "Camo"]
BACKGROUNDS = ["Platinum", "Gold", "Neon", "Space", "Crimson", "Emerald"]

async def init_db():
    async with aiosqlite.connect("clone.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT, stars INTEGER DEFAULT 1000)""")
        await db.execute("""CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            user_id TEXT, 
            gift_id TEXT,
            is_upgraded INTEGER DEFAULT 0,
            model TEXT DEFAULT '',
            pattern TEXT DEFAULT '',
            background TEXT DEFAULT ''
        )""")
        await db.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id TEXT, receiver_id TEXT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        await db.commit()

@app.on_event("startup")
async def startup():
    await init_db()

# --- API ---
@app.get("/api/users")
async def get_users():
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT user_id, username FROM users") as cursor:
            return [{"id": u[0], "name": u[1]} for u in await cursor.fetchall()]

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT username, stars FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user: return {"error": "Not found"}
            async with db.execute("SELECT id, gift_id, is_upgraded, model, pattern, background FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                inventory = [{"inv_id": r[0], "gift_id": r[1], "name": GIFTS_CATALOG.get(r[1], {}).get("name"), "icon": GIFTS_CATALOG.get(r[1], {}).get("icon"), "is_upgraded": bool(r[2]), "model": r[3], "pattern": r[4], "background": r[5]} for r in rows if r[1] in GIFTS_CATALOG]
            return {"username": user[0], "stars": user[1], "inventory": inventory}

@app.get("/api/history/{user1}/{user2}")
async def get_history(user1: str, user2: str):
    async with aiosqlite.connect("clone.db") as db:
        query = """SELECT sender_id, text FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY id ASC"""
        async with db.execute(query, (user1, user2, user2, user1)) as cursor:
            return [{"sender": m[0], "text": m[1]} for m in await cursor.fetchall()]

@app.post("/api/buy")
async def buy_gift(request: Request):
    data = await request.json()
    gift = GIFTS_CATALOG.get(data["gift_id"])
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT stars FROM users WHERE user_id = ?", (data["user_id"],)) as cursor:
            user = await cursor.fetchone()
            if not user or user[0] < gift["price_stars"]: return {"success": False, "message": "Мало звезд!"}
            await db.execute("UPDATE users SET stars = stars - ? WHERE user_id = ?", (gift["price_stars"], data["user_id"]))
            await db.execute("INSERT INTO inventory (user_id, gift_id) VALUES (?, ?)", (data["user_id"], data["gift_id"]))
            await db.commit()
            return {"success": True}

@app.post("/api/upgrade")
async def upgrade_gift(request: Request):
    data = await request.json()
    user_id, inv_id, cost = data["user_id"], data["inv_id"], 25
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT stars FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user or user[0] < cost: return {"success": False, "message": "Мало звезд (нужно 25 ⭐)"}
        
        async with db.execute("SELECT is_upgraded FROM inventory WHERE id = ? AND user_id = ?", (inv_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row: return {"success": False, "message": "Подарок не найден"}
            if row[0] == 1: return {"success": False, "message": "Уже улучшен!"}

        await db.execute("UPDATE users SET stars = stars - ? WHERE user_id = ?", (cost, user_id))
        new_model, new_pattern, new_bg = random.choice(MODELS), random.choice(PATTERNS), random.choice(BACKGROUNDS)
        await db.execute("UPDATE inventory SET is_upgraded = 1, model = ?, pattern = ?, background = ? WHERE id = ?", (new_model, new_pattern, new_bg, inv_id))
        await db.commit()
        return {"success": True, "model": new_model, "pattern": new_pattern, "background": new_bg}

# --- WebSocket ---
class ConnectionManager:
    def __init__(self): self.active_connections: dict[str, WebSocket] = {}
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    def disconnect(self, user_id: str): 
        if user_id in self.active_connections: del self.active_connections[user_id]
    async def send_personal(self, message: str, receiver_id: str):
        if receiver_id in self.active_connections: await self.active_connections[receiver_id].send_text(message)
manager = ConnectionManager()

@app.websocket("/ws/{user_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, username: str):
    await manager.connect(user_id, websocket)
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if not await cursor.fetchone():
                await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
                await db.commit()
                await websocket.send_text(json.dumps({"system": "Добро пожаловать! Тебе начислено 1000 ⭐"}))
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            async with aiosqlite.connect("clone.db") as db:
                await db.execute("INSERT INTO messages (sender_id, receiver_id, text) VALUES (?, ?, ?)", (user_id, payload["receiver"], payload["text"]))
                await db.commit()
            await manager.send_personal(json.dumps({"sender": user_id, "text": payload["text"]}), payload["receiver"])
            await manager.send_personal(json.dumps({"sender": user_id, "text": payload["text"]}), user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.get("/manifest.json")
async def get_manifest(): return FileResponse("manifest.json")

@app.get("/")
async def get(): return HTMLResponse(html_client)

# --- HTML КЛИЕНТ ---
html_client = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>MyGram</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <link rel="manifest" href="/manifest.json">
    <style>
        * { box-sizing: border-box; }
        body { background: #0f0f11; color: #fff; font-family: -apple-system, sans-serif; margin: 0; padding: 0; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
        .page { display: none; flex: 1; overflow-y: auto; flex-direction: column; padding-bottom: 60px; }
        .page.active { display: flex; }
        
        .bottom-nav { position: absolute; bottom: 0; width: 100%; background: #1c1c1e; border-top: 1px solid #333; display: flex; height: 60px; z-index: 10; }
        .nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #888; font-size: 11px; cursor: pointer; }
        .nav-item.active { color: #0a84ff; }
        .nav-icon { font-size: 22px; margin-bottom: 4px; }
        .header { background: #1c1c1e; padding: 15px; font-weight: bold; font-size: 18px; border-bottom: 1px solid #333; position: sticky; top: 0; z-index: 5; display: flex; align-items: center; gap: 10px;}

        #chat-container { flex: 1; display: none; flex-direction: column; height: calc(100vh - 60px); }
        #chat { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
        .msg { max-width: 80%; padding: 10px 15px; border-radius: 15px; background: #2c2c2e; align-self: flex-start; word-wrap: break-word; font-size: 14px;}
        .my-msg { background: #0a84ff; align-self: flex-end; }
        .input-area { display: flex; padding: 10px; background: #1c1c1e; border-top: 1px solid #333; }
        input { flex: 1; padding: 12px; border-radius: 20px; border: none; background: #2c2c2e; color: white; outline: none; }
        button { background: #0a84ff; color: white; border: none; padding: 0 15px; border-radius: 20px; margin-left: 10px; font-weight: bold; }

        .contact-item { display: flex; align-items: center; padding: 15px; border-bottom: 1px solid #333; cursor: pointer; }
        .contact-avatar { width: 40px; height: 40px; background: #0a84ff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px; }

        .gift-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; padding: 10px; }
        .gift-card { background: #1c1c1e; border-radius: 10px; padding: 10px 5px; text-align: center; border: 1px solid #333; position: relative; }
        .gift-icon { font-size: 40px; margin-bottom: 5px; }
        .gift-name { font-size: 11px; color: #ccc; margin-bottom: 5px; height: 30px; display:flex; align-items:center; justify-content:center; text-align:center;}
        .gift-price { font-size: 12px; font-weight: bold; color: #0a84ff; background: #2c2c2e; padding: 4px 8px; border-radius: 10px; display: inline-block; cursor: pointer; }
        
        .profile-info { text-align: center; padding: 20px; }
        .balances { display: flex; justify-content: center; gap: 10px; margin-top: 15px; }
        .bal-box { background: #1c1c1e; padding: 10px 20px; border-radius: 15px; text-align: center; }
        .bal-val { font-size: 20px; font-weight: bold; color: #0a84ff; }
        .inv-section { padding: 15px; }
        .inv-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }
        
        /* КАРТОЧКА ПОДАРКА (АНИМАЦИИ) */
        .inv-item { background: #1c1c1e; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #333; position: relative; display: flex; flex-direction: column; align-items: center; overflow: hidden;}
        .inv-icon { font-size: 40px; margin-bottom: 5px; position: relative; z-index: 2;}
        .inv-name { font-size: 11px; margin-bottom: 5px; height: 30px; z-index: 2;}
        .inv-btn { font-size: 11px; background: #0a84ff; color: white; padding: 4px 8px; border-radius: 5px; cursor: pointer; border: none; width: 100%; z-index: 2;}
        .inv-btn:disabled { background: #444; cursor: not-allowed; }
        
        /* ЭФФЕКТЫ УЛУЧШЕНИЯ */
        /* Фоны (свечение) */
        .bg-Platinum { box-shadow: inset 0 0 20px rgba(255,255,255,0.4); background: linear-gradient(135deg, #1c1c1e, #444); }
        .bg-Gold { box-shadow: inset 0 0 20px rgba(255,215,0,0.5); background: linear-gradient(135deg, #1c1c1e, #665500); }
        .bg-Neon { box-shadow: inset 0 0 20px rgba(0,255,255,0.5); background: linear-gradient(135deg, #1c1c1e, #004444); }
        .bg-Space { box-shadow: inset 0 0 20px rgba(128,0,128,0.5); background: linear-gradient(135deg, #1c1c1e, #2a0033); }
        .bg-Crimson { box-shadow: inset 0 0 20px rgba(255,0,0,0.5); background: linear-gradient(135deg, #1c1c1e, #440000); }
        
        /* Модели (цвет иконки) */
        .model-Circus.Bear { filter: hue-rotate(180deg); } /* Синий */
        .model-Zebra { filter: grayscale(100%); }
        .model-Gold { filter: sepia(1) saturate(5) hue-rotate(10deg); }
        .model-Bifrost { animation: rainbow 3s infinite linear; }
        @keyframes rainbow { 0% { filter: hue-rotate(0deg); } 100% { filter: hue-rotate(360deg); } }
        
        /* Узоры (анимация поверх) */
        .pattern-Diamond::after { content: "💎"; position: absolute; top: 5px; right: 5px; font-size: 15px; opacity: 0.8; z-index: 3;}
        .pattern-Fire::after { content: "🔥"; position: absolute; top: 5px; right: 5px; font-size: 15px; opacity: 0.8; z-index: 3;}
        .pattern-Star::after { content: "⭐"; position: absolute; top: 5px; right: 5px; font-size: 15px; opacity: 0.8; z-index: 3; animation: pulse 1.5s infinite;}
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.3); } 100% { transform: scale(1); } }

        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 100; align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: #1c1c1e; padding: 20px; border-radius: 15px; width: 80%; max-width: 300px; text-align: center; border: 1px solid #333; }
    </style>
</head>
<body>

    <div id="page-chats" class="page active">
        <div class="header">Чаты</div>
        <div id="contacts-list" style="flex:1; overflow-y:auto;"></div>
    </div>

    <div id="chat-container">
        <div class="header"><span onclick="closeChat()" style="cursor:pointer; font-size:20px;">←</span> <span id="chat-with"></span></div>
        <div id="chat"></div>
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Сообщение...">
            <button onclick="sendMessage()">➤</button>
        </div>
    </div>

    <div id="page-shop" class="page">
        <div class="header">Магазин</div>
        <div class="gift-grid" id="shop-grid"></div>
    </div>

    <div id="page-profile" class="page">
        <div class="header">Профиль</div>
        <div class="profile-info">
            <h2 id="profile-name">Загрузка...</h2>
            <div class="balances">
                <div class="bal-box"><div class="bal-val" id="profile-stars">0</div><div style="font-size:12px;color:#888;">Звезды ⭐</div></div>
            </div>
        </div>
        <div class="inv-section">
            <h3>Мои подарки</h3>
            <div class="inv-grid" id="inventory"></div>
        </div>
    </div>

    <div id="upgrade-modal" class="modal">
        <div class="modal-content" id="modal-content"></div>
    </div>

    <div class="bottom-nav">
        <div class="nav-item active" onclick="switchPage('page-chats', this)"><div class="nav-icon">💬</div><div>Чаты</div></div>
        <div class="nav-item" onclick="switchPage('page-shop', this)"><div class="nav-icon">🛒</div><div>Магазин</div></div>
        <div class="nav-item" onclick="switchPage('page-profile', this)"><div class="nav-icon">👤</div><div>Профиль</div></div>
    </div>

    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        const userId = tg.initDataUnsafe?.user?.id || "test_123";
        const username = tg.initDataUnsafe?.user?.first_name || "Гость";
        
        let currentChatUserId = null;
        let ws;
        let userInventory = [];

        function switchPage(pageId, navElement) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            document.getElementById(pageId).classList.add('active');
            navElement.classList.add('active');
            document.getElementById('chat-container').style.display = 'none';
            
            if (pageId === 'page-profile') loadProfile();
            if (pageId === 'page-shop') renderShop();
            if (pageId === 'page-chats') loadUsers();
        }

        async function loadUsers() {
            const res = await fetch('/api/users');
            const users = await res.json();
            const list = document.getElementById('contacts-list');
            list.innerHTML = '';
            users.forEach(u => {
                if (u.id === userId) return;
                const div = document.createElement('div');
                div.className = 'contact-item';
                div.innerHTML = `<div class="contact-avatar">${u.name[0]}</div><div>${u.name}</div>`;
                div.onclick = () => openChat(u.id, u.name);
                list.appendChild(div);
            });
        }

        async function openChat(targetId, targetName) {
            currentChatUserId = targetId;
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById('chat-container').style.display = 'flex';
            document.getElementById('chat-with').innerText = targetName;
            document.getElementById('chat').innerHTML = '';
            
            const res = await fetch(`/api/history/${userId}/${targetId}`);
            const history = await res.json();
            history.forEach(m => {
                const div = document.createElement("div");
                div.className = "msg " + (m.sender === userId ? "my-msg" : "");
                div.innerText = m.text;
                document.getElementById('chat').appendChild(div);
            });
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
            connectWS();
        }

        function closeChat() {
            document.getElementById('chat-container').style.display = 'none';
            document.getElementById('page-chats').classList.add('active');
            currentChatUserId = null;
        }

        function connectWS() {
            if (ws && ws.readyState === WebSocket.OPEN) return;
            ws = new WebSocket("wss://" + window.location.host + "/ws/" + userId + "/" + username);
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.system) { tg.showAlert(data.system); return; }
                if (currentChatUserId === data.sender) {
                    const div = document.createElement("div");
                    div.className = "msg " + (data.sender === userId ? "my-msg" : "");
                    div.innerText = data.text;
                    document.getElementById('chat').appendChild(div);
                    document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
                }
            };
        }

        function sendMessage() {
            const input = document.getElementById("messageInput");
            if (input.value && currentChatUserId && ws) {
                ws.send(JSON.stringify({ receiver: currentChatUserId, text: input.value }));
                input.value = "";
            }
        }

        const GIFTS = {
            "heart": {"name": "Сердце", "icon": "❤️", "price": 15},
            "bear": {"name": "Мишка", "icon": "🧸", "price": 15},
            "rose": {"name": "Роза", "icon": "🌹", "price": 25},
            "cake": {"name": "Торт", "icon": "🎂", "price": 50},
            "rocket": {"name": "Ракета", "icon": "🚀", "price": 75},
            "trophy": {"name": "Трофей", "icon": "🏆", "price": 100},
            "crown": {"name": "Корона", "icon": "👑", "price": 500},
        };

        function renderShop() {
            const grid = document.getElementById("shop-grid");
            grid.innerHTML = "";
            for (const [id, gift] of Object.entries(GIFTS)) {
                const card = document.createElement("div");
                card.className = "gift-card";
                card.innerHTML = `
                    <div class="gift-icon">${gift.icon}</div>
                    <div class="gift-name">${gift.name}</div>
                    <div class="gift-price" onclick="buyItem('${id}')">${gift.price} ⭐</div>
                `;
                grid.appendChild(card);
            }
        }

        async function buyItem(giftId) {
            const res = await fetch('/api/buy', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ user_id: userId, gift_id: giftId })
            });
            const data = await res.json();
            if (data.success) tg.showAlert("Подарок куплен!");
            else tg.showAlert(data.message);
        }

        async function loadProfile() {
            const res = await fetch(`/api/profile/${userId}`);
            const data = await res.json();
            if (data.error) return;
            
            document.getElementById("profile-name").innerText = data.username;
            document.getElementById("profile-stars").innerText = data.stars;
            userInventory = data.inventory;
            
            const inv = document.getElementById("inventory");
            inv.innerHTML = "";
            if (userInventory.length === 0) inv.innerHTML = "<div style='color:#888;'>Пока пусто...</div>";
            
            userInventory.forEach(g => {
                const div = document.createElement('div');
                // Применяем классы визуальных эффектов
                let bgClass = g.is_upgraded ? `bg-${g.background.replace(' ', '')}` : '';
                div.className = `inv-item ${bgClass}`;
                
                let iconClass = g.is_upgraded ? `model-${g.model.replace(' ', '')} pattern-${g.pattern}` : '';
                let upgradeBtn = "";
                
                if (!g.is_upgraded) {
                    upgradeBtn = `<button class="inv-btn" onclick="openUpgradeModal(${g.inv_id})">Улучшить (25 ⭐)</button>`;
                } else {
                    upgradeBtn = `<div style="font-size:10px;color:#0a84ff;margin-top:5px;z-index:2;">NFT</div>`;
                }

                div.innerHTML = `
                    <div class="inv-icon ${iconClass}">${g.icon}</div>
                    <div class="inv-name">${g.name}</div>
                    ${upgradeBtn}
                `;
                inv.appendChild(div);
            });
        }

        function openUpgradeModal(invId) {
            const gift = userInventory.find(g => g.inv_id === invId);
            if (!gift) return;
            
            const modal = document.getElementById('upgrade-modal');
            const content = document.getElementById('modal-content');
            
            content.innerHTML = `
                <h2>Улучшение</h2>
                <div style="font-size:60px; margin:20px 0; text-align:center;">${gift.icon}</div>
                <p style="font-size:14px; color:#ccc; text-align:center;">Подарок станет уникальным, получит анимированный фон, узор и модель.</p>
                <button class="inv-btn" style="padding:15px; font-size:16px; margin-top:15px; background:#0a84ff; color:white;" onclick="doUpgrade(${invId})">Улучшить за 25 ⭐</button>
                <button class="inv-btn" style="background:#333; padding:10px; margin-top:10px; color:white;" onclick="closeModal()">Отмена</button>
            `;
            modal.classList.add('active');
        }

        function closeModal() {
            document.getElementById('upgrade-modal').classList.remove('active');
        }

        async function doUpgrade(invId) {
            closeModal();
            const res = await fetch('/api/upgrade', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ user_id: userId, inv_id: invId })
            });
            const data = await res.json();
            
            if (data.success) {
                tg.showAlert(`Успешно! Подарок улучшен.\nМодель: ${data.model}\nУзор: ${data.pattern}\nФон: ${data.background}`);
                loadProfile();
            } else {
                tg.showAlert(data.message);
            }
        }

        connectWS();
        loadUsers();
        renderShop();
    </script>
</body>
</html>
