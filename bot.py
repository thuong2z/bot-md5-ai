import telebot
import sqlite3
import random
import string
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, ADMIN_ID, BANK_INFO, RATE, MIN_NAP, MAX_NAP

bot = telebot.TeleBot(TOKEN)

# ==========================
# ✅ DATABASE
# ==========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS nap
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount INTEGER, code TEXT, status TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, ?)", (user_id, username, 0))
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else 0

def update_balance(user_id, amount):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

# ==========================
# ✅ MENU CHÍNH
# ==========================
def main_menu(is_admin=False):
    menu = ReplyKeyboardMarkup(resize_keyboard=True)
    menu.add(KeyboardButton("💳 Tài Khoản"), KeyboardButton("💰 Nạp Tiền"))
    menu.add(KeyboardButton("🔮 Phân Tích"), KeyboardButton("🎟 Nhập Code"))
    menu.add(KeyboardButton("📞 Hỗ Trợ"), KeyboardButton("📜 Lịch Sử Nạp"))
    if is_admin:
        menu.add(KeyboardButton("🛠 Panel Admin"))
    return menu

# ==========================
# ✅ /START
# ==========================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Người dùng"
    add_user(user_id, username)

    # Gửi hình minh họa + giới thiệu
    photo_url = "https://i.ibb.co/fMQnWJd/md5bot.jpg"  # thay link ảnh minh họa bot của bạn
    caption = (f"🐰 **BOT PHÂN TÍCH MD5 SIÊU CHUẨN**\n\n"
               f"Chào @{username}!\n"
               f"💰 Số xu hiện có: {get_balance(user_id)}\n\n"
               f"Chọn chức năng bên dưới để sử dụng:")
    bot.send_photo(user_id, photo_url, caption, reply_markup=main_menu(user_id in ADMIN_ID))

# ==========================
# ✅ XỬ LÝ NÚT MENU
# ==========================
@bot.message_handler(func=lambda m: True)
def handle_menu(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Người dùng"
    text = message.text
    add_user(user_id, username)

    if text == "💳 Tài Khoản":
        bot.reply_to(message, f"👤 @{username}\n💰 Số xu: {get_balance(user_id)}")

    elif text == "💰 Nạp Tiền":
        bot.reply_to(message, f"✅ Dùng lệnh: /nap <số tiền>\nVí dụ: /nap 50000")

    elif text == "🔮 Phân Tích":
        bot.reply_to(message, "✅ Gửi chuỗi MD5 (32 ký tự) để phân tích.")

    elif text == "🎟 Nhập Code":
        bot.reply_to(message, "⏳ Tính năng này đang phát triển.")

    elif text == "📞 Hỗ Trợ":
        bot.reply_to(message, "📞 Liên hệ Admin: @TenAdmin (hoặc đổi thành link nhóm hỗ trợ)")

    elif text == "📜 Lịch Sử Nạp":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT amount, status FROM nap WHERE user_id=? ORDER BY id DESC LIMIT 5", (user_id,))
        rows = c.fetchall()
        conn.close()
        if rows:
            ls = "\n".join([f"{i+1}. {r[0]:,}đ - {r[1]}" for i, r in enumerate(rows)])
            bot.reply_to(message, f"📜 LỊCH SỬ NẠP GẦN ĐÂY:\n{ls}")
        else:
            bot.reply_to(message, "❌ Chưa có lịch sử nạp.")

    elif text == "🛠 Panel Admin" and user_id in ADMIN_ID:
        bot.reply_to(message, "🛠 ADMIN PANEL\n/danhsach\n/duyetnap <user_id> <code>\n/guitien <user_id> <so_xu>")

# ==========================
# ✅ NẠP TIỀN + DUYỆT (giữ nguyên code cũ)
# ==========================
@bot.message_handler(commands=['nap'])
def nap_tien(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Người dùng"
    add_user(user_id, username)

    try:
        amount = int(message.text.split()[1])
        if amount < MIN_NAP or amount > MAX_NAP:
            bot.reply_to(message, f"⚠️ Nạp tối thiểu {MIN_NAP:,}đ, tối đa {MAX_NAP:,}đ!")
            return
        xu = amount // RATE
        code = ''.join(random.choices(string.digits, k=9))

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO nap (user_id, amount, code, status) VALUES (?, ?, ?, ?)", (user_id, amount, code, "pending"))
        conn.commit()
        conn.close()

        text = (f"🐰 NẠP TIỀN\n\n"
                f"💳 STK: {BANK_INFO['stk']}\n"
                f"🏦 Ngân hàng: {BANK_INFO['bank']}\n"
                f"👤 Tên: {BANK_INFO['name']}\n"
                f"📝 Nội dung: NAP {code}\n"
                f"💰 Bạn sẽ nhận: {xu} xu\n\n"
                f"✅ Chuyển xong admin sẽ duyệt trong vài phút.")
        bot.reply_to(message, text)

        for admin in ADMIN_ID:
            bot.send_message(admin, f"🆕 ĐƠN NẠP\nUser: {username} ({user_id})\nSố tiền: {amount}\nCode: {code}")

    except:
        bot.reply_to(message, "❌ Sai cú pháp!\nDùng: /nap 50000")

@bot.message_handler(commands=['duyetnap'])
def duyet_nap(message):
    if message.from_user.id not in ADMIN_ID:
        return
    try:
        args = message.text.split()
        user_id = int(args[1])
        code = args[2]
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT amount FROM nap WHERE user_id=? AND code=? AND status='pending'", (user_id, code))
        res = c.fetchone()
        if res:
            amount = res[0]
            xu = amount // RATE
            update_balance(user_id, xu)
            c.execute("UPDATE nap SET status='done' WHERE user_id=? AND code=?", (user_id, code))
            conn.commit()
            bot.reply_to(message, f"✅ Duyệt thành công +{xu} xu")
            bot.send_message(user_id, f"✅ Admin đã duyệt đơn nạp {amount:,}đ, bạn nhận được {xu} xu")
        else:
            bot.reply_to(message, "❌ Không tìm thấy đơn!")
        conn.close()
    except:
        bot.reply_to(message, "❌ Sai cú pháp!\nDùng: /duyetnap user_id code")

# ==========================
# ✅ PHÂN TÍCH MD5 (giữ nguyên)
# ==========================
@bot.message_handler(func=lambda msg: len(msg.text) == 32)
def md5_analyze(message):
    user_id = message.from_user.id
    username = message.from_user.username or "Người dùng"
    add_user(user_id, username)
    balance = get_balance(user_id)

    if balance < 1:
        bot.reply_to(message, "❌ Bạn không đủ xu! Hãy nạp thêm.")
        return

    update_balance(user_id, -1)
    tai_percent = round(random.uniform(50, 70), 2)
    xiu_percent = round(100 - tai_percent, 2)
    ket_qua = "🔥 TÀI" if tai_percent > 50 else "💧 XỈU"

    bot.reply_to(message,
                 f"🐰 PHÂN TÍCH MD5 🔮\n\n"
                 f"{message.text}\n\n"
                 f"💎 Kết quả: {ket_qua}\n"
                 f"📊 Tài: {tai_percent}% | Xỉu: {xiu_percent}%\n"
                 f"💰 Xu còn: {get_balance(user_id)}")

# ==========================
# ✅ CHẠY BOT
# ==========================
if __name__ == "__main__":
    init_db()
    print("✅ Bot đang chạy...")
    bot.infinity_polling()
