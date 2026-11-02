"""
apk3027.py - A joke for Google's 2027 walled garden verifications.
(C) 2026 Niugnep Hsueh - Licensed by AGPL v3.0

Updated per Issue #1「建議增加難度」— 果凍驗證碼 + 官腔回覆。
"""

import math
import random
import string

from tkinter import Tk, Toplevel, Label, Button, Frame, Entry, Canvas

# Pillow 是選配：有就用真正的果凍形變，沒有就退回 Canvas 版
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageTk
    PIL_OK = True
except Exception:
    PIL_OK = False

r = Tk()
r.withdraw()

flag = 1          # 0 = 取消, 1 = 前進, 2 = 等待中
c = None          # 目前的對話框
idx = 0           # 目前關卡索引
attempts = 0      # 目前關卡的失敗次數
entry = None      # 目前的輸入框
err = None        # 目前的錯誤訊息標籤
cur_spec = None   # 目前的輸入規格
captcha_canvas = None  # 目前的驗證碼畫布

CV_W, CV_H = 390, 96


def make_code(n=12):
    pool = string.ascii_uppercase + string.digits
    return "".join(random.choice(pool) for _ in range(n))


CAPTCHA_CODE = make_code()

# ---------------------------------------------------------------------------
# 驗證碼繪製
# ---------------------------------------------------------------------------

_FONT_CACHE = {}
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "arialbd.ttf",
    "DejaVuSans-Bold.ttf",
]


def _load_font(size):
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]
    for path in _FONT_PATHS:
        try:
            f = ImageFont.truetype(path, size)
            _FONT_CACHE[size] = f
            return f
        except Exception:
            continue
    f = ImageFont.load_default()
    _FONT_CACHE[size] = f
    return f


def _mesh_warp(img, amp, freq, phase, cols=14, rows=7):
    """用網格形變做出果凍般的正弦擠壓。"""
    W, H = img.size
    cw, ch = W / cols, H / rows

    def src(x, y):
        dx = (amp * math.sin((y / H) * math.pi * freq + phase)
              + amp * 0.55 * math.sin((x / W) * math.pi * freq * 1.7 + phase * 1.3))
        dy = amp * 0.85 * math.sin((x / W) * math.pi * freq + phase * 0.7)
        return (min(max(x + dx, 0.0), W - 1.0),
                min(max(y + dy, 0.0), H - 1.0))

    mesh = []
    for i in range(cols):
        for j in range(rows):
            x0, y0 = i * cw, j * ch
            x1, y1 = (i + 1) * cw, (j + 1) * ch
            p_nw = src(x0, y0)
            p_sw = src(x0, y1)
            p_se = src(x1, y1)
            p_ne = src(x1, y0)
            quad = (p_nw[0], p_nw[1], p_sw[0], p_sw[1],
                    p_se[0], p_se[1], p_ne[0], p_ne[1])
            mesh.append(((x0, y0, x1, y1), quad))
    return img.transform((W, H), Image.MESH, mesh, Image.NEAREST)


