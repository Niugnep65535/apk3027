"""
apk3027.py - A joke for Google's 2027 walled garden verifications.
(C) 2026 Niugnep <penguin@niugnep.idv.tw> - Licensed by AGPL v3.0 
"""
from tkinter import *
from time import sleep

r = Tk()
r.withdraw()

flag = 1
c = None
idx = 0

ls = [
    ["要安裝應用程式嗎？",
     "應用程式: NewPipe",
     0, "安裝", ["取消"]],

    ["應用程式可能有風險",
     "Google 無法確認此應用程式是否安全。\n"
     "這可能是因為你沒有從我們希望的地方下載它。",
     3, "繼續", ["取消"]],

    ["等等",
     "你正在嘗試安裝未經我們驗證的應用程式。\n"
     "真的要繼續嗎？",
     3, "我確定", ["算了"]],

    ["進階使用者警告",
     "只有真正懂 Android 的人才能繼續。\n"
     "如果你不知道什麼是 APK，請返回。",
     3, "我知道 APK 是什麼", ["返回"]],

    ["等待",
     "為了保護你的安全，請等待 5 秒。",
     5, "好", ["為什麼"]],

    ["還是要安裝嗎？",
     "應用程式: NewPipe\n"
     "來源: 你自己選擇的來源\n"
     "可信度: 我們不知道",
     3, "安裝", ["取消"]],

    # 這是靈魂
    ["請稍等",
     "為了確保您的安全，我們需要等待 24 小時。\n"
     "期間您可以繼續使用您的裝置\n",
     86400, "安裝", ["取消"]],

    ["最後一次確認",
     "你即將安裝一個你自己下載的 APK。\n\n"
     "這是你的手機。\n"
     "但我們還是想再問一次。",
     5, "安裝", ["取消"]]
]


def _next():
    global flag

    # OK 按鈕被禁用時，不允許繼續
    if c and getattr(c, "ok_button", None):
        if c.ok_button["state"] == "disabled":
            return

    flag = 1


def _exit():
    global flag
    flag = 0


def enable_ok():
    if c and c.winfo_exists():
        c.ok_button.config(state="normal")


def countdown(seconds, button):
    if not c or not c.winfo_exists():
        return

    if seconds <= 0:
        button.config(state="normal")
        return

    button.config(
        state="disabled",
        text=f"{button.original_text} ({seconds})"
    )

    c.after(1000, countdown, seconds - 1, button)


def popup(title, info, timeout, ok_btn, buttons):
    global flag, c

    c = Toplevel()
    c.title("Android™")
    c.geometry("650x300")
    c.resizable(False, False)

    Label(
        c,
        text=title,
        font=('Noto Sans', 28)
    ).pack(pady=20, padx=20)

    Label(
        c,
        text=info,
        font=('Noto Sans', 12),
        justify="left"
    ).pack(pady=10, padx=20)

    bs = Frame(c)
    bs.pack(pady=20, padx=20)

    ok_button = Button(
        bs,
        text=ok_btn,
        command=_next,
        font=('Noto Sans', 12)
    )

    ok_button.original_text = ok_btn
    ok_button.pack(side='right', padx=10)

    # 把按鈕掛到視窗上，方便其他函式取得
    c.ok_button = ok_button

    for i in buttons:
        Button(
            bs,
            text=i,
            command=_exit,
            font=('Noto Sans', 12)
        ).pack(side='right', padx=10)

    # timeout > 0 時，OK 按鈕一開始就是灰的
    if timeout > 0:
        ok_button.config(state="disabled")
        countdown(timeout, ok_button)
    flag = 2


def looping():
    global flag, c, idx

    if flag == 0:
        if c and c.winfo_exists():
            c.destroy()

        Label(
            r,
            text="安裝已取消。\n\n"
                 "感謝你沒有自行決定自己的手機可以做什麼。",
            font=('Noto Sans', 16)
        ).pack()

        return

    if flag == 1:
        if c and c.winfo_exists():
            c.destroy()

        if idx >= len(ls):
            Label(
                r,
                text="安裝完成！\n\n"
                     "恭喜。\n"
                     "你花了 24 小時證明你真的想安裝一個 APK。",
                font=('Noto Sans', 18)
            ).pack()

            return

        title, info, timeout, ok_btn, buttons = ls[idx]

        idx += 1
        popup(title, info, timeout, ok_btn, buttons)

    r.after(100, looping)


looping()
r.mainloop()
