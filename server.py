# language: Python, file: server.py, target: Python 3.10+
# *NovaGram: ЛС, магазин (все подарки со скринов), улучшения, админка*
# *зависимости: fastapi, uvicorn, aiosqlite, websockets*

import json
import aiosqlite
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- СЕКРЕТНЫЙ КОД ---
SECRET_ADMIN_KEY = "rtuphkvz1028" 

# --- ПОЛНЫЙ КАТАЛОГ ПОДАРКОВ (Со скринов) ---
GIFTS_CATALOG = {
    # Обычные (дешевые)
    "heart": {"name": "Сердце", "icon": "❤️", "price_stars": 15},
    "bear": {"name": "Мишка", "icon": "🧸", "price_stars": 15},
    "giftbox_15": {"name": "Коробка", "icon": "🎁", "price_stars": 15},
    "rose": {"name": "Роза", "icon": "🌹", "price_stars": 15},
    "cake_25": {"name": "Торт", "icon": "🎂", "price_stars": 25},
    "bouquet_50": {"name": "Букет", "icon": "💐", "price_stars": 50},
    "rocket_75": {"name": "Ракета", "icon": "🚀", "price_stars": 75},
    "trophy_100": {"name": "Трофей", "icon": "🏆", "price_stars": 100},
    "ring_140": {"name": "Кольцо", "icon": "💍", "price_stars": 140},
    "diamond_100": {"name": "Бриллиант", "icon": "💎", "price_stars": 100},
    "champagne_200": {"name": "Шампанское", "icon": "🍾", "price_stars": 200},
    "torch_150": {"name": "Факел", "icon": "🕯️", "price_stars": 150},
    "statue_250": {"name": "Статуя Свободы", "icon": "🗽", "price_stars": 250},
    "icecream_250": {"name": "Мороженое", "icon": "🍦", "price_stars": 250},
    "dino_200": {"name": "Динозаврик", "icon": "🦖", "price_stars": 200},
    "noodles_200": {"name": "Лапша", "icon": "🍜", "price_stars": 200},
    "swan_300": {"name": "Лебедь", "icon": "🦢", "price_stars": 300},
    "popsicle_100": {"name": "Эскимо", "icon": "🍦", "price_stars": 100},
    "lollipop_145": {"name": "Леденец", "icon": "🍭", "price_stars": 145},
    "backpack_500": {"name": "Рюкзак", "icon": "🎒", "price_stars": 500},
    "chips_200": {"name": "Чипсы", "icon": "🍟", "price_stars": 200},
    "poop_100": {"name": "Какашка", "icon": "💩", "price_stars": 100},
    "basket_200": {"name": "Корзинка", "icon": "🧺", "price_stars": 200},
    "clover_100": {"name": "Клевер", "icon": "🍀", "price_stars": 100},
    "snowman_250": {"name": "Снеговик", "icon": "⛄", "price_stars": 250},
    "santa_100": {"name": "Санта", "icon": "🎅", "price_stars": 100},
    "candy_100": {"name": "Конфета", "icon": "🍬", "price_stars": 100},
    "mosque_100": {"name": "Мечеть", "icon": "🕌", "price_stars": 100},
    "cookie_150": {"name": "Печенье", "icon": "🍪", "price_stars": 150},
    "cherry_cake_100": {"name": "Торт с вишней", "icon": "🍰", "price_stars": 100},
    "socks_100": {"name": "Носки", "icon": "🧦", "price_stars": 100},
    "snake_250": {"name": "Змея", "icon": "🐍", "price_stars": 250},
    "sparkler_150": {"name": "Бенгальский огонь", "icon": "🎇", "price_stars": 150},
    "party_popper_200": {"name": "Хлопушка", "icon": "🎉", "price_stars": 200},
    "jester_150": {"name": "Колпак шута", "icon": "🃏", "price_stars": 150},
    "money_bouquet_150": {"name": "Букет из денег", "icon": "💵", "price_stars": 150},
    "book_200": {"name": "Книга", "icon": "📕", "price_stars": 200},
    "easter_basket_150": {"name": "Пасхальная корзина", "icon": "🐰", "price_stars": 150},
    "medal_300": {"name": "Медаль", "icon": "🏅", "price_stars": 300},
    "cake_500": {"name": "Праздничный торт", "icon": "🎂", "price_stars": 500},
    "lightsaber_200": {"name": "Световой меч", "icon": "⚔️", "price_stars": 200},
    "keycap_200": {"name": "Кейкап", "icon": "⌨️", "price_stars": 200},
    "ufo_200": {"name": "НЛО", "icon": "🛸", "price_stars": 200},
    "moon_100": {"name": "Месяц", "icon": "🌙", "price_stars": 100},
    "fireworks_2500": {"name": "Фейерверк", "icon": "🎆", "price_stars": 2500},
    "rose_bouquet_250": {"name": "Букет роз", "icon": "💐", "price_stars": 250},
    "gingerbread_150": {"name": "Пряничный человечек", "icon": "🍪", "price_stars": 150},
    "jar_200": {"name": "Банка", "icon": "🫙", "price_stars": 200},
    "calendar_150": {"name": "Календарь", "icon": "📅", "price_stars": 150},
    "ufc_250": {"name": "UFC", "icon": "🥊", "price_stars": 250},
    "monkey_200": {"name": "Обезьянка", "icon": "🐒", "price_stars": 200},
    "cocoa_250": {"name": "Какао", "icon": "☕", "price_stars": 250},
    "love_you_300": {"name": "Love You", "icon": "❤️", "price_stars": 300},
    "mushroom_150": {"name": "Гриб", "icon": "🍄", "price_stars": 150},
    "dumplings_250": {"name": "Пельмени", "icon": "🥟", "price_stars": 250},
    "clock_200": {"name": "Часы", "icon": "⏰", "price_stars": 200},
    "lemonade_150": {"name": "Лимонад", "icon": "🍹", "price_stars": 150},
    "eye_150": {"name": "Глаз", "icon": "👁️", "price_stars": 150},
    "lollipop_250": {"name": "Леденец", "icon": "🍭", "price_stars": 250},
    "pot_of_gold_250": {"name": "Горшок золота", "icon": "🪙", "price_stars": 250},
    "sakura_175": {"name": "Сакура", "icon": "🌸", "price_stars": 175},
    "easter_egg_200": {"name": "Пасхальное яйцо", "icon": "🥚", "price_stars": 200},
    "wreath_250": {"name": "Венок", "icon": "🎄", "price_stars": 250},
    "notebook_250": {"name": "Блокнот", "icon": "📓", "price_stars": 250},
    "2025_200": {"name": "2025", "icon": "🎆", "price_stars": 200},
    "giftbox_300": {"name": "Подарок", "icon": "🎁", "price_stars": 300},
    "cupcake_200": {"name": "Капкейк", "icon": "🧁", "price_stars": 200},
    "bow_300": {"name": "Бант", "icon": "🎀", "price_stars": 300},
    "witch_hat_150": {"name": "Шляпа ведьмы", "icon": "🧙‍♀️", "price_stars": 150},
    "cauldron_150": {"name": "Котел", "icon": "🍲", "price_stars": 150},
    "heart_box_400": {"name": "Сердце-коробка", "icon": "💝", "price_stars": 400},
    "sweets_200": {"name": "Сладости", "icon": "🍬", "price_stars": 200},
    "star_200": {"name": "Звезда", "icon": "⭐", "price_stars": 200},
    "santa_hat_200": {"name": "Шапка Санты", "icon": "🎅", "price_stars": 200},
    "potion_200": {"name": "Зелье", "icon": "🧪", "price_stars": 200},
    "candle_250": {"name": "Свеча", "icon": "🕯️", "price_stars": 250},
    "shoes_300": {"name": "Туфельки", "icon": "👠", "price_stars": 300},
    "coconut_2900": {"name": "Кокос", "icon": "🥥", "price_stars": 2900},
    "skull_150": {"name": "Череп", "icon": "💀", "price_stars": 150},
    "spider_heart_150": {"name": "Сердце паука", "icon": "🕷️", "price_stars": 150},
    "snow_globe_150": {"name": "Снежный шар", "icon": "🔮", "price_stars": 150},
    "top_hat_200": {"name": "Цилиндр", "icon": "🎩", "price_stars": 200},
    "golden_heart_500": {"name": "Золотое сердце", "icon": "💛", "price_stars": 500},
    "rose_glass_250": {"name": "Роза под стеклом", "icon": "🌹", "price_stars": 250},
    "bells_250": {"name": "Колокольчики", "icon": "🔔", "price_stars": 250},
    "ring_box_100": {"name": "Кольцо в коробке", "icon": "💍", "price_stars": 100},
    "bell_100": {"name": "Колокольчик", "icon": "🔔", "price_stars": 100},
    "ring_200": {"name": "Кольцо", "icon": "💍", "price_stars": 200},
    "cigar_100": {"name": "Сигара", "icon": "🚬", "price_stars": 100},
    "skull_flower_250": {"name": "Цветок-череп", "icon": "💀", "price_stars": 250},
    "candy_cane_100": {"name": "Карамельная трость", "icon": "🍬", "price_stars": 100},
    "broom_150": {"name": "Метла", "icon": "🧹", "price_stars": 150},
    "dove_5000": {"name": "Голубь", "icon": "🕊️", "price_stars": 5000},
    "box_star_200": {"name": "Коробка со звездой", "icon": "📦", "price_stars": 200},
    "car_5000": {"name": "Машина", "icon": "🚗", "price_stars": 5000},
    "bear_150": {"name": "Мишка", "icon": "🧸", "price_stars": 150},
    "voodoo_150": {"name": "Вуду", "icon": "🧸", "price_stars": 150},
    "pumpkin_250": {"name": "Тыква", "icon": "🎃", "price_stars": 250},
    "helmet_2500": {"name": "Шлем", "icon": "🏍️", "price_stars": 2500},
    "ring_150": {"name": "Кольцо", "icon": "💍", "price_stars": 150},
    "watch_100": {"name": "Часы", "icon": "⌚", "price_stars": 100},
    "pacifier_5000": {"name": "Соска", "icon": "🍼", "price_stars": 5000},
    "victory_10000": {"name": "Виктория", "icon": "✌️", "price_stars": 10000},
    "ring_500": {"name": "Кольцо", "icon": "💍", "price_stars": 500},
    "ring_10000": {"name": "Кольцо", "icon": "💍", "price_stars": 10000},
    "frog_150": {"name": "Жаба", "icon": "🐸", "price_stars": 150},
    "lips_200": {"name": "Губы", "icon": "👄", "price_stars": 200},
    "skull_purple_250": {"name": "Череп", "icon": "💀", "price_stars": 250},
    "ring_5000": {"name": "Кольцо", "icon": "💍", "price_stars": 5000},
    "peach_200": {"name": "Персик", "icon": "🍑", "price_stars": 200},
    "crystal_500": {"name": "Кристалл", "icon": "💎", "price_stars": 500},
    "ice_100": {"name": "Лед", "icon": "🧊", "price_stars": 100},
    "perfume_500": {"name": "Духи", "icon": "🧴", "price_stars": 500},
    "lamp_350": {"name": "Лампа", "icon": "🪔", "price_stars": 350},
    "cat_250": {"name": "Кот", "icon": "🐱", "price_stars": 250},
    "potion_green_200": {"name": "Зелье", "icon": "🧪", "price_stars": 200},
    "bag_2500": {"name": "Сумка", "icon": "👜", "price_stars": 2500},
    "oscar_500": {"name": "Оскар", "icon": "🏆", "price_stars": 500},
    "chocolate_5000": {"name": "Шоколад", "icon": "🍫", "price_stars": 5000},
    "helmet_5000": {"name": "Шлем", "icon": "🪖", "price_stars": 5000},
    "cap_200": {"name": "Кепка", "icon": "🧢", "price_stars": 200},
    "swan_gold_10000": {"name": "Золотой лебедь", "icon": "🦢", "price_stars": 10000},
    "heart_150": {"name": "Сердце", "icon": "💖", "price_stars": 150},
    "doll_41000": {"name": "Кукла", "icon": "🪆", "price_stars": 41000},
    "shirt_10000": {"name": "Футболка", "icon": "👕", "price_stars": 10000},
    "sneakers_10000": {"name": "Кроссовки", "icon": "👟", "price_stars": 10000},
    "case_5000": {"name": "Чемодан", "icon": "💼", "price_stars": 5000},
    "castle_500": {"name": "Замок", "icon": "🏰", "price_stars": 500},
    "cocktail_150": {"name": "Коктейль", "icon": "🍹", "price_stars": 150},
    "icecream_150": {"name": "Мороженое", "icon": "🍨", "price_stars": 150},
    "star_red_100": {"name": "Звезда", "icon": "🌟", "price_stars": 100},
    "stamp_150": {"name": "Марка", "icon": "🖼️", "price_stars": 150},
    "1may_100": {"name": "1 Мая", "icon": "1️⃣", "price_stars": 100},
    "cake_150": {"name": "Торт", "icon": "🎂", "price_stars": 150},
    "8march_200": {"name": "8 Марта", "icon": "8️⃣", "price_stars": 200},
}