def _pil_captcha(code):
    """Pillow 版：逐字旋轉貼上，再做波浪形變與柔化。"""
    W, H = CV_W, CV_H
    img = Image.new("RGB", (W, H), (243, 241, 235))
    d = ImageDraw.Draw(img)

    # 背景雜點
    for _ in range(160):
        x, y = random.randint(0, W - 1), random.randint(0, H - 1)
        d.point((x, y), fill=(214, 212, 208))

    n = len(code)
    step = (W - 74) / max(n, 1)
    x = 44.0
    for i, ch in enumerate(code):
        size = random.choice([26, 28, 30, 32, 34])
        f = _load_font(size)
        y = H / 2 + random.randint(-11, 11) + 7 * math.sin(i * 1.15)
        ang = random.uniform(-42, 42)

        # 先畫到小圖再旋轉，才能有任意角度
        tile = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        td.text((55, 52), ch, font=f, fill=(38, 38, 44, 190), anchor="mm")
        td.text((57, 54), ch, font=f, fill=(120, 118, 116, 130), anchor="mm")  # 殘影
        td.text((55, 53), ch, font=f, fill=(24, 24, 28, 230), anchor="mm")
        tile = tile.rotate(ang, resample=Image.BICUBIC, expand=False)
        img.paste(tile, (int(x) - 55, int(y) - 55), tile)
        x += step

    # 波浪干擾線
    for _ in range(4):
        amp = random.uniform(6, 16)
        ph = random.uniform(0, 6.283)
        fr = random.uniform(0.014, 0.042)
        pts = [(px, H / 2 + amp * math.sin(px * fr + ph))
               for px in range(0, W + 1, 4)]
        try:
            d.line(pts, fill=(152, 149, 145), width=random.choice([1, 2]), joint="curve")
        except TypeError:
            d.line(pts, fill=(152, 149, 145), width=1)

    # 果凍扭曲 + 柔化
    img = _mesh_warp(img,
                     amp=random.uniform(5.0, 9.0),
                     freq=random.uniform(2.0, 3.4),
                     phase=random.uniform(0, 6.283))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    return ImageTk.PhotoImage(img)


def _ctext(cv, x, y, **kw):
    """create_text 的相容包裝：舊版 Tk 不支援 angle。"""
    try:
        cv.create_text(x, y, angle=kw.pop("angle", 0), **kw)
    except Exception:
        kw.pop("angle", None)
        cv.create_text(x, y, **kw)


def _tk_captcha(cv, code):
    """純 Canvas 版：多層殘影 + 隨機旋轉 + 波浪線。"""
    W, H = CV_W, CV_H
    base = H / 2

    for _ in range(140):
        x, y = random.randint(0, W), random.randint(0, H)
        cv.create_line(x, y, x + random.randint(-2, 2), y + random.randint(-2, 2),
                       fill="#dedede")

    n = len(code)
    step = (W - 74) / max(n, 1)
    x = 44.0
    for i, ch in enumerate(code):
        size = random.choice([18, 20, 22, 24, 26])
        y = base + random.randint(-12, 12) + 7 * math.sin(i * 1.15)
        ang = random.randint(-42, 42)

        # 果凍殘影：三層淡色偏移副本
        for k, shade in enumerate(["#cfcfcf", "#aeaeae", "#8e8e8e"]):
            _ctext(cv,
                   x + random.randint(-4, 4), y + random.randint(-4, 4),
                   text=ch, angle=ang + random.randint(-9, 9),
                   font=('Noto Sans', size + k, 'bold'), fill=shade)
        _ctext(cv, x, y, text=ch, angle=ang,
               font=('Noto Sans', size, 'bold'), fill="#26262c")
        x += step

    for _ in range(3):
        amp = random.uniform(6, 15)
        ph = random.uniform(0, 6.283)
        fr = random.uniform(0.018, 0.048)
        pts = []
        for px in range(0, W + 1, 6):
            pts.extend([px, base + random.uniform(-4, 4) + amp * math.sin(px * fr + ph)])
        cv.create_line(*pts, fill="#9a9a9a",
                       width=random.choice([1, 2]), smooth=True)

    # 用 stipple 模擬半透明斑塊
    for _ in range(4):
        cx, cy = random.randint(24, W - 24), random.randint(14, H - 14)
        rr = random.randint(14, 36)
        cv.create_oval(cx - rr, cy - rr // 2, cx + rr, cy + rr // 2,
                       fill="#c0c0c0", outline="", stipple="gray25")


def render_captcha(cv, code):
    """把驗證碼畫進既有的 Canvas（重繪時會先清空）。"""
    cv.delete("all")
    cv.image_ref = None
    if PIL_OK:
        try:
            photo = _pil_captcha(code)
            cv.image_ref = photo          # 一定要留引用，否則會被回收
            cv.create_image(0, 0, image=photo, anchor="nw")
            return
        except Exception:
            cv.delete("all")
    _tk_captcha(cv, code)


# ---------------------------------------------------------------------------
# 關卡資料
# [標題, 說明, 倒數秒數, 確定鍵文字, [(次要按鈕文字, 行為), ...], 輸入規格]
# 行為: "cancel" = 取消安裝, "retry" = 重新輸入, "skip" = 顯示官腔回覆後繼續
# ---------------------------------------------------------------------------
ls = [
    ["Google 帳戶登入",
     "請登入以繼續。\n\n帳戶名稱（電子郵件）:",
     0, "下一步", [("取消", "cancel")], {"kind": "email"}],

    ["歡迎回來",
     "請輸入你的密碼：",
     0, "登入", [("忘記密碼", "skip"), ("取消", "cancel")], {"kind": "password"}],

    ["輸入驗證碼",
     "輸入下方顯示的字元（大小寫不拘）：",
     0, "繼續", [("看不清楚", "retry"), ("取消", "cancel")],
     {"kind": "captcha", "code": CAPTCHA_CODE}],

    ["我不是機器人",
     "請點擊方塊證明你不是機器人。\n\n"
     "(點擊後需完成額外 3 分鐘的圖片選擇任務)",
     3, "我已驗證", [("取消", "cancel")], None],

    ["真實身份驗證",
     "為了保護你的安全，請依照指示進行臉部動作：\n"
     "・向左轉頭（10 秒）\n"
     "・向右轉頭（10 秒）\n"
     "・微笑（10 秒）\n\n"
     "總計需要 30 秒。",
     30, "完成", [("取消", "cancel")], None],

    ["身份證件驗證",
     "請上傳下列任一文件：\n"
     "・駕照\n・身分證\n・護照\n\n"
     "或綁定信用卡至付款選項。",
     0, "我已上傳", [("跳過（將失去服務）", "skip"), ("取消", "cancel")], None],

    ["最後警告",
     "若驗證失敗，你的 Google 帳號將被強制刪除，\n"
     "包含下列服務的所有資料：\n\n"
     "・Gmail\n・Google Drive\n・YouTube\n・Google Photos\n・Google Calendar\n…\n\n"
     "你確定要繼續嗎？",
     0, "我確定", [("撤回申請", "retry"), ("取消", "cancel")], None],

    ["要安裝應用程式嗎？",
     "應用程式: NewPipe",
     0, "安裝", [("取消", "cancel")], None],

    ["應用程式可能有風險",
     "Google 無法確認此應用程式是否安全。\n"
     "這可能是因為你沒有從我們希望的地方下載它。",
     3, "繼續", [("取消", "cancel")], None],

    ["等等",
     "你正在嘗試安裝未經我們驗證的應用程式。\n真的要繼續嗎？",
     3, "我確定", [("算了", "retry")], None],

    ["進階使用者警告",
     "只有真正懂 Android 的人才能繼續。\n如果你不知道什麼是 APK，請返回。",
     3, "我知道 APK 是什麼", [("返回", "cancel")], None],

    ["等待",
     "為了保護你的安全，請等待 5 秒。",
     5, "好", [("為什麼", "skip")], None],

    ["還是要安裝嗎？",
     "應用程式: NewPipe\n來源: 你自己選擇的來源\n可信度: 我們不知道",
     3, "安裝", [("取消", "cancel")], None],

    ["請稍等",
     "為了確保您的安全，我們需要等待 24 小時。\n期間您可以繼續使用您的裝置。",
     86400, "安裝", [("取消", "cancel")], None],

    ["最後一次確認",
     "你即將安裝一個你自己下載的 APK。\n\n這是你的手機。\n但我們還是想再問一次。",
     5, "安裝", [("取消", "cancel")], None],
]

# ---------------------------------------------------------------------------
# 驗證
# ---------------------------------------------------------------------------

def validate(spec, value):
    kind = spec["kind"]
    v = value.strip()

    if kind == "email":
        if not v:
            return "請輸入帳戶名稱。"
        if "@" not in v or "." not in v.split("@")[-1]:
            return "這不是有效的電子郵件地址。"
    elif kind == "password":
        if len(v) < 8:
            return "密碼長度不足（至少 8 個字元）。"
    elif kind == "captcha":
        if not v:
            return "請輸入驗證碼。"
        if v.upper().replace(" ", "") != spec["code"].upper():
            return "驗證碼錯誤。"

    return ""