MODELS = ["Circus Bear", "Zebra", "Panda", "Polar", "Bifrost", "Gold"]
PATTERNS = ["Diamond", "Fire", "Star", "Stripes", "Bishop", "Camo"]
BACKGROUNDS = ["Platinum", "Gold", "Neon", "Space", "Crimson", "Emerald"]

async def init_db():
    async with aiosqlite.connect("clone.db") as db:
        await db.execute("""CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT, stars INTEGER DEFAULT 1000, anon_number TEXT DEFAULT '')""")
        await db.execute("""CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, gift_id TEXT, is_upgraded INTEGER DEFAULT 0, model TEXT DEFAULT '', pattern TEXT DEFAULT '', background TEXT DEFAULT '')""")
        await db.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id TEXT, receiver_id TEXT, text TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        await db.commit()

@app.on_event("startup")
async def startup():
    await init_db()

# --- API ---
@app.get("/api/users")
async def get_users():
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT user_id, username, anon_number FROM users") as cursor:
            return [{"id": u[0], "name": u[1], "anon": u[2]} for u in await cursor.fetchall()]

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    async with aiosqlite.connect("clone.db") as db:
        async with db.execute("SELECT username, stars, anon_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user: return {"error": "Not found"}
            async with db.execute("SELECT id, gift_id, is_upgraded, model, pattern, background FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
                rows = await cursor.fetchall()
                inventory = [{"inv_id": r[0], "gift_id": r[1], "name": GIFTS_CATALOG.get(r[1], {}).get("name"), "icon": GIFTS_CATALOG.get(r[1], {}).get("icon"), "is_upgraded": bool(r[2]), "model": r[3], "pattern": r[4], "background": r[5]} for r in rows if r[1] in GIFTS_CATALOG]
            return {"username": user[0], "stars": user[1], "anon_number": user[2], "inventory": inventory}

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
            if not user or user[0] < cost: return {"success": False, "message": "Мало звезд!"}
        async with db.execute("SELECT is_upgraded FROM inventory WHERE id = ? AND user_id = ?", (inv_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if not row or row[0] == 1: return {"success": False, "message": "Уже улучшен!"}
        await db.execute("UPDATE users SET stars = stars - ? WHERE user_id = ?", (cost, user_id))
        new_model, new_pattern, new_bg = random.choice(MODELS), random.choice(PATTERNS), random.choice(BACKGROUNDS)
        await db.execute("UPDATE inventory SET is_upgraded = 1, model = ?, pattern = ?, background = ? WHERE id = ?", (new_model, new_pattern, new_bg, inv_id))
        await db.commit()
        return {"success": True, "model": new_model, "pattern": new_pattern, "background": new_bg}

@app.post("/api/admin/give_stars")
async def admin_give_stars(request: Request):
    data = await request.json()
    if data.get("secret") != SECRET_ADMIN_KEY: return {"success": False, "message": "Неверный код!"}
    async with aiosqlite.connect("clone.db") as db:
        await db.execute("UPDATE users SET stars = stars + ? WHERE user_id = ?", (data["amount"], data["target_id"]))
        await db.commit()
        return {"success": True}

@app.post("/api/admin/create_anon")
async def admin_create_anon(request: Request):
    data = await request.json()
    if data.get("secret") != SECRET_ADMIN_KEY: return {"success": False, "message": "Неверный код!"}
    new_num = "+888 8888 8888" if data.get("is_self") else f"+888 {random.randint(1000, 9999)}"
    async with aiosqlite.connect("clone.db") as db:
        await db.execute("UPDATE users SET anon_number = ? WHERE user_id = ?", (new_num, data["target_id"]))
        await db.commit()
        return {"success": True, "number": new_num}

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
                new_anon = f"+888 {random.randint(1000, 9999)}"
                await db.execute("INSERT INTO users (user_id, username, anon_number) VALUES (?, ?, ?)", (user_id, username, new_anon))
                await db.commit()
                await websocket.send_text(json.dumps({"system": f"Добро пожаловать! Тебе начислено 1000 ⭐ и выдан номер {new_anon}"}))
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
    <title>NovaGram</title>
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
        .inv-item { background: #1c1c1e; border-radius: 10px; padding: 10px; text-align: center; border: 1px solid #333; position: relative; display: flex; flex-direction: column; align-items: center; overflow: hidden;}
        .inv-icon { font-size: 40px; margin-bottom: 5px; position: relative; z-index: 2;}
        .inv-name { font-size: 11px; margin-bottom: 5px; height: 30px; z-index: 2;}
        .inv-btn { font-size: 11px; background: #0a84ff; color: white; padding: 4px 8px; border-radius: 5px; cursor: pointer; border: none; width: 100%; z-index: 2;}
        .inv-btn:disabled { background: #444; cursor: not-allowed; }
        .bg-Platinum { box-shadow: inset 0 0 20px rgba(255,255,255,0.4); background: linear-gradient(135deg, #1c1c1e, #444); }
        .bg-Gold { box-shadow: inset 0 0 20px rgba(255,215,0,0.5); background: linear-gradient(135deg, #1c1c1e, #665500); }
        .bg-Neon { box-shadow: inset 0 0 20px rgba(0,255,255,0.5); background: linear-gradient(135deg, #1c1c1e, #004444); }
        .bg-Space { box-shadow: inset 0 0 20px rgba(128,0,128,0.5); background: linear-gradient(135deg, #1c1c1e, #2a0033); }
        .bg-Crimson { box-shadow: inset 0 0 20px rgba(255,0,0,0.5); background: linear-gradient(135deg, #1c1c1e, #440000); }
        .model-Circus { filter: hue-rotate(180deg); }
        .model-Zebra { filter: grayscale(100%); }
        .model-Gold { filter: sepia(1) saturate(5) hue-rotate(10deg); }
        .model-Bifrost { animation: rainbow 3s infinite linear; }
        @keyframes rainbow { 0% { filter: hue-rotate(0deg); } 100% { filter: hue-rotate(360deg); } }
        .pattern-Diamond::after { content: "💎"; position: absolute; top: 5px; right: 5px; font-size: 15px; z-index: 3;}
        .pattern-Fire::after { content: "🔥"; position: absolute; top: 5px; right: 5px; font-size: 15px; z-index: 3;}
        .pattern-Star::after { content: "⭐"; position: absolute; top: 5px; right: 5px; font-size: 15px; z-index: 3; animation: pulse 1.5s infinite;}
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
            <div class="avatar" id="profile-avatar" onclick="secretClick()" style="width: 80px; height: 80px; background: #333; border-radius: 50%; margin: 0 auto 10px; display: flex; align-items: center; justify-content: center; font-size: 40px; cursor: pointer;">👤</div>
            <h2 id="profile-name">Загрузка...</h2>
            <div id="anon-num" style="color:#888; font-size:14px; margin-bottom:10px;"></div>
            <div class="balances">
                <div class="bal-box"><div class="bal-val" id="profile-stars">0</div><div style="font-size:12px;color:#888;">Звезды ⭐</div></div>
            </div>
        </div>
        <div class="inv-section">
            <h3>Мои подарки</h3>
            <div class="inv-grid" id="inventory"></div>
        </div>
    </div>
    <div id="page-admin" class="page">
        <div class="header">Админ-панель</div>
        <div style="padding: 15px; display: flex; flex-direction: column; gap: 15px;">
            <div style="background:#1c1c1e; padding:15px; border-radius:10px;">
                <h3>Выдать звезды</h3>
                <input type="text" id="admin-target" placeholder="ID пользователя" style="width:100%; margin-bottom:10px; padding:10px; border-radius:5px; border:none; background:#2c2c2e; color:white;">
                <input type="number" id="admin-amount" placeholder="Сумма" style="width:100%; margin-bottom:10px; padding:10px; border-radius:5px; border:none; background:#2c2c2e; color:white;">
                <button onclick="adminGiveStars()" style="width:100%; padding:10px; background:#0a84ff; color:white; border:none; border-radius:5px;">Выдать</button>
            </div>
            <div style="background:#1c1c1e; padding:15px; border-radius:10px; border: 1px solid #ff3366;">
                <h3>Выдать себе 8888</h3>
                <button onclick="adminGetMyAnon()" style="width:100%; padding:10px; background:#ff3366; color:white; border:none; border-radius:5px;">Получить мой номер</button>
            </div>
        </div>
    </div>
    <div id="upgrade-modal" class="modal">
        <div class="modal-content" id="modal-content"></div>
    </div>
    <div class="bottom-nav">
        <div class="nav-item active" onclick="switchPage('page-chats', this)"><div class="nav-icon">💬</div><div>Чаты</div></div>
        <div class="nav-item" onclick="switchPage('page-shop', this)"><div class="nav-icon">🛒</div><div>Магазин</div></div>
        <div class="nav-item" onclick="switchPage('page-profile', this)"><div class="nav-icon">👤</div><div>Профиль</div></div>
        <div id="admin-nav-btn" class="nav-item" style="display:none;" onclick="switchPage('page-admin', this)"><div class="nav-icon">⚙️</div><div>Админ</div></div>
    </div>
    <script>
        const tg = window.Telegram.WebApp;
        tg.expand();
        const userId = tg.initDataUnsafe?.user?.id || "test_123";
        const username = tg.initDataUnsafe?.user?.first_name || "Гость";
        let currentChatUserId = null;
        let ws;
        let userInventory = [];
        let clickCount = 0;
        let clickTimer;
        function secretClick() {
            clickCount++;
            clearTimeout(clickTimer);
            clickTimer = setTimeout(() => { clickCount = 0; }, 2000);
            if (clickCount >= 5) {
                let pass = prompt("Введите секретный код:");
                if (pass === "rtuphkvz1028") {
                    document.getElementById('admin-nav-btn').style.display = 'flex';
                    tg.showAlert("Админ-панель разблокирована!");
                    switchPage('page-admin', document.getElementById('admin-nav-btn'));
                } else { tg.showAlert("Неверный код!"); }
                clickCount = 0;
            }
        }
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
                const displayName = u.anon ? `${u.name} (${u.anon})` : u.name;
                div.innerHTML = `<div class="contact-avatar">${u.name[0]}</div><div>${displayName}</div>`;
                div.onclick = () => openChat(u.id, displayName);
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
        const GIFTS = {"heart": {"name": "Сердце", "icon": "❤️", "price": 15}, "bear": {"name": "Мишка", "icon": "🧸", "price": 15}, "giftbox_15": {"name": "Коробка", "icon": "🎁", "price": 15}, "rose": {"name": "Роза", "icon": "🌹", "price": 15}, "cake_25": {"name": "Торт", "icon": "🎂", "price": 25}, "bouquet_50": {"name": "Букет", "icon": "💐", "price": 50}, "rocket_75": {"name": "Ракета", "icon": "🚀", "price": 75}, "trophy_100": {"name": "Трофей", "icon": "🏆", "price": 100}, "ring_140": {"name": "Кольцо", "icon": "💍", "price": 140}, "diamond_100": {"name": "Бриллиант", "icon": "💎", "price": 100}, "champagne_200": {"name": "Шампанское", "icon": "🍾", "price": 200}, "torch_150": {"name": "Факел", "icon": "🕯️", "price": 150}, "statue_250": {"name": "Статуя Свободы", "icon": "🗽", "price": 250}, "icecream_250": {"name": "Мороженое", "icon": "🍦", "price": 250}, "dino_200": {"name": "Динозаврик", "icon": "🦖", "price": 200}, "noodles_200": {"name": "Лапша", "icon": "🍜", "price": 200}, "swan_300": {"name": "Лебедь", "icon": "🦢", "price": 300}, "popsicle_100": {"name": "Эскимо", "icon": "🍦", "price": 100}, "lollipop_145": {"name": "Леденец", "icon": "🍭", "price": 145}, "backpack_500": {"name": "Рюкзак", "icon": "🎒", "price": 500}, "chips_200": {"name": "Чипсы", "icon": "🍟", "price": 200}, "poop_100": {"name": "Какашка", "icon": "💩", "price": 100}, "basket_200": {"name": "Корзинка", "icon": "🧺", "price": 200}, "clover_100": {"name": "Клевер", "icon": "🍀", "price": 100}, "snowman_250": {"name": "Снеговик", "icon": "⛄", "price": 250}, "santa_100": {"name": "Санта", "icon": "🎅", "price": 100}, "candy_100": {"name": "Конфета", "icon": "🍬", "price": 100}, "mosque_100": {"name": "Мечеть", "icon": "🕌", "price": 100}, "cookie_150": {"name": "Печенье", "icon": "🍪", "price": 150}, "cherry_cake_100": {"name": "Торт с вишней", "icon": "🍰", "price": 100}, "socks_100": {"name": "Носки", "icon": "🧦", "price": 100}, "snake_250": {"name": "Змея", "icon": "🐍", "price": 250}, "sparkler_150": {"name": "Бенгальский огонь", "icon": "🎇", "price": 150}, "party_popper_200": {"name": "Хлопушка", "icon": "🎉", "price": 200}, "jester_150": {"name": "Колпак шута", "icon": "🃏", "price": 150}, "money_bouquet_150": {"name": "Букет из денег", "icon": "💵", "price": 150}, "book_200": {"name": "Книга", "icon": "📕", "price": 200}, "easter_basket_150": {"name": "Пасхальная корзина", "icon": "🐰", "price": 150}, "medal_300": {"name": "Медаль", "icon": "🏅", "price": 300}, "cake_500": {"name": "Праздничный торт", "icon": "🎂", "price": 500}, "lightsaber_200": {"name": "Световой меч", "icon": "⚔️", "price": 200}, "keycap_200": {"name": "Кейкап", "icon": "⌨️", "price": 200}, "ufo_200": {"name": "НЛО", "icon": "🛸", "price": 200}, "moon_100": {"name": "Месяц", "icon": "🌙", "price": 100}, "fireworks_2500": {"name": "Фейерверк", "icon": "🎆", "price": 2500}, "rose_bouquet_250": {"name": "Букет роз", "icon": "💐", "price": 250}, "gingerbread_150": {"name": "Пряничный человечек", "icon": "🍪", "price": 150}, "jar_200": {"name": "Банка", "icon": "🫙", "price": 200}, "calendar_150": {"name": "Календарь", "icon": "📅", "price": 150}, "ufc_250": {"name": "UFC", "icon": "🥊", "price": 250}, "monkey_200": {"name": "Обезьянка", "icon": "🐒", "price": 200}, "cocoa_250": {"name": "Какао", "icon": "☕", "price": 250}, "love_you_300": {"name": "Love You", "icon": "❤️", "price": 300}, "mushroom_150": {"name": "Гриб", "icon": "🍄", "price": 150}, "dumplings_250": {"name": "Пельмени", "icon": "🥟", "price": 250}, "clock_200": {"name": "Часы", "icon": "⏰", "price": 200}, "lemonade_150": {"name": "Лимонад", "icon": "🍹", "price": 150}, "eye_150": {"name": "Глаз", "icon": "👁️", "price": 150}, "lollipop_250": {"name": "Леденец", "icon": "🍭", "price": 250}, "pot_of_gold_250": {"name": "Горшок золота", "icon": "🪙", "price": 250}, "sakura_175": {"name": "Сакура", "icon": "🌸", "price": 175}, "easter_egg_200": {"name": "Пасхальное яйцо", "icon": "🥚", "price": 200}, "wreath_250": {"name": "Венок", "icon": "🎄", "price": 250}, "notebook_250": {"name": "Блокнот", "icon": "📓", "price": 250}, "2025_200": {"name": "2025", "icon": "🎆", "price": 200}, "giftbox_300": {"name": "Подарок", "icon": "🎁", "price": 300}, "cupcake_200": {"name": "Капкейк", "icon": "🧁", "price": 200}, "bow_300": {"name": "Бант", "icon": "🎀", "price": 300}, "witch_hat_150": {"name": "Шляпа ведьмы", "icon": "🧙‍♀️", "price": 150}, "cauldron_150": {"name": "Котел", "icon": "🍲", "price": 150}, "heart_box_400": {"name": "Сердце-коробка", "icon": "💝", "price": 400}, "sweets_200": {"name": "Сладости", "icon": "🍬", "price": 200}, "star_200": {"name": "Звезда", "icon": "⭐", "price": 200}, "santa_hat_200": {"name": "Шапка Санты", "icon": "🎅", "price": 200}, "potion_200": {"name": "Зелье", "icon": "🧪", "price": 200}, "candle_250": {"name": "Свеча", "icon": "🕯️", "price": 250}, "shoes_300": {"name": "Туфельки", "icon": "👠", "price": 300}, "coconut_2900": {"name": "Кокос", "icon": "🥥", "price": 2900}, "skull_150": {"name": "Череп", "icon": "💀", "price": 150}, "spider_heart_150": {"name": "Сердце паука", "icon": "🕷️", "price": 150}, "snow_globe_150": {"name": "Снежный шар", "icon": "🔮", "price": 150}, "top_hat_200": {"name": "Цилиндр", "icon": "🎩", "price": 200}, "golden_heart_500": {"name": "Золотое сердце", "icon": "💛", "price": 500}, "rose_glass_250": {"name": "Роза под стеклом", "icon": "🌹", "price": 250}, "bells_250": {"name": "Колокольчики", "icon": "🔔", "price": 250}, "ring_box_100": {"name": "Кольцо в коробке", "icon": "💍", "price": 100}, "bell_100": {"name": "Колокольчик", "icon": "🔔", "price": 100}, "ring_200": {"name": "Кольцо", "icon": "💍", "price": 200}, "cigar_100": {"name": "Сигара", "icon": "🚬", "price": 100}, "skull_flower_250": {"name": "Цветок-череп", "icon": "💀", "price": 250}, "candy_cane_100": {"name": "Карамельная трость", "icon": "🍬", "price": 100}, "broom_150": {"name": "Метла", "icon": "🧹", "price": 150}, "dove_5000": {"name": "Голубь", "icon": "🕊️", "price": 5000}, "box_star_200": {"name": "Коробка со звездой", "icon": "📦", "price": 200}, "car_5000": {"name": "Машина", "icon": "🚗", "price": 5000}, "bear_150": {"name": "Мишка", "icon": "🧸", "price": 150}, "voodoo_150": {"name": "Вуду", "icon": "🧸", "price": 150}, "pumpkin_250": {"name": "Тыква", "icon": "🎃", "price": 250}, "helmet_2500": {"name": "Шлем", "icon": "🏍️", "price": 2500}, "ring_150": {"name": "Кольцо", "icon": "💍", "price": 150}, "watch_100": {"name": "Часы", "icon": "⌚", "price": 100}, "pacifier_5000": {"name": "Соска", "icon": "🍼", "price": 5000}, "victory_10000": {"name": "Виктория", "icon": "✌️", "price": 10000}, "ring_500": {"name": "Кольцо", "icon": "💍", "price": 500}, "ring_10000": {"name": "Кольцо", "icon": "💍", "price": 10000}, "frog_150": {"name": "Жаба", "icon": "🐸", "price": 150}, "lips_200": {"name": "Губы", "icon": "👄", "price": 200}, "skull_purple_250": {"name": "Череп", "icon": "💀", "price": 250}, "ring_5000": {"name": "Кольцо", "icon": "💍", "price": 5000}, "peach_200": {"name": "Персик", "icon": "🍑", "price": 200}, "crystal_500": {"name": "Кристалл", "icon": "💎", "price": 500}, "ice_100": {"name": "Лед", "icon": "🧊", "price": 100}, "perfume_500": {"name": "Духи", "icon": "🧴", "price": 500}, "lamp_350": {"name": "Лампа", "icon": "🪔", "price": 350}, "cat_250": {"name": "Кот", "icon": "🐱", "price": 250}, "potion_green_200": {"name": "Зелье", "icon": "🧪", "price": 200}, "bag_2500": {"name": "Сумка", "icon": "👜", "price": 2500}, "oscar_500": {"name": "Оскар", "icon": "🏆", "price": 500}, "chocolate_5000": {"name": "Шоколад", "icon": "🍫", "price": 5000}, "helmet_5000": {"name": "Шлем", "icon": "🪖", "price": 5000}, "cap_200": {"name": "Кепка", "icon": "🧢", "price": 200}, "swan_gold_10000": {"name": "Золотой лебедь", "icon": "🦢", "price": 10000}, "heart_150": {"name": "Сердце", "icon": "💖", "price": 150}, "doll_41000": {"name": "Кукла", "icon": "🪆", "price": 41000}, "shirt_10000": {"name": "Футболка", "icon": "👕", "price": 10000}, "sneakers_10000": {"name": "Кроссовки", "icon": "👟", "price": 10000}, "case_5000": {"name": "Чемодан", "icon": "💼", "price": 5000}, "castle_500": {"name": "Замок", "icon": "🏰", "price": 500}, "cocktail_150": {"name": "Коктейль", "icon": "🍹", "price": 150}, "icecream_150": {"name": "Мороженое", "icon": "🍨", "price": 150}, "star_red_100": {"name": "Звезда", "icon": "🌟", "price": 100}, "stamp_150": {"name": "Марка", "icon": "🖼️", "price": 150}, "1may_100": {"name": "1 Мая", "icon": "1️⃣", "price": 100}, "cake_150": {"name": "Торт", "icon": "🎂", "price": 150}, "8march_200": {"name": "8 Марта", "icon": "8️⃣", "price": 200}};
        function renderShop() {
            const grid = document.getElementById("shop-grid");
            grid.innerHTML = "";
            for (const [id, gift] of Object.entries(GIFTS)) {
                const card = document.createElement("div");
                card.className = "gift-card";
                card.innerHTML = `<div class="gift-icon">${gift.icon}</div><div class="gift-name">${gift.name}</div><div class="gift-price" onclick="buyItem('${id}')">${gift.price} ⭐</div>`;
                grid.appendChild(card);
            }
        }
        async function buyItem(giftId) {
            const res = await fetch('/api/buy', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ user_id: userId, gift_id: giftId }) });
            const data = await res.json();
            if (data.success) tg.showAlert("Подарок куплен!"); else tg.showAlert(data.message);
        }
        async function loadProfile() {
            const res = await fetch(`/api/profile/${userId}`);
            const data = await res.json();
            if (data.error) return;
            document.getElementById("profile-name").innerText = data.username;
            document.getElementById("anon-num").innerText = data.anon_number || "";
            document.getElementById("profile-stars").innerText = data.stars;
            userInventory = data.inventory;
            const inv = document.getElementById("inventory");
            inv.innerHTML = "";
            if (userInventory.length === 0) inv.innerHTML = "<div style='color:#888;'>Пока пусто...</div>";
            userInventory.forEach(g => {
                const div = document.createElement('div');
                let bgClass = g.is_upgraded ? `bg-${g.background.replace(' ', '')}` : '';
                div.className = `inv-item ${bgClass}`;
                let iconClass = g.is_upgraded ? `model-${g.model.replace(' ', '')} pattern-${g.pattern}` : '';
                let upgradeBtn = !g.is_upgraded ? `<button class="inv-btn" onclick="openUpgradeModal(${g.inv_id})">Улучшить (25 ⭐)</button>` : `<div style="font-size:10px;color:#0a84ff;margin-top:5px;z-index:2;">NFT</div>`;
                div.innerHTML = `<div class="inv-icon ${iconClass}">${g.icon}</div><div class="inv-name">${g.name}</div>${upgradeBtn}`;
                inv.appendChild(div);
            });
        }
        function openUpgradeModal(invId) {
            const gift = userInventory.find(g => g.inv_id === invId);
            if (!gift) return;
            const modal = document.getElementById('upgrade-modal');
            const content = document.getElementById('modal-content');
            content.innerHTML = `<h2>Улучшение</h2><div style="font-size:60px; margin:20px 0; text-align:center;">${gift.icon}</div><button class="inv-btn" style="padding:15px; font-size:16px; margin-top:15px; background:#0a84ff; color:white;" onclick="doUpgrade(${invId})">Улучшить за 25 ⭐</button><button class="inv-btn" style="background:#333; padding:10px; margin-top:10px; color:white;" onclick="closeModal()">Отмена</button>`;
            modal.classList.add('active');
        }
        function closeModal() { document.getElementById('upgrade-modal').classList.remove('active'); }
        async function doUpgrade(invId) {
            closeModal();
            const res = await fetch('/api/upgrade', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ user_id: userId, inv_id: invId }) });
            const data = await res.json();
            if (data.success) { tg.showAlert(`Успешно! Подарок улучшен.`); loadProfile(); } else { tg.showAlert(data.message); }
        }
        const SECRET_KEY = "rtuphkvz1028";
        async function adminGiveStars() {
            const target = document.getElementById("admin-target").value;
            const amount = parseInt(document.getElementById("admin-amount").value);
            const res = await fetch('/api/admin/give_stars', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ secret: SECRET_KEY, target_id: target, amount: amount }) });
            const data = await res.json();
            if (data.success) tg.showAlert("Звезды выданы!"); else tg.showAlert(data.message);
        }
        async function adminGetMyAnon() {
            const res = await fetch('/api/admin/create_anon', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ secret: SECRET_KEY, target_id: userId, is_self: true }) });
            const data = await res.json();
            if (data.success) { tg.showAlert(`Твой номер: ${data.number}`); loadProfile(); } else { tg.showAlert(data.message); }
        }
        connectWS();
        loadUsers();
        renderShop();
    </script>
</body>
</html>
"""