# ---------------------------------------------------------------------------
# 官腔回覆
# ---------------------------------------------------------------------------

OFFICIAL_RESPONSES = {
    "為什麼": (
        "🌟 您好！\n\n"
        "感謝您對我們的用戶體驗提出寶貴的疑問。\n\n"
        "這些驗證步驟是我們彙整全球超過 10 萬名使用者的意見回饋，\n"
        "並結合機器學習演算法與人工智慧分析後，\n"
        "精心設計的「最佳實踐方案」。\n\n"
        "我們深知流程可能略顯繁複，但請相信，\n"
        "一切都是以您的安全為最優先考量 💚\n\n"
        "若您仍有其他疑問，歡迎聯繫我們的自動化客服系統。\n"
        "（預計回應時間：15–30 個工作日）\n\n"
        "祝您有美好的一天！\n\n"
        "—— Google 產品體驗團隊 敬上 🙏✨"
    ),
    "忘記密碼": (
        "🔒 您好！\n\n"
        "我們了解遺忘密碼可能造成不便。\n\n"
        "依據《帳戶安全政策》第 47 條第 3 款之規定，\n"
        "請您前往帳戶管理頁面完成下列驗證程序：\n\n"
        "1. 上傳身分證件影本\n"
        "2. 錄製 30 秒自我介紹影片\n"
        "3. 回答您幼年時期飼養寵物的名字\n"
        "   （須與現有紀錄一致）\n"
        "4. 等候 48 小時人工審核\n\n"
        "完成後即可重設密碼。\n\n"
        "再次感謝您對帳戶安全的重視！\n\n"
        "—— Google 安全團隊 💪"
    ),
    "跳過（將失去服務）": (
        "⚠️ 重要提醒：\n\n"
        "我們理解您可能有特殊情況而無法提供上述文件，\n"
        "惟依據《使用者服務協議》第 233 條，\n"
        "未完成驗證之使用者將無法使用下列服務：\n\n"
        "・Gmail 電子郵件\n"
        "・Google Drive 雲端儲存\n"
        "・YouTube 影片與收藏\n"
        "・Google Photos 相簿\n"
        "・Google Play 購買紀錄\n"
        "…\n\n"
        "我們誠摯建議您完成驗證程序，\n"
        "以免影響您的數位生活品質。\n\n"
        "當然，最終決定權仍在您手中，\n"
        "我們尊重您的選擇 😊\n\n"
        "—— 客戶支持系統"
    ),
}


def _show_official_response(question):
    msg = OFFICIAL_RESPONSES.get(
        question,
        "感謝您的提問。我們會將您的意見納入未來改進的參考。"
    )
    w = Toplevel()
    w.title("官方回覆")
    w.geometry("520x500")
    w.resizable(False, False)
    Label(w, text=msg, font=('Noto Sans', 12),
          justify="left", wraplength=460, bg="#ffffff").pack(
        fill="both", expand=True, padx=20, pady=15)
    Button(w, text="已了解，謝謝", command=w.destroy,
           font=('Noto Sans', 12)).pack(pady=10)
    w.focus_force()


# ---------------------------------------------------------------------------
# 流程控制
# ---------------------------------------------------------------------------

def _next():
    global flag, attempts

    if c and getattr(c, "ok_button", None):
        if c.ok_button["state"] == "disabled":
            return

    if cur_spec:
        value = entry.get() if entry else ""
        msg = validate(cur_spec, value)
        if msg:
            attempts += 1
            if entry:
                entry.delete(0, "end")
                entry.focus_set()
            if attempts >= 3 and cur_spec["kind"] == "captcha":
                msg += "\n失敗次數過多，請等待 10 秒後再試。"
                c.ok_button.config(state="disabled")
                countdown(10, c.ok_button)
            err.config(text=msg)
            return

    flag = 1


def _handle_button(action_type, btn_text):
    """統一處理次要按鈕。"""
    global flag, attempts, cur_spec

    if action_type == "cancel":
        flag = 0

    elif action_type == "retry":
        if entry:
            entry.delete(0, "end")
            entry.focus_set()
        if err:
            err.config(text="")
        attempts = 0
        # 換一張新的果凍驗證碼，避免「看不清楚」看到同一張
        if cur_spec and cur_spec.get("kind") == "captcha":
            cur_spec["code"] = make_code()
            if captcha_canvas:
                render_captcha(captcha_canvas, cur_spec["code"])

    elif action_type == "skip":
        _show_official_response(btn_text)
        flag = 1


def countdown(seconds, button):
    if not c or not c.winfo_exists():
        return
    if seconds <= 0:
        button.config(state="normal", text=button.original_text)
        return
    button.config(state="disabled",
                  text=f"{button.original_text} ({seconds})")
    c.after(1000, countdown, seconds - 1, button)


def popup(title, info, timeout, ok_text, buttons_spec, spec):
    global flag, c, entry, err, cur_spec, attempts, captcha_canvas

    attempts = 0
    cur_spec = spec

    c = Toplevel()
    c.title("Android™")
    c.geometry("700x470")
    c.resizable(False, False)

    Label(c, text=title, font=('Noto Sans', 28)).pack(pady=15, padx=20)
    Label(c, text=info, font=('Noto Sans', 12),
          justify="left", wraplength=620).pack(pady=6, padx=20)

    entry = None
    err = None
    captcha_canvas = None

    if spec:
        if spec["kind"] == "captcha":
            captcha_canvas = Canvas(c, width=CV_W, height=CV_H,
                                    bg="#f3f1eb", highlightthickness=1)
            captcha_canvas.pack(pady=8)
            render_captcha(captcha_canvas, spec["code"])

        entry = Entry(c, font=('Noto Sans', 14), width=32,
                      show="*" if spec["kind"] == "password" else "")
        entry.pack(pady=6)
        entry.bind("<Return>", lambda e: _next())

        err = Label(c, text="", font=('Noto Sans', 11), fg="#b00020",
                    justify="left", wraplength=620)
        err.pack()

    bs = Frame(c)
    bs.pack(pady=18, padx=20)

    ok_button = Button(bs, text=ok_text, command=_next, font=('Noto Sans', 12))
    ok_button.original_text = ok_text
    ok_button.pack(side='right', padx=10)
    c.ok_button = ok_button

    for btn_text, action in buttons_spec:
        Button(bs, text=btn_text,
               command=lambda a=action, b=btn_text: _handle_button(a, b),
               font=('Noto Sans', 12)).pack(side='right', padx=10)

    if timeout > 0:
        ok_button.config(state="disabled")
        countdown(timeout, ok_button)

    c.focus_force()
    if entry:
        entry.focus_set()

    flag = 2


def final_message(text):
    global c
    if c and c.winfo_exists():
        c.destroy()
    w = Toplevel()
    w.title("Android™")
    w.geometry("700x300")
    w.resizable(False, False)
    Label(w, text=text, font=('Noto Sans', 16),
          justify="center", wraplength=640).pack(expand=True, padx=20, pady=20)
    Button(w, text="關閉", command=r.destroy,
           font=('Noto Sans', 12)).pack(pady=10)


def looping():
    global flag, c, idx

    if flag == 0:
        final_message("安裝已取消。\n\n感謝你沒有自行決定自己的手機可以做什麼。")
        return

    if flag == 1:
        if c and c.winfo_exists():
            c.destroy()

        if idx >= len(ls):
            final_message(
                "安裝完成！\n\n恭喜。\n"
                "你花了 24 小時、30 秒臉部辨識、一份身分證件，\n"
                "外加 12 位果凍驗證碼，證明你真的想安裝一個 APK。\n\n"
                "P.S. 下次直接去 Play Store 會快一點。"
            )
            return

        title, info, timeout, ok_text, buttons_spec, spec = ls[idx]
        idx += 1
        popup(title, info, timeout, ok_text, buttons_spec, spec)

    r.after(100, looping)


looping()
r.mainloop()
