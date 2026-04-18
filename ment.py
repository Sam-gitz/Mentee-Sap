"""
Mentee-SAP — Mentor/Mentee/Student Desktop Application
Built with Python tkinter (stdlib only — no pip required for GUI)
Requires: pip install google-generativeai twilio
Run: python mentee_sap.py

FEATURES:
  - Separate Login pages for Mentor and Mentee
  - 1-to-1 Chat Messaging between Mentor and Mentee
  - Create Account / Registration Flow
  - Role-Based Access Control
  - 100% Dynamic Data (No Fake Seed Users)
  - Integrated Automated Advisor (Hidden Gemini backend)
  - Twilio SMS Notifications for Session Requests
  - Dynamic Session Management (Request, Accept, Decline)
  - NEW: Group Chats (Mentors can create rooms with multiple mentees)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading, json, os, uuid
from datetime import datetime

try:
    from twilio.rest import Client
except ImportError:
    Client = None

# Replace these with your actual Twilio credentials
TWILIO_SID = "your_twilio_account_sid"
TWILIO_AUTH = "your_twilio_auth_token"
TWILIO_FROM = "+1234567890"  # Your Twilio phone number

# --- HARDCODED GEMINI API KEY ---
SYSTEM_API_KEY = "AIzaSyBZFwUd4f8Mh-JFIJlKhX4XDQfKRE5_Skc"


# ══════════════════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════════════════
BG      = "#0f0e0d"
BG2     = "#1a1816"
BG3     = "#252220"
SURFACE = "#2e2b27"
BORDER  = "#2a2825"
TEXT    = "#f0ede8"
TEXT2   = "#a09890"
TEXT3   = "#6b6560"
GOLD    = "#d4a853"
GOLD2   = "#e8c47a"
SAGE    = "#7a9e7e"
SAGE2   = "#a0c4a5"
CORAL   = "#c97b5a"
BLUE    = "#5b8dd9"
BLUE2   = "#7aaae8"
PURPLE  = "#9b72cf"

FONT_H1   = ("Georgia", 22, "bold")
FONT_H2   = ("Georgia", 16, "bold")
FONT_H3   = ("Georgia", 13, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_SM   = ("Helvetica", 10)
FONT_XS   = ("Helvetica", 9)
FONT_BOLD = ("Helvetica", 11, "bold")
FONT_MONO = ("Courier", 10)

AVATARS = ["🧑‍💻","👩‍💼","👨‍🎓","👩‍🔬","🧑‍🎨","🧑‍🚀","👷","🦸",
           "👩‍🏫","👨‍🏫","🧑‍🔧","👩‍💻","🧑‍⚕️","👩‍🎤","🧑‍🌾","🎯"]

# ══════════════════════════════════════════════════════════════════════════════
#  DATA FILES
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
PROFILE_FILE  = os.path.join(BASE_DIR, "msap_profile.json")
PEOPLE_FILE   = os.path.join(BASE_DIR, "msap_people.json")
MESSAGES_FILE = os.path.join(BASE_DIR, "msap_messages.json")
SESSIONS_FILE = os.path.join(BASE_DIR, "msap_sessions.json")
GROUPS_FILE   = os.path.join(BASE_DIR, "msap_groups.json")  # NEW: Groups DB

SEED_DATA = []

def load_people():
    if os.path.exists(PEOPLE_FILE):
        try:
            with open(PEOPLE_FILE) as f: return json.load(f)
        except Exception: pass
    save_people(list(SEED_DATA))
    return list(SEED_DATA)

def save_people(data):
    try:
        with open(PEOPLE_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print("Save error:", e)

def load_my_profile():
    default = {"fname":"Guest","lname":"User","avatar":"👤","role":"New User","location":"Not set","linkedin":"","bio":"Write something about yourself.","goal":"Set your goal here","skills":"","avail":"Flexible"}
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE) as f: default.update(json.load(f))
        except Exception: pass
    return default

def save_my_profile(p):
    try:
        with open(PROFILE_FILE, "w") as f: json.dump(p, f, indent=2)
    except Exception: pass

def load_messages():
    if os.path.exists(MESSAGES_FILE):
        try:
            with open(MESSAGES_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def save_messages(data):
    try:
        with open(MESSAGES_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print("Messages save error:", e)

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE) as f: return json.load(f)
        except Exception: pass
    return []

def save_sessions(data):
    try:
        with open(SESSIONS_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print("Sessions save error:", e)

def load_groups():
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE) as f: return json.load(f)
        except Exception: pass
    return []

def save_groups(data):
    try:
        with open(GROUPS_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print("Groups save error:", e)

def conv_key(id1, id2):
    return f"{min(id1,id2)}|{max(id1,id2)}"


# ══════════════════════════════════════════════════════════════════════════════
#  SHARED WIDGET HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def gold_btn(parent, text, cmd, font=FONT_BOLD):
    return tk.Button(parent, text=text, font=font, bg=GOLD, fg="#1a1614", relief="flat", padx=12, pady=6, cursor="hand2", activebackground=GOLD2, activeforeground="#1a1614", command=cmd)

def outline_btn(parent, text, cmd, fg_color=TEXT2):
    return tk.Button(parent, text=text, font=FONT_SM, bg=SURFACE, fg=fg_color, relief="flat", padx=12, pady=6, cursor="hand2", activebackground=BG3, activeforeground=TEXT, command=cmd)

def danger_btn(parent, text, cmd):
    return tk.Button(parent, text=text, font=FONT_SM, bg="#3a1a1a", fg="#e08080", relief="flat", padx=12, pady=6, cursor="hand2", activebackground="#4a2020", activeforeground="#f0a0a0", command=cmd)

def divider(parent, padx=30, pady=12):
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=padx, pady=pady)

def scrollable(parent, bg=BG):
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
    sb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=bg)
    wid = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))
    return canvas, inner


# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN & REGISTRATION PAGE
# ══════════════════════════════════════════════════════════════════════════════
class LoginPage(tk.Frame):
    def __init__(self, master, people, on_login):
        super().__init__(master, bg=BG)
        self.people    = people
        self.on_login  = on_login
        self._mode     = tk.StringVar(value="mentee")
        self._action   = tk.StringVar(value="login")
        self._err_var  = tk.StringVar(value="")
        self._email_v = tk.StringVar()
        self._pw_v = tk.StringVar()
        self._fname_v = tk.StringVar()
        self._lname_v = tk.StringVar()
        self._build()

    def _build(self):
        left = tk.Frame(self, bg=BG2, width=360)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)
        self._build_left(left)
        right = tk.Frame(self, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._right_panel = right
        self._build_right(right)

    def _build_left(self, panel):
        tk.Frame(panel, bg=GOLD, height=4).pack(fill="x")
        inner = tk.Frame(panel, bg=BG2)
        inner.pack(fill="both", expand=True, padx=36, pady=40)
        tk.Label(inner, text="Mentee", font=("Georgia",28,"bold"), fg=GOLD,  bg=BG2).pack(anchor="w")
        tk.Label(inner, text="-SAP",   font=("Georgia",28,"italic"), fg=TEXT2, bg=BG2).pack(anchor="w")
        tk.Label(inner, text="Mentor · Mentee · Student\nPlatform", font=FONT_BODY, fg=TEXT3, bg=BG2).pack(anchor="w", pady=(6,30))
        for icon, txt in [("🎯","Goal-driven mentorship"),("🤝","1-to-1 & Group messaging"),("💡","Career Coaching Advisor"),("📅","Session scheduling"),("📈","Progress tracking")]:
            row = tk.Frame(inner, bg=BG2); row.pack(anchor="w", pady=4)
            tk.Label(row, text=icon, font=("Helvetica",14), bg=BG2).pack(side="left", padx=(0,8))
            tk.Label(row, text=txt, font=FONT_SM, fg=TEXT2, bg=BG2).pack(side="left")
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=24)
        tk.Label(inner, text="Start your journey today.", font=FONT_XS, fg=TEXT3, bg=BG2).pack(anchor="w")

    def _build_right(self, panel):
        for w in panel.winfo_children(): w.destroy()
        wrapper = tk.Frame(panel, bg=BG)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")
        mode = self._mode.get(); action = self._action.get()
        accent = GOLD if mode == "mentor" else BLUE
        
        if action == "login":
            title = "Mentor Login" if mode == "mentor" else "Mentee / Student Login"
            sub   = "Sign in to manage mentees, sessions\nand your mentor profile." if mode == "mentor" else "Sign in to connect with mentors\nand track your learning journey."
        else:
            title = "Create Mentor Account" if mode == "mentor" else "Create Mentee Account"
            sub   = "Join as a mentor to guide the next generation." if mode == "mentor" else "Join to connect with mentors and start growing."

        tk.Label(wrapper, text=title, font=FONT_H1, fg=TEXT, bg=BG).pack(anchor="w", pady=(0,4))
        tk.Label(wrapper, text=sub, font=FONT_SM, fg=TEXT2, bg=BG, justify="left").pack(anchor="w", pady=(0,20))

        tog = tk.Frame(wrapper, bg=BG); tog.pack(anchor="w", pady=(0,20))
        tk.Button(tog, text=" 🏆  Mentor ", font=FONT_SM, bg=GOLD if mode=="mentor" else SURFACE, fg="#1a1614" if mode=="mentor" else TEXT2, relief="flat", padx=14, pady=7, cursor="hand2", command=lambda: self._switch_mode("mentor")).pack(side="left", padx=(0,6))
        tk.Button(tog, text=" 🎓  Mentee / Student ", font=FONT_SM, bg=BLUE if mode=="mentee" else SURFACE, fg="white" if mode=="mentee" else TEXT2, relief="flat", padx=14, pady=7, cursor="hand2", command=lambda: self._switch_mode("mentee")).pack(side="left")

        if action == "register":
            name_frame = tk.Frame(wrapper, bg=BG); name_frame.pack(fill="x", pady=(0, 12))
            lf = tk.Frame(name_frame, bg=BG); lf.pack(side="left", fill="x", expand=True, padx=(0,4))
            tk.Label(lf, text="First Name", font=FONT_XS, fg=TEXT2, bg=BG).pack(anchor="w", pady=(0,3))
            lf_inner = tk.Frame(lf, bg=BG3, padx=2, pady=2); lf_inner.pack(fill="x")
            tk.Entry(lf_inner, textvariable=self._fname_v, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0).pack(fill="x", ipady=8, ipadx=10)
            rf = tk.Frame(name_frame, bg=BG); rf.pack(side="left", fill="x", expand=True, padx=(4,0))
            tk.Label(rf, text="Last Name", font=FONT_XS, fg=TEXT2, bg=BG).pack(anchor="w", pady=(0,3))
            rf_inner = tk.Frame(rf, bg=BG3, padx=2, pady=2); rf_inner.pack(fill="x")
            tk.Entry(rf_inner, textvariable=self._lname_v, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0).pack(fill="x", ipady=8, ipadx=10)

        tk.Label(wrapper, text="Email Address", font=FONT_XS, fg=TEXT2, bg=BG).pack(anchor="w", pady=(0,3))
        email_frame = tk.Frame(wrapper, bg=BG3, padx=2, pady=2); email_frame.pack(fill="x", pady=(0,12), ipadx=2)
        tk.Entry(email_frame, textvariable=self._email_v, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, width=32).pack(fill="x", ipady=8, ipadx=10)

        tk.Label(wrapper, text="Password", font=FONT_XS, fg=TEXT2, bg=BG).pack(anchor="w", pady=(0,3))
        pw_frame = tk.Frame(wrapper, bg=BG3, padx=2, pady=2); pw_frame.pack(fill="x", pady=(0,6), ipadx=2)
        pw_entry = tk.Entry(pw_frame, textvariable=self._pw_v, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, show="•", width=32)
        pw_entry.pack(fill="x", ipady=8, ipadx=10)
        
        if action == "login": pw_entry.bind("<Return>", lambda e: self._do_login())
        else: pw_entry.bind("<Return>", lambda e: self._do_register())

        self._err_lbl = tk.Label(wrapper, textvariable=self._err_var, font=FONT_XS, fg=CORAL, bg=BG)
        self._err_lbl.pack(anchor="w", pady=(0,8))

        btn_text = f"  Sign in as {title.split()[0]}  →" if action == "login" else "  Create Account  →"
        btn_cmd  = self._do_login if action == "login" else self._do_register
        tk.Button(wrapper, text=btn_text, font=FONT_BOLD, bg=accent, fg="white" if mode=="mentee" else "#1a1614", relief="flat", padx=16, pady=10, cursor="hand2", activebackground=GOLD2 if mode=="mentor" else BLUE2, command=btn_cmd).pack(fill="x", pady=(4,10))

        switch_text = "Don't have an account? Create one" if action == "login" else "Already have an account? Sign in"
        switch_cmd  = "register" if action == "login" else "login"
        tk.Button(wrapper, text=switch_text, font=FONT_XS, bg=BG, fg=TEXT2, relief="flat", cursor="hand2", activebackground=BG, activeforeground=TEXT, command=lambda: self._switch_action(switch_cmd)).pack()

        tk.Label(wrapper, text="─── or ───", font=FONT_XS, fg=TEXT3, bg=BG).pack(pady=10)
        tk.Button(wrapper, text=" Continue as Admin (no login) ", font=FONT_XS, bg=SURFACE, fg=TEXT2, relief="flat", padx=10, pady=6, cursor="hand2", command=lambda: self.on_login(None)).pack()

    def _switch_mode(self, mode):
        self._mode.set(mode); self._err_var.set(""); self._build_right(self._right_panel)

    def _switch_action(self, action):
        self._action.set(action); self._err_var.set(""); self._build_right(self._right_panel)

    def _do_login(self):
        email = self._email_v.get().strip().lower(); pw = self._pw_v.get().strip(); mode = self._mode.get()
        if not email or not pw: return self._err_var.set("⚠  Please enter email and password.")
        allowed_types = ["mentor"] if mode == "mentor" else ["mentee", "student"]
        match = next((p for p in self.people if p.get("email","").lower() == email and p.get("password","") == pw and p.get("type", "") in allowed_types), None)
        if match is None: return self._err_var.set("⚠  Invalid credentials or wrong portal.")
        self.on_login(match)

    def _do_register(self):
        fname = self._fname_v.get().strip(); lname = self._lname_v.get().strip()
        email = self._email_v.get().strip().lower(); pw = self._pw_v.get().strip(); mode = self._mode.get()
        if not fname or not lname or not email or not pw: return self._err_var.set("⚠  Please fill in all required fields.")
        if any(p.get("email", "").lower() == email for p in self.people): return self._err_var.set("⚠  Email already exists. Please sign in.")
        new_user = { "id": str(uuid.uuid4()), "type": mode, "avatar": "👤", "fname": fname, "lname": lname, "role": f"New {mode.capitalize()}", "email": email, "phone": "", "location": "Global", "linkedin": "", "skills": "Ready to learn", "bio": "I am new here!", "goal": "Grow and succeed.", "category": "Other", "badge": "New", "exp": "N/A", "rating": 0, "sessions": 0, "status": "active", "avail": "Flexible", "institution": "", "joined": datetime.now().strftime("%Y-%m-%d"), "color": GOLD if mode == "mentor" else BLUE, "password": pw }
        self.people.append(new_user)
        save_people(self.people)
        self.on_login(new_user)


# ══════════════════════════════════════════════════════════════════════════════
#  MESSAGING (1-ON-1 AND GROUPS)
# ══════════════════════════════════════════════════════════════════════════════
class MessagingPage(tk.Frame):
    POLL_MS = 1500

    def __init__(self, master, current_user, people, messages_ref, save_msg_fn, groups_ref, save_grp_fn, toast_fn):
        super().__init__(master, bg=BG)
        self.current_user  = current_user
        self.people        = people
        self.messages      = messages_ref
        self.save_msg_fn   = save_msg_fn
        self.groups        = groups_ref
        self.save_grp_fn   = save_grp_fn
        self.toast_fn      = toast_fn
        self._active_conv  = None
        self._conv_buttons = {}
        self._after_id     = None
        self._build()
        self._poll()

    def destroy(self):
        if self._after_id: self.after_cancel(self._after_id)
        super().destroy()

    def _build(self):
        self._sidebar = tk.Frame(self, bg=BG2, width=280)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        sb_hdr = tk.Frame(self._sidebar, bg=BG2)
        sb_hdr.pack(fill="x", padx=14, pady=(14,6))
        tk.Label(sb_hdr, text="💬  Messages", font=FONT_H2, fg=TEXT, bg=BG2).pack(side="left")

        # Mentors can create both 1-to-1s and Groups
        tk.Button(sb_hdr, text=" + New ", font=FONT_XS, bg=GOLD, fg="#1a1614", relief="flat", padx=8, pady=4, cursor="hand2", command=self._new_conv_dialog).pack(side="right")
        if self.current_user.get("type") == "mentor":
            tk.Button(sb_hdr, text=" + Group ", font=FONT_XS, bg=BLUE, fg="white", relief="flat", padx=8, pady=4, cursor="hand2", command=self._new_group_dialog).pack(side="right", padx=(0,4))

        tk.Frame(self._sidebar, bg=BORDER, height=1).pack(fill="x", padx=10)

        self._conv_list_frame = tk.Frame(self._sidebar, bg=BG2)
        self._conv_list_frame.pack(fill="both", expand=True)
        self._refresh_conv_list()

        self._chat_area = tk.Frame(self, bg=BG)
        self._chat_area.pack(side="left", fill="both", expand=True)
        self._show_empty_state()

    def _show_empty_state(self):
        for w in self._chat_area.winfo_children(): w.destroy()
        wrapper = tk.Frame(self._chat_area, bg=BG); wrapper.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(wrapper, text="💬", font=("Helvetica",48), bg=BG).pack()
        tk.Label(wrapper, text="Select a conversation", font=FONT_H2, fg=TEXT, bg=BG).pack()
        tk.Label(wrapper, text="or start a new one with the buttons on the left.", font=FONT_SM, fg=TEXT2, bg=BG).pack(pady=4)

    def _refresh_conv_list(self):
        for w in self._conv_list_frame.winfo_children(): w.destroy()
        self._conv_buttons.clear()

        uid = self.current_user.get("id")
        my_items = []
        
        # 1. Gather 1-on-1 Messages
        for key, msgs in self.messages.items():
            ids = key.split("|")
            if uid in ids:
                other_id = ids[0] if ids[1] == uid else ids[1]
                last_msg = msgs[-1] if msgs else None
                ts = last_msg["ts"] if last_msg else ""
                my_items.append({"type": "1v1", "id": other_id, "last_msg": last_msg, "ts": ts})

        # 2. Gather Group Messages
        for g in self.groups:
            if uid in g.get("members", []):
                msgs = g.get("messages", [])
                last_msg = msgs[-1] if msgs else None
                ts = last_msg["ts"] if last_msg else ""
                my_items.append({"type": "group", "group": g, "last_msg": last_msg, "ts": ts})

        if not my_items:
            tk.Label(self._conv_list_frame, text="No conversations yet.\nClick + New to start.", font=FONT_XS, fg=TEXT3, bg=BG2, justify="center").pack(pady=30, padx=14)
            return

        # Sort all conversations by latest message timestamp
        my_items.sort(key=lambda x: x["ts"], reverse=True)

        for item in my_items:
            if item["type"] == "1v1":
                other = next((p for p in self.people if p.get("id") == item["id"]), None)
                if other: self._render_sidebar_btn(other.get("id"), other.get("avatar","👤"), f"{other.get('fname')} {other.get('lname')}", item["last_msg"], is_group=False)
            else:
                g = item["group"]
                self._render_sidebar_btn(g["id"], "👥", g.get("name", "Group Chat"), item["last_msg"], is_group=True)

    def _render_sidebar_btn(self, conv_id, icon, title, last_msg, is_group):
        is_active = (self._active_conv == conv_id)
        bg = SURFACE if is_active else BG2

        btn_frame = tk.Frame(self._conv_list_frame, bg=bg, cursor="hand2")
        btn_frame.pack(fill="x", pady=1)
        self._conv_buttons[conv_id] = btn_frame

        uid = self.current_user.get("id")
        unread = 0
        if not is_group:
            key = conv_key(uid, conv_id)
            msgs = self.messages.get(key, [])
            unread = sum(1 for m in msgs if m.get("sender") != uid and not m.get("read", False))
        else:
            # Simple unread indicator for groups (if last message isn't from me)
            if last_msg and last_msg.get("sender") != uid and not is_active:
                unread = 1 

        av = tk.Label(btn_frame, text=icon, font=("Helvetica",18), bg=bg, width=3)
        av.pack(side="left", padx=(8,4), pady=10)
        info = tk.Frame(btn_frame, bg=bg)
        info.pack(side="left", fill="x", expand=True)
        name_row = tk.Frame(info, bg=bg); name_row.pack(fill="x")
        tk.Label(name_row, text=title[:18] + (".." if len(title)>18 else ""), font=FONT_BOLD, fg=TEXT, bg=bg, anchor="w").pack(side="left")
        
        if is_group:
            tk.Label(name_row, text="Group", font=FONT_XS, fg=BLUE, bg=bg).pack(side="right", padx=8)

        preview = ""
        if last_msg:
            preview = last_msg.get("text","")[:35] + ("…" if len(last_msg.get("text","")) > 35 else "")
        tk.Label(info, text=preview, font=FONT_XS, fg=TEXT3, bg=bg, anchor="w").pack(anchor="w")

        if unread > 0 and not is_group:
            badge = tk.Label(btn_frame, text=str(unread), font=FONT_XS, bg=CORAL, fg="white", padx=5, pady=1)
            badge.pack(side="right", padx=8)
        elif unread > 0 and is_group:
            badge = tk.Label(btn_frame, text="New", font=FONT_XS, bg=BLUE, fg="white", padx=5, pady=1)
            badge.pack(side="right", padx=8)

        for w in [btn_frame, av, info, name_row]:
            w.bind("<Button-1>", lambda e, cid=conv_id: self._open_conversation(cid))
            w.bind("<Enter>",    lambda e, f=btn_frame: f.configure(bg=BG3))
            w.bind("<Leave>",    lambda e, f=btn_frame, b=bg: f.configure(bg=b))

    def _open_conversation(self, conv_id):
        self._active_conv = conv_id
        uid = self.current_user.get("id")
        
        if conv_id.startswith("grp_"):
            self._refresh_conv_list()
            self._render_chat_area(conv_id, is_group=True)
        else:
            key = conv_key(uid, conv_id)
            for m in self.messages.get(key, []):
                if m.get("sender") != uid: m["read"] = True
            self.save_msg_fn(self.messages)
            self._refresh_conv_list()
            self._render_chat_area(conv_id, is_group=False)

    def _render_chat_area(self, conv_id, is_group):
        for w in self._chat_area.winfo_children(): w.destroy()

        hdr = tk.Frame(self._chat_area, bg=BG2); hdr.pack(fill="x")
        
        if is_group:
            g = next((gr for gr in self.groups if gr["id"] == conv_id), None)
            if not g: return
            tk.Frame(hdr, bg=BLUE, width=4).pack(side="left", fill="y")
            tk.Label(hdr, text="👥", font=("Helvetica",22), bg=BG2, padx=10).pack(side="left", pady=10)
            meta = tk.Frame(hdr, bg=BG2); meta.pack(side="left", fill="y", pady=8)
            tk.Label(meta, text=g.get("name","Group Chat"), font=FONT_BOLD, fg=TEXT, bg=BG2).pack(anchor="w")
            tk.Label(meta, text=f"{len(g.get('members',[]))} members", font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w")
        else:
            other = next((p for p in self.people if p.get("id") == conv_id), None)
            if not other: return
            tk.Frame(hdr, bg=other.get("color", GOLD), width=4).pack(side="left", fill="y")
            tk.Label(hdr, text=other.get("avatar","👤"), font=("Helvetica",22), bg=BG2, padx=10).pack(side="left", pady=10)
            meta = tk.Frame(hdr, bg=BG2); meta.pack(side="left", fill="y", pady=8)
            tk.Label(meta, text=f"{other.get('fname','')} {other.get('lname','')}", font=FONT_BOLD, fg=TEXT, bg=BG2).pack(anchor="w")
            tk.Label(meta, text=other.get("role",""), font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w")
            tk.Label(hdr, text="● Online", font=FONT_XS, fg=SAGE2, bg=BG2).pack(side="right", padx=16)

        tk.Frame(self._chat_area, bg=BORDER, height=1).pack(fill="x")

        self._msg_canvas = tk.Canvas(self._chat_area, bg=BG, highlightthickness=0)
        msg_sb = ttk.Scrollbar(self._chat_area, orient="vertical", command=self._msg_canvas.yview)
        self._msg_canvas.configure(yscrollcommand=msg_sb.set)
        msg_sb.pack(side="right", fill="y")
        self._msg_canvas.pack(side="top", fill="both", expand=True)

        self._msg_inner = tk.Frame(self._msg_canvas, bg=BG)
        self._msg_wid = self._msg_canvas.create_window((0,0), window=self._msg_inner, anchor="nw")
        self._msg_canvas.bind("<Configure>", lambda e: self._msg_canvas.itemconfig(self._msg_wid, width=e.width))
        self._msg_inner.bind("<Configure>", lambda e: self._msg_canvas.configure(scrollregion=self._msg_canvas.bbox("all")))

        self._render_messages(conv_id, is_group)

        inp_frame = tk.Frame(self._chat_area, bg=BG2, pady=10); inp_frame.pack(fill="x", side="bottom")
        tk.Frame(inp_frame, bg=BORDER, height=1).pack(fill="x", pady=(0,8))
        row = tk.Frame(inp_frame, bg=BG2); row.pack(fill="x", padx=14)
        self._msg_entry = tk.Entry(row, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0)
        self._msg_entry.pack(side="left", fill="x", expand=True, ipady=9, ipadx=10)
        self._msg_entry.bind("<Return>", lambda e: self._send_message(conv_id, is_group))
        self._msg_entry.focus_set()

        accent_col = BLUE if is_group else (other.get("color", GOLD) if not is_group else GOLD)
        tk.Button(row, text=" Send ↑ ", font=FONT_BOLD, bg=accent_col, fg="white" if accent_col in (BLUE, PURPLE) else "#1a1614",
                  relief="flat", padx=12, pady=8, cursor="hand2", command=lambda: self._send_message(conv_id, is_group)).pack(side="right", padx=(8,0))

    def _render_messages(self, conv_id, is_group):
        for w in self._msg_inner.winfo_children(): w.destroy()

        uid = self.current_user.get("id")
        if is_group:
            g = next((gr for gr in self.groups if gr["id"] == conv_id), None)
            msgs = g.get("messages", []) if g else []
        else:
            key = conv_key(uid, conv_id)
            msgs = self.messages.get(key, [])

        if not msgs:
            tk.Label(self._msg_inner, text="No messages yet. Say hello! 👋", font=FONT_SM, fg=TEXT3, bg=BG).pack(pady=40)
        else:
            prev_date = None
            for msg in msgs:
                ts = msg.get("ts", "")
                try:
                    dt = datetime.fromisoformat(ts)
                    date_str = dt.strftime("%B %d, %Y")
                    time_str = dt.strftime("%I:%M %p")
                except Exception:
                    date_str = ts[:10]; time_str = ts[11:16]

                if date_str != prev_date:
                    sep = tk.Frame(self._msg_inner, bg=BG); sep.pack(fill="x", pady=8, padx=20)
                    tk.Frame(sep, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=6)
                    tk.Label(sep, text=f"  {date_str}  ", font=FONT_XS, fg=TEXT3, bg=BG).pack(side="left")
                    tk.Frame(sep, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, pady=6)
                    prev_date = date_str

                is_mine = (msg.get("sender") == uid)
                sender_name = None
                if is_group and not is_mine:
                    sender_p = next((p for p in self.people if p.get("id") == msg.get("sender")), None)
                    if sender_p: sender_name = f"{sender_p.get('fname')} {sender_p.get('lname')}"
                
                self._msg_bubble(self._msg_inner, msg.get("text",""), time_str, is_mine, sender_name)

        self._msg_inner.update_idletasks()
        self._msg_canvas.configure(scrollregion=self._msg_canvas.bbox("all"))
        self._msg_canvas.yview_moveto(1.0)

    def _msg_bubble(self, parent, text, time_str, is_mine, sender_name=None):
        outer = tk.Frame(parent, bg=BG); outer.pack(fill="x", padx=16, pady=3)

        if is_mine:
            bubble_bg = SURFACE; bubble_fg = TEXT; anchor_side = "right"; time_anchor = "e"
        else:
            bubble_bg = BG2; bubble_fg = TEXT; anchor_side = "left"; time_anchor = "w"

        bubble = tk.Frame(outer, bg=bubble_bg, padx=12, pady=8)
        bubble.pack(side=anchor_side)

        if sender_name:
            tk.Label(bubble, text=sender_name, font=FONT_XS, fg=GOLD, bg=bubble_bg, anchor="w").pack(anchor="w", pady=(0,2))

        tk.Label(bubble, text=text, font=FONT_BODY, fg=bubble_fg, bg=bubble_bg, wraplength=360, justify="left", anchor="w").pack(anchor="w")
        tk.Label(bubble, text=time_str, font=FONT_XS, fg=TEXT3, bg=bubble_bg, anchor=time_anchor).pack(anchor=time_anchor, pady=(2,0))

    def _send_message(self, conv_id, is_group):
        text = self._msg_entry.get().strip()
        if not text: return
        self._msg_entry.delete(0, tk.END)

        uid = self.current_user.get("id")
        new_msg = {
            "id": str(uuid.uuid4()),
            "sender": uid,
            "text": text,
            "ts": datetime.now().isoformat(),
            "read": False
        }

        if is_group:
            g = next((gr for gr in self.groups if gr["id"] == conv_id), None)
            if g:
                if "messages" not in g: g["messages"] = []
                g["messages"].append(new_msg)
                self.save_grp_fn(self.groups)
        else:
            key = conv_key(uid, conv_id)
            if key not in self.messages: self.messages[key] = []
            self.messages[key].append(new_msg)
            self.save_msg_fn(self.messages)

        self._render_messages(conv_id, is_group)
        self._refresh_conv_list()

    def _new_conv_dialog(self):
        win = tk.Toplevel(self); win.title("New Conversation"); win.geometry("420x480"); win.configure(bg=BG2); win.grab_set()
        tk.Frame(win, bg=GOLD, height=4).pack(fill="x")
        tk.Label(win, text="Start a Conversation", font=FONT_H2, fg=TEXT, bg=BG2).pack(pady=(14,4), padx=20, anchor="w")

        uid = self.current_user.get("id"); utype = self.current_user.get("type")
        if utype == "mentor":
            targets = [p for p in self.people if p.get("type") in ("mentee","student") and p.get("id") != uid]
            tk.Label(win, text="Choose a mentee or student to message:", font=FONT_SM, fg=TEXT2, bg=BG2).pack(padx=20, anchor="w", pady=(0,8))
        else:
            targets = [p for p in self.people if p.get("type") == "mentor" and p.get("id") != uid]
            tk.Label(win, text="Choose a mentor to message:", font=FONT_SM, fg=TEXT2, bg=BG2).pack(padx=20, anchor="w", pady=(0,8))

        _, inner = scrollable(win, bg=BG2)
        if not targets:
            tk.Label(inner, text="No valid users found.", font=FONT_SM, fg=TEXT3, bg=BG2).pack(pady=20); return

        def start(person):
            win.destroy()
            key = conv_key(uid, person.get("id"))
            if key not in self.messages: self.messages[key] = []; self.save_msg_fn(self.messages)
            self._open_conversation(person.get("id"))

        for p in targets:
            row = tk.Frame(inner, bg=BG3, cursor="hand2", pady=8, padx=12); row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text=p.get("avatar","👤"), font=("Helvetica",18), bg=BG3).pack(side="left", padx=(0,8))
            info = tk.Frame(row, bg=BG3); info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=f"{p.get('fname','')} {p.get('lname','')}", font=FONT_BOLD, fg=TEXT, bg=BG3).pack(anchor="w")
            tk.Label(info, text=p.get("role",""), font=FONT_XS, fg=TEXT2, bg=BG3).pack(anchor="w")
            tk.Button(row, text=" Chat → ", font=FONT_XS, bg=p.get("color",GOLD), fg="#1a1614", relief="flat", padx=8, pady=4, cursor="hand2", command=lambda pp=p: start(pp)).pack(side="right")
            for w in (row, info):
                w.bind("<Button-1>", lambda e, pp=p: start(pp)); w.bind("<Enter>", lambda e, r=row: r.configure(bg=SURFACE)); w.bind("<Leave>", lambda e, r=row: r.configure(bg=BG3))

    def _new_group_dialog(self):
        win = tk.Toplevel(self); win.title("Create New Group"); win.geometry("420x520"); win.configure(bg=BG2); win.grab_set()
        tk.Frame(win, bg=BLUE, height=4).pack(fill="x")
        tk.Label(win, text="Create a Group Chat", font=FONT_H2, fg=TEXT, bg=BG2).pack(pady=(14,4), padx=20, anchor="w")
        
        tk.Label(win, text="Group Name:", font=FONT_XS, fg=TEXT2, bg=BG2).pack(padx=20, anchor="w", pady=(4,2))
        name_var = tk.StringVar()
        tk.Entry(win, textvariable=name_var, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0).pack(fill="x", padx=20, ipady=8, ipadx=10)

        tk.Label(win, text="Select Mentees to Add:", font=FONT_XS, fg=TEXT2, bg=BG2).pack(padx=20, anchor="w", pady=(12,4))
        
        _, inner = scrollable(win, bg=BG2)
        uid = self.current_user.get("id")
        targets = [p for p in self.people if p.get("type") in ("mentee","student") and p.get("id") != uid]
        
        if not targets:
            tk.Label(inner, text="No mentees available to add.", font=FONT_SM, fg=TEXT3, bg=BG2).pack(pady=20)
        
        cb_vars = {}
        for p in targets:
            var = tk.BooleanVar()
            cb_vars[p["id"]] = var
            cb = tk.Checkbutton(inner, text=f"{p.get('fname')} {p.get('lname')} - {p.get('role')}", variable=var, bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2, activeforeground=TEXT, font=FONT_BODY)
            cb.pack(anchor="w", padx=16, pady=4)

        def create_group():
            g_name = name_var.get().strip()
            selected = [pid for pid, v in cb_vars.items() if v.get()]
            if not g_name:
                return messagebox.showerror("Missing Name", "Please enter a group name.", parent=win)
            if not selected:
                return messagebox.showerror("No Members", "Please select at least one mentee.", parent=win)
            
            new_grp = {
                "id": "grp_" + str(uuid.uuid4()),
                "mentor_id": uid,
                "name": g_name,
                "members": [uid] + selected,
                "messages": []
            }
            self.groups.append(new_grp)
            self.save_grp_fn(self.groups)
            self.toast_fn(f"Group '{g_name}' created!")
            win.destroy()
            self._open_conversation(new_grp["id"])

        btm = tk.Frame(win, bg=BG2); btm.pack(side="bottom", fill="x", pady=14, padx=20)
        outline_btn(btm, " Cancel ", win.destroy).pack(side="left")
        tk.Button(btm, text=" Create Group ✓ ", font=FONT_BOLD, bg=BLUE, fg="white", relief="flat", padx=12, pady=6, cursor="hand2", command=create_group).pack(side="right")

    def _poll(self):
        if self._active_conv:
            self._refresh_conv_list()
        self._after_id = self.after(self.POLL_MS, self._poll)


# ══════════════════════════════════════════════════════════════════════════════
#  PERSON FORM  (Add / Edit / Delete)
# ══════════════════════════════════════════════════════════════════════════════
class PersonForm(tk.Toplevel):
    TYPE_COLORS = {"mentor": GOLD, "mentee": BLUE, "student": PURPLE}
    TYPE_LABELS = {"mentor": "Mentor", "mentee": "Mentee", "student": "Student"}

    def __init__(self, master, person_type=None, existing=None, on_save=None):
        super().__init__(master)
        self.on_save  = on_save
        self.existing = existing
        self.is_edit  = existing is not None
        self.ptype    = existing.get("type", person_type) if existing else person_type
        self.accent   = self.TYPE_COLORS.get(self.ptype, GOLD)

        mode = "Edit" if self.is_edit else "Add New"
        tlabel = self.TYPE_LABELS.get(self.ptype, "Person")
        self.title(f"{mode} {tlabel}")
        self.geometry("580x680")
        self.configure(bg=BG2)
        self.grab_set()
        self.resizable(True, True)

        tk.Frame(self, bg=self.accent, height=4).pack(fill="x")
        tk.Label(self, text=f"{mode} {tlabel}", font=FONT_H1, fg=TEXT, bg=BG2).pack(pady=(14,2), padx=24, anchor="w")
        sub = "Update the existing record." if self.is_edit else f"Register a new {tlabel.lower()} on Mentee-SAP."
        tk.Label(self, text=sub, font=FONT_XS, fg=TEXT2, bg=BG2).pack(padx=24, anchor="w", pady=(0,8))

        _, self.form = scrollable(self, bg=BG2)
        self.entries = {}
        self._sel_av = tk.StringVar(value=existing.get("avatar", AVATARS[0]) if existing else AVATARS[0])
        self._build_form()

        bar = tk.Frame(self, bg=BG2)
        bar.pack(side="bottom", fill="x", padx=24, pady=14)
        if self.is_edit:
            danger_btn(bar, " 🗑  Delete ", self._do_delete).pack(side="left")
        outline_btn(bar, " Cancel ", self.destroy).pack(side="right", padx=(8, 0))
        gold_btn(bar, " Save ✓ ", self._do_save).pack(side="right")

    def _build_form(self):
        f  = self.form
        ex = self.existing or {}

        def field(parent, lbl, key, default=""):
            tk.Label(parent, text=lbl, font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8, 2))
            e = tk.Entry(parent, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0)
            e.pack(fill="x", padx=24, ipady=6, ipadx=8)
            e.insert(0, ex.get(key, default))
            self.entries[key] = e

        def textarea(parent, lbl, key, default="", h=3):
            tk.Label(parent, text=lbl, font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8, 2))
            t = tk.Text(parent, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, height=h, wrap="word")
            t.pack(fill="x", padx=24, ipady=4, ipadx=8)
            t.insert("1.0", ex.get(key, default))
            self.entries[key] = t

        def combo(parent, lbl, key, values, default=""):
            tk.Label(parent, text=lbl, font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8, 2))
            var = tk.StringVar(value=ex.get(key, default or values[0]))
            cb = ttk.Combobox(parent, textvariable=var, values=values, state="readonly")
            cb.pack(fill="x", padx=24, ipady=4)
            self.entries[key] = var

        def two(build_l, build_r):
            row = tk.Frame(f, bg=BG2)
            row.pack(fill="x")
            l = tk.Frame(row, bg=BG2); l.pack(side="left", fill="x", expand=True)
            r = tk.Frame(row, bg=BG2); r.pack(side="left", fill="x", expand=True)
            build_l(l); build_r(r)

        def section(title):
            row = tk.Frame(f, bg=BG2)
            row.pack(fill="x", padx=24, pady=(14, 0))
            tk.Label(row, text=title, font=FONT_BOLD, fg=self.accent, bg=BG2).pack(side="left")
            tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=6)

        section("👤  Identity")
        tk.Label(f, text="Avatar", font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8, 4))
        av_row = tk.Frame(f, bg=BG2)
        av_row.pack(anchor="w", padx=24)
        self._av_btns = []
        for av in AVATARS:
            sel = av == self._sel_av.get()
            b = tk.Button(av_row, text=av, font=("Helvetica", 15), bg=self.accent if sel else BG3,
                          fg="#1a1614" if sel else TEXT, width=2, relief="flat", cursor="hand2")
            b.configure(command=lambda v=av: self._pick_av(v))
            b.pack(side="left", padx=2, pady=2)
            self._av_btns.append(b)

        two(lambda p: field(p, "First Name *", "fname"), lambda p: field(p, "Last Name *",  "lname"))
        field(f, "Role / Title *", "role", default={"mentor":"Mentor","mentee":"Mentee","student":"Student"}.get(self.ptype,""))
        two(lambda p: field(p, "Email", "email"), lambda p: field(p, "Phone (+1...)", "phone"))
        two(lambda p: field(p, "Location", "location"), lambda p: field(p, "LinkedIn", "linkedin"))

        section("📋  Details")
        cats = ["Engineering","Product","Design","Data & AI","Startup","Finance","Education","Other"]
        combo(f, "Category", "category", cats, default=ex.get("category","Engineering"))

        if self.ptype == "student":
            two(lambda p: combo(p, "Year / Level", "exp", ["Fresher","1st Year","2nd Year","3rd Year","4th Year","Postgrad","PhD"], default=ex.get("exp","Fresher")),
                lambda p: field(p, "Institution", "institution", default=ex.get("institution","")))
        else:
            two(lambda p: field(p, "Experience", "exp", default=ex.get("exp","1 yr")),
                lambda p: combo(p, "Status", "status", ["active","inactive","on-leave"], default=ex.get("status","active")))

        field(f, "Skills (comma separated)", "skills", default=ex.get("skills",""))
        textarea(f, "Bio / About", "bio", default=ex.get("bio",""))
        field(f, "Goal", "goal", default=ex.get("goal",""))

        section("🔑  Login Credentials")
        field(f, "Password (for login)", "password", default=ex.get("password",""))

        if self.ptype == "mentor":
            two(lambda p: field(p, "Sessions Completed", "sessions", default=str(ex.get("sessions", 0))),
                lambda p: field(p, "Rating (0–5)", "rating", default=str(ex.get("rating", 0.0))))

        combo(f, "Availability", "avail", ["Weekends only","Evenings (6–10 PM)","Flexible","Full-time available"], default=ex.get("avail","Flexible"))
        tk.Frame(f, height=20, bg=BG2).pack()

    def _pick_av(self, val):
        self._sel_av.set(val)
        for b in self._av_btns:
            sel = b.cget("text") == val
            b.configure(bg=self.accent if sel else BG3, fg="#1a1614" if sel else TEXT)

    def _gv(self, key):
        w = self.entries.get(key)
        if w is None: return ""
        if isinstance(w, tk.StringVar): return w.get()
        if isinstance(w, tk.Text): return w.get("1.0", tk.END).strip()
        return w.get().strip()

    def _do_save(self):
        fname = self._gv("fname")
        lname = self._gv("lname")
        role  = self._gv("role")
        if not fname or not lname or not role:
            messagebox.showerror("Required Fields", "First Name, Last Name and Role are required.", parent=self)
            return
        type_colors = {"mentor":GOLD,"mentee":BLUE,"student":PURPLE}
        record = {
            "id":          self.existing["id"] if self.is_edit else str(uuid.uuid4()),
            "type":        self.ptype,
            "avatar":      self._sel_av.get(),
            "fname":       fname, "lname": lname, "role": role,
            "email":       self._gv("email"), "phone": self._gv("phone"),
            "location":    self._gv("location"), "linkedin": self._gv("linkedin"),
            "category":    self._gv("category"), "skills": self._gv("skills"),
            "bio":         self._gv("bio"), "goal": self._gv("goal"),
            "avail":       self._gv("avail"),
            "status":      self._gv("status") or "active",
            "exp":         self._gv("exp") or "N/A",
            "institution": self._gv("institution"),
            "password":    self._gv("password") or (self.existing.get("password","") if self.is_edit else ""),
            "sessions":    int(self._gv("sessions") or 0) if self.ptype=="mentor" else (self.existing.get("sessions",0) if self.is_edit else 0),
            "rating":      float(self._gv("rating") or 0) if self.ptype=="mentor" else (self.existing.get("rating",0) if self.is_edit else 0),
            "badge":       {"mentor":"Mentor","mentee":"Active","student":"Student"}[self.ptype],
            "color":       type_colors[self.ptype],
            "joined":      self.existing.get("joined", datetime.now().strftime("%Y-%m-%d")) if self.is_edit else datetime.now().strftime("%Y-%m-%d"),
        }
        if self.on_save:
            self.on_save(record, self.is_edit)
        self.destroy()

    def _do_delete(self):
        name = f"{self.existing.get('fname','')} {self.existing.get('lname','')}"
        if messagebox.askyesno("Confirm Delete", f"Permanently delete {name}?\nThis cannot be undone.", parent=self):
            if self.on_save:
                self.on_save(self.existing, "delete")
            self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  PEOPLE PAGE
# ══════════════════════════════════════════════════════════════════════════════
class PeoplePage(tk.Frame):
    TABS = [("All", None, TEXT2), ("Mentors","mentor",GOLD),
            ("Mentees","mentee",BLUE), ("Students","student",PURPLE)]

    def __init__(self, master, people_ref, save_fn, toast_fn):
        super().__init__(master, bg=BG)
        self.people    = people_ref
        self.save_fn   = save_fn
        self.toast_fn  = toast_fn
        self.cur_type  = None
        self.list_inner = None
        self.stats_bar  = None
        self.search_v   = tk.StringVar()
        self.search_v.trace_add("write", lambda *_: self._refresh())
        self._build()
        self._refresh()

    def _build(self):
        bar = tk.Frame(self, bg=BG)
        bar.pack(fill="x", padx=24, pady=(18, 6))
        tk.Label(bar, text="People Manager", font=FONT_H1, fg=TEXT, bg=BG).pack(side="left")
        btns = tk.Frame(bar, bg=BG)
        btns.pack(side="right")
        for lbl, pt, col in [(" + Student","student",PURPLE),
                               (" + Mentee", "mentee", BLUE),
                               (" + Mentor", "mentor", GOLD)]:
            tk.Button(btns, text=lbl, font=FONT_SM, bg=col, fg="#1a1614" if col==GOLD else "#0d0d0d",
                      relief="flat", padx=10, pady=5, cursor="hand2", command=lambda t=pt: self._add(t)).pack(side="right", padx=4)

        tab_row = tk.Frame(self, bg=BG)
        tab_row.pack(fill="x", padx=24, pady=(4, 0))
        self._tab_btns = {}
        for name, ft, col in self.TABS:
            btn = tk.Button(tab_row, text=name, font=FONT_SM, bg=SURFACE, fg=TEXT2,
                            relief="flat", padx=14, pady=6, cursor="hand2", command=lambda f=ft, n=name: self._set_tab(f, n))
            btn.pack(side="left", padx=3)
            self._tab_btns[name] = (btn, col)
        self._highlight_tab("All")

        srch = tk.Frame(tab_row, bg=BG)
        srch.pack(side="right")
        tk.Label(srch, text="🔍", font=FONT_SM, fg=TEXT3, bg=BG).pack(side="left")
        tk.Entry(srch, textvariable=self.search_v, font=FONT_SM, bg=BG2, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, width=22).pack(side="left", ipady=5, ipadx=8)

        self.stats_bar = tk.Frame(self, bg=BG)
        self.stats_bar.pack(fill="x", padx=24, pady=(8, 4))

        hdr = tk.Frame(self, bg=BG3)
        hdr.pack(fill="x", padx=24)
        for txt, w in [("",3),("Name & Role",26),("Category",13),("Contact / Location",18), ("Type",9),("Joined",10),("Actions",12)]:
            tk.Label(hdr, text=txt, font=FONT_XS, fg=TEXT3, bg=BG3, width=w, anchor="w", padx=6, pady=6).pack(side="left")

        _, self.list_inner = scrollable(self, bg=BG)

    def _highlight_tab(self, name):
        for n, (btn, col) in self._tab_btns.items():
            active = (n == name)
            btn.configure(bg=col if active else SURFACE, fg="#1a1614" if (active and col==GOLD) else "#0d0d0d" if active else TEXT2)

    def _set_tab(self, ftype, name):
        self.cur_type = ftype
        self._highlight_tab(name)
        self._refresh()

    def _refresh(self):
        if self.list_inner is None or self.stats_bar is None: return
        for w in self.list_inner.winfo_children(): w.destroy()
        for w in self.stats_bar.winfo_children(): w.destroy()

        q = self.search_v.get().lower()
        visible = [p for p in self.people
                   if (self.cur_type is None or p.get("type") == self.cur_type)
                   and (not q or q in (p.get("fname","")+" "+p.get("lname","")).lower() or q in p.get("role","").lower()
                        or q in p.get("skills","").lower() or q in p.get("category","").lower()
                        or q in p.get("email","").lower())]

        cnt = {"mentor":0,"mentee":0,"student":0}
        for p in self.people: cnt[p.get("type")] = cnt.get(p.get("type"),0)+1
        tk.Label(self.stats_bar, text=f"Total: {len(self.people)}", font=FONT_XS, fg=TEXT2, bg=BG).pack(side="left")
        for lbl, col in [(f"  Mentors: {cnt['mentor']}",GOLD), (f"  Mentees: {cnt['mentee']}",BLUE), (f"  Students: {cnt['student']}",PURPLE)]:
            tk.Label(self.stats_bar, text=lbl, font=FONT_XS, fg=col, bg=BG).pack(side="left")
        if q: tk.Label(self.stats_bar, text=f"  [{len(visible)} matching]", font=FONT_XS, fg=TEXT3, bg=BG).pack(side="left")

        if not visible:
            tk.Label(self.list_inner, text="No active records found. Be the first to register!", font=FONT_BODY, fg=TEXT3, bg=BG).pack(pady=40)
            return
        for i, person in enumerate(visible):
            self._row(self.list_inner, person, i)

    def _row(self, parent, p, idx):
        rbg = BG2 if idx % 2 == 0 else BG
        row = tk.Frame(parent, bg=rbg, cursor="hand2")
        row.pack(fill="x", padx=24, pady=1)
        for w in (row,):
            w.bind("<Enter>", lambda e, r=row: r.configure(bg=BG3))
            w.bind("<Leave>", lambda e, r=row, b=rbg: r.configure(bg=b))
            w.bind("<Button-1>", lambda e, person=p: self._edit(person))

        tk.Frame(row, bg=p.get("color",GOLD), width=4).pack(side="left", fill="y")
        av = tk.Label(row, text=p.get("avatar","👤"), font=("Helvetica",18), bg=rbg, width=3)
        av.pack(side="left", padx=(6,4), pady=8)
        av.bind("<Button-1>", lambda e, person=p: self._edit(person))

        def lbl_bind(w, person=p):
            w.bind("<Button-1>", lambda e, pp=person: self._edit(pp))
            w.bind("<Enter>", lambda e, r=row: r.configure(bg=BG3))
            w.bind("<Leave>", lambda e, r=row, b=rbg: r.configure(bg=b))

        nf = tk.Frame(row, bg=rbg, width=200, height=48); nf.pack(side="left", padx=4, pady=6); nf.pack_propagate(False)
        nm = tk.Label(nf, text=f"{p.get('fname','')} {p.get('lname','')}", font=FONT_BOLD, fg=TEXT, bg=rbg, anchor="w"); nm.pack(anchor="w")
        rl = tk.Label(nf, text=p.get("role","")[:38], font=FONT_XS, fg=TEXT2, bg=rbg, anchor="w"); rl.pack(anchor="w")
        for w in (nf, nm, rl): lbl_bind(w)

        cf = tk.Frame(row, bg=rbg, width=105, height=48); cf.pack(side="left", padx=4); cf.pack_propagate(False)
        c = tk.Label(cf, text=p.get("category","—"), font=FONT_XS, fg=TEXT2, bg=rbg); c.pack(anchor="w", pady=8)
        lbl_bind(c)

        cof = tk.Frame(row, bg=rbg, width=145, height=48); cof.pack(side="left", padx=4); cof.pack_propagate(False)
        em = tk.Label(cof, text=p.get("email","—") or "—", font=FONT_XS, fg=TEXT2, bg=rbg); em.pack(anchor="w", pady=(8,0))
        lo = tk.Label(cof, text=p.get("location","") or "", font=FONT_XS, fg=TEXT3, bg=rbg); lo.pack(anchor="w")
        for w in (cof, em, lo): lbl_bind(w)

        tf = tk.Frame(row, bg=rbg, width=75, height=48); tf.pack(side="left", padx=4); tf.pack_propagate(False)
        t = tk.Label(tf, text=p.get("type","").capitalize(), font=FONT_XS, fg=p.get("color",GOLD), bg=rbg); t.pack(anchor="w", pady=8)
        lbl_bind(t)

        jf = tk.Frame(row, bg=rbg, width=78, height=48); jf.pack(side="left", padx=4); jf.pack_propagate(False)
        j = tk.Label(jf, text=p.get("joined","—"), font=FONT_XS, fg=TEXT3, bg=rbg); j.pack(anchor="w", pady=8)
        lbl_bind(j)

        af = tk.Frame(row, bg=rbg)
        af.pack(side="right", padx=10)
        tk.Button(af, text=" ✏ Edit ", font=FONT_XS, bg=SURFACE, fg=TEXT2, relief="flat", padx=6, pady=3, cursor="hand2", command=lambda person=p: self._edit(person)).pack(side="left", padx=2)
        tk.Button(af, text=" 🗑 ", font=FONT_XS, bg="#3a1a1a", fg="#e08080", relief="flat", padx=6, pady=3, cursor="hand2", command=lambda person=p: self._confirm_del(person)).pack(side="left", padx=2)

    def _add(self, ptype):
        PersonForm(self, person_type=ptype, on_save=self._handle)

    def _edit(self, person):
        PersonForm(self, existing=person, on_save=self._handle)

    def _handle(self, record, mode):
        if mode == "delete":
            self.people[:] = [p for p in self.people if p.get("id") != record.get("id")]
            self.toast_fn(f"🗑  {record.get('fname','')} {record.get('lname','')} deleted.")
        elif mode is True:
            for i, p in enumerate(self.people):
                if p.get("id") == record.get("id"):
                    self.people[i] = record
                    break
            self.toast_fn(f"✓  {record.get('fname','')} {record.get('lname','')} updated.")
        else:
            self.people.append(record)
            self.toast_fn(f"✓  {record.get('fname','')} {record.get('lname','')} added as {record.get('type','')}.")
        self.save_fn(self.people)
        self._refresh()

    def _confirm_del(self, person):
        name = f"{person.get('fname','')} {person.get('lname','')}"
        if messagebox.askyesno("Confirm Delete", f"Delete {name}?\nThis cannot be undone."):
            self._handle(person, "delete")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════
class MenteeSAP(tk.Tk):

    def __init__(self):
        super().__init__()
        self.my_profile    = load_my_profile()
        self.people        = load_people()
        self.messages_data = load_messages()
        self.sessions_data = load_sessions()
        self.groups_data   = load_groups() # NEW: Load groups
        self.chat_history  = []
        self.current_user  = None   
        self.title("Mentee-SAP")
        self.geometry("1200x760")
        self.minsize(1000, 640)
        self.configure(bg=BG)
        self._show_login()

    def _show_login(self):
        self._login_page = LoginPage(self, self.people, self._on_login)
        self._login_page.pack(fill="both", expand=True)

    def _on_login(self, user_record):
        self._login_page.pack_forget()
        self._login_page.destroy()
        self.current_user = user_record

        if user_record is None:
            self.current_user = {
                "id": "admin", "type": "mentee",
                "fname": self.my_profile.get("fname", ""),
                "lname": self.my_profile.get("lname", ""),
                "avatar": self.my_profile.get("avatar", "👤"),
                "role": self.my_profile.get("role", "Admin"),
            }

        self._build_nav()
        self._build_pages()
        self._show_page("home")

    def _build_nav(self):
        nav = tk.Frame(self, bg=BG2, height=52)
        nav.pack(fill="x")
        nav.pack_propagate(False)
        tk.Label(nav, text="Mentee", font=("Georgia",17,"bold"), fg=GOLD, bg=BG2).pack(side="left", padx=(18,0))
        tk.Label(nav, text="-SAP", font=("Georgia",17,"italic"), fg=TEXT2, bg=BG2).pack(side="left")
        tabs = tk.Frame(nav, bg=BG3)
        tabs.pack(side="left", padx=18)
        self.nav_btns = {}
        
        u_type = self.current_user.get("type", "mentee")
        if u_type == "mentor":
            nav_items = [("🏠 Home","home"),("👥 People Manager","people"),
                         ("📅 Sessions","sessions"),("💬 Messages","messages"),
                         ("👤 My Profile","profile")]
        else:
            nav_items = [("🏠 Home","home"),("🔍 Find Mentors","mentors"),
                         ("📅 Sessions","sessions"),("💬 Messages","messages"),
                         ("💡 Career Advisor","advisor"),("👤 My Profile","profile")]

        for lbl, key in nav_items:
            btn = tk.Button(tabs, text=lbl, font=FONT_SM, bg=BG3, fg=TEXT2, bd=0, padx=10, pady=7, cursor="hand2",
                            activebackground=SURFACE, activeforeground=TEXT, command=lambda k=key: self._show_page(k))
            btn.pack(side="left", padx=1)
            self.nav_btns[key] = btn

        u = self.current_user
        pill_text = f"  {u.get('avatar','👤')}  {u.get('fname','')} {u.get('lname','A')[0:1]}.  "
        self.nav_pill = tk.Label(nav, text=pill_text, font=FONT_SM, fg=TEXT, bg=SURFACE, padx=6, pady=4)
        self.nav_pill.pack(side="right", padx=4)

        tk.Button(nav, text=" ⏻ Logout ", font=FONT_XS, bg=BG3, fg=TEXT3, relief="flat", padx=8, pady=4, cursor="hand2", command=self._logout).pack(side="right", padx=8)

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            for widget in self.winfo_children():
                widget.destroy()
            self.current_user = None
            self._show_login()

    def _show_page(self, key):
        for k, btn in self.nav_btns.items():
            btn.configure(bg=SURFACE if k==key else BG3, fg=TEXT if k==key else TEXT2)
        for k, frm in self._pages.items():
            frm.pack_forget()
            
        if key in self._pages:
            self._pages[key].pack(fill="both", expand=True)
            if key == "profile":
                self._refresh_profile()
            if key == "mentors":
                self._pages["mentors"].destroy()
                self._pages["mentors"] = self._mk_mentors()
                self._pages["mentors"].pack(fill="both", expand=True)
            if key == "sessions":
                self._pages["sessions"].destroy()
                self._pages["sessions"] = self._mk_sessions()
                self._pages["sessions"].pack(fill="both", expand=True)

    def _build_pages(self):
        self._pages = {
            "home":     self._mk_home(),
            "people":   PeoplePage(self, self.people, save_people, self._toast),
            "mentors":  self._mk_mentors(),
            "sessions": self._mk_sessions(),
            "messages": MessagingPage(self, self.current_user, self.people, self.messages_data, save_messages, self.groups_data, save_groups, self._toast),
            "advisor":  self._mk_advisor(),
            "profile":  self._mk_profile(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    #  HOME
    # ─────────────────────────────────────────────────────────────────────────
    def _mk_home(self):
        frame = tk.Frame(self, bg=BG)
        _, inner = scrollable(frame)

        hero = tk.Frame(inner, bg=BG, pady=24)
        hero.pack(fill="x", padx=60)

        u = self.current_user
        greeting = f"Welcome back, {u.get('fname', 'there')}! 👋"
        if u.get("type") == "mentor":
            sub_text = "Manage your mentees, sessions and messages."
        else:
            sub_text = "Connect with experienced professionals.\nGet personalized career guidance and coaching."

        tk.Label(hero, text=greeting, font=("Georgia",26,"bold"), fg=TEXT, bg=BG).pack(pady=(12, 0))
        tk.Label(hero, text=sub_text, font=FONT_BODY, fg=TEXT2, bg=BG, justify="center").pack(pady=8)
        
        hbtns = tk.Frame(hero, bg=BG)
        hbtns.pack(pady=8)
        if u.get("type") != "mentor":
            gold_btn(hbtns, "  Find Mentors →  ", lambda: self._show_page("mentors")).pack(side="left", padx=6)
            outline_btn(hbtns, "  Advisor  ",    lambda: self._show_page("advisor")).pack(side="left", padx=6)
        else:
            gold_btn(hbtns, "  People Manager →  ", lambda: self._show_page("people")).pack(side="left", padx=6)
            
        outline_btn(hbtns, "  💬 Messages  ", lambda: self._show_page("messages")).pack(side="left", padx=6)

        stats = tk.Frame(inner, bg=BG)
        stats.pack(pady=10, padx=60)
        mentors_n  = sum(1 for p in self.people if p.get("type")=="mentor")
        mentees_n  = sum(1 for p in self.people if p.get("type")=="mentee")
        students_n = sum(1 for p in self.people if p.get("type")=="student")
        for num, lbl, col in [(str(mentors_n),"Registered Mentors",GOLD),
                               (str(mentees_n),"Active Mentees",BLUE),
                               (str(students_n),"Students",PURPLE)]:
            b = tk.Frame(stats, bg=BG2, padx=22, pady=12)
            b.pack(side="left", padx=6)
            tk.Label(b, text=num, font=("Georgia",18,"bold"), fg=col, bg=BG2).pack()
            tk.Label(b, text=lbl, font=FONT_XS, fg=TEXT2, bg=BG2).pack()

        divider(inner)
        tk.Label(inner, text="Upcoming Sessions", font=FONT_H2, fg=TEXT, bg=BG).pack(anchor="w", padx=30, pady=(4,8))
        tk.Label(inner, text="No sessions scheduled. Head to 'Find Mentors' to book one!", font=FONT_SM, fg=TEXT3, bg=BG).pack(anchor="w", padx=30, pady=4)

        if u.get("type") != "mentor":
            divider(inner)
            tk.Label(inner, text="Available Mentors", font=FONT_H2, fg=TEXT, bg=BG).pack(anchor="w", padx=30, pady=(4,8))
            grid = tk.Frame(inner, bg=BG)
            grid.pack(padx=30, fill="x", pady=(0,30))
            featured = [p for p in self.people if p.get("type")=="mentor"][:3]
            
            if not featured:
                tk.Label(grid, text="No mentors have registered yet. Check back soon!", font=FONT_SM, fg=TEXT3, bg=BG).grid(row=0, column=0, sticky="w")
            else:
                for i, m in enumerate(featured):
                    self._mentor_card(grid, m, 0, i)
                for c in range(3):
                    grid.columnconfigure(c, weight=1)
                
        return frame

    # ─────────────────────────────────────────────────────────────────────────
    #  MENTORS
    # ─────────────────────────────────────────────────────────────────────────
    def _mk_mentors(self):
        frame = tk.Frame(self, bg=BG)
        hdr = tk.Frame(frame, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(20,8))
        tk.Label(hdr, text="Find Your Mentor", font=FONT_H1, fg=TEXT, bg=BG).pack(side="left")

        chip_frame = tk.Frame(frame, bg=BG)
        chip_frame.pack(fill="x", padx=30, pady=(0,10))
        self._mchips = {}
        for c in ["All","Engineering","Product","Design","Data & AI","Startup","Finance"]:
            btn = tk.Button(chip_frame, text=c, font=FONT_XS, bg=GOLD if c=="All" else SURFACE, fg="#1a1614" if c=="All" else TEXT2,
                            relief="flat", padx=10, pady=4, cursor="hand2", command=lambda cat=c: self._filter_mentors(cat))
            btn.pack(side="left", padx=3)
            self._mchips[c] = btn

        _, self.mg_inner = scrollable(frame)
        self._render_mentors("All")
        return frame

    def _filter_mentors(self, cat):
        for c, btn in self._mchips.items():
            btn.configure(bg=GOLD if c==cat else SURFACE, fg="#1a1614" if c==cat else TEXT2)
        self._render_mentors(cat)

    def _render_mentors(self, cat):
        for w in self.mg_inner.winfo_children(): w.destroy()
        lst = [p for p in self.people if p.get("type")=="mentor" and (cat=="All" or p.get("category","")==cat)]
        
        if not lst:
            tk.Label(self.mg_inner, text="No mentors match this category yet. Be the first to register as one!", font=FONT_BODY, fg=TEXT3, bg=BG).grid(row=0, column=0, pady=40, padx=30, sticky="w")
            return
            
        cols = 3
        for i, m in enumerate(lst):
            self._mentor_card(self.mg_inner, m, i//cols, i%cols)
        for c in range(cols): self.mg_inner.columnconfigure(c, weight=1)

    def _mentor_card(self, parent, m, row, col):
        card = tk.Frame(parent, bg=BG2, padx=14, pady=12, cursor="hand2")
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        top = tk.Frame(card, bg=BG2); top.pack(fill="x")
        av = tk.Frame(top, bg=BG3, width=48, height=48); av.pack(side="left", padx=(0,10)); av.pack_propagate(False)
        tk.Label(av, text=m.get("avatar","👤"), font=("Helvetica",22), bg=BG3).place(relx=0.5, rely=0.5, anchor="center")
        meta = tk.Frame(top, bg=BG2); meta.pack(side="left", fill="x", expand=True)
        tk.Label(meta, text=f"{m.get('fname','')} {m.get('lname','')}", font=FONT_BOLD, fg=TEXT, bg=BG2).pack(anchor="w")
        tk.Label(meta, text=m.get("role",""), font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w")
        tk.Label(meta, text=f"  {m.get('badge','Mentor')}  ", font=FONT_XS, fg=m.get("color", GOLD), bg=BG2).pack(anchor="w", pady=2)

        tags = tk.Frame(card, bg=BG2); tags.pack(fill="x", pady=(6,4))
        for tag in (m.get("skills","") or "").split(",")[:3]:
            if tag.strip(): tk.Label(tags, text=f" {tag.strip()} ", font=FONT_XS, fg=TEXT2, bg=SURFACE, padx=4, pady=2).pack(side="left", padx=2)

        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", pady=6)
        footer = tk.Frame(card, bg=BG2); footer.pack(fill="x")
        tk.Label(footer, text=f"★ {m.get('rating',0)}  ·  {m.get('sessions',0)} sessions", font=FONT_XS, fg=TEXT2, bg=BG2).pack(side="left")
        btn_f = tk.Frame(footer, bg=BG2); btn_f.pack(side="right")
        tk.Button(btn_f, text=" 💬 Chat ", font=FONT_XS, bg=BLUE, fg="white", relief="flat", padx=6, pady=3, cursor="hand2", command=lambda mn=m: self._start_chat_with(mn)).pack(side="left", padx=2)
        gold_btn(btn_f, " Connect ", lambda mn=m: self._connect_dialog(mn)).pack(side="left")

        for w in [card, top, meta, tags, footer]:
            w.bind("<Enter>", lambda e, c=card: c.configure(bg=BG3))
            w.bind("<Leave>", lambda e, c=card: c.configure(bg=BG2))

    def _start_chat_with(self, mentor):
        uid = self.current_user.get("id")
        key = conv_key(uid, mentor.get("id"))
        if key not in self.messages_data:
            self.messages_data[key] = []
            save_messages(self.messages_data)
        msg_page = self._pages.get("messages")
        if msg_page:
            msg_page._active_conv = mentor.get("id")
            msg_page._refresh_conv_list()
            msg_page._render_chat_area(mentor.get("id"), is_group=False)
        self._show_page("messages")

    def _connect_dialog(self, m):
        name = f"{m.get('fname','')} {m.get('lname','')}"
        win = tk.Toplevel(self)
        win.title(f"Connect with {name}")
        win.geometry("440x210")
        win.configure(bg=BG2)
        win.grab_set()
        tk.Label(win, text=f"Connect with {name}", font=FONT_H2, fg=TEXT, bg=BG2).pack(pady=(18,4), padx=24, anchor="w")
        tk.Label(win, text=f"{name} — {m.get('role','')}.\nFirst session: free 30-min intro call.", font=FONT_BODY, fg=TEXT2, bg=BG2, wraplength=390, justify="left").pack(padx=24, anchor="w")
        row = tk.Frame(win, bg=BG2)
        row.pack(side="bottom", pady=16, padx=24, anchor="e")
        outline_btn(row, " Cancel ", win.destroy).pack(side="left", padx=6)
        gold_btn(row, " Send Request → ", lambda: [win.destroy(), self._toast(f"Request sent to {name}! 🎉")]).pack(side="left")

    def _quick_person(self, ptype):
        def handle(record, mode):
            if mode != "delete":
                self.people.append(record)
                save_people(self.people)
                self._toast(f"✓  {record.get('fname','')} {record.get('lname','')} added.")
                self._render_mentors("All")
                self._pages["people"]._refresh()
        PersonForm(self, person_type=ptype, on_save=handle)

    def _edit_via_people(self, person):
        people_page = self._pages.get("people")
        if people_page: people_page._edit(person)

    # ─────────────────────────────────────────────────────────────────────────
    #  SESSIONS
    # ─────────────────────────────────────────────────────────────────────────
    def _mk_sessions(self):
        frame = tk.Frame(self, bg=BG)
        _, inner = scrollable(frame)
        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(20,10))
        tk.Label(hdr, text="Your Sessions", font=FONT_H1, fg=TEXT, bg=BG).pack(side="left")
        
        u = self.current_user
        is_mentor = (u.get("type") == "mentor")
        if not is_mentor:
            gold_btn(hdr, " + Request Session ", self._request_session_dialog).pack(side="right")
        
        my_id = u.get("id")
        my_sessions = [s for s in self.sessions_data if s.get("mentee_id") == my_id or s.get("mentor_id") == my_id]
        
        pending = [s for s in my_sessions if s.get("status") == "pending"]
        upcoming = [s for s in my_sessions if s.get("status") == "upcoming"]
        past = [s for s in my_sessions if s.get("status") in ["completed", "declined"]]

        def build_section(title, data):
            divider(inner)
            tk.Label(inner, text=title, font=FONT_XS, fg=TEXT3, bg=BG).pack(anchor="w", padx=30, pady=(4,4))
            if not data:
                tk.Label(inner, text="Nothing here right now.", font=FONT_SM, fg=TEXT3, bg=BG).pack(anchor="w", padx=30, pady=(4,4))
            for s in data:
                self._session_row(inner, s)

        build_section("PENDING REQUESTS", pending)
        build_section("UPCOMING SESSIONS", upcoming)
        build_section("PAST & DECLINED", past)

        return frame

    def _session_row(self, parent, s):
        row = tk.Frame(parent, bg=BG2, padx=14, pady=10)
        row.pack(fill="x", padx=30, pady=3)
        
        status = s.get("status", "pending")
        dot_color = {"upcoming": GOLD, "pending": BLUE2, "completed": SAGE, "declined": CORAL}.get(status, TEXT3)
        
        dot = tk.Canvas(row, width=10, height=10, bg=BG2, highlightthickness=0)
        dot.create_oval(0,0,10,10, fill=dot_color, outline="")
        dot.pack(side="left", padx=(0,12))
        
        info = tk.Frame(row, bg=BG2)
        info.pack(side="left", fill="x", expand=True)
        
        is_mentor = self.current_user.get("type") == "mentor"
        other_name = s.get("mentee_name") if is_mentor else s.get("mentor_name")
        title = f"Session with {other_name}"
        
        tk.Label(info, text=title, font=FONT_BOLD, fg=TEXT, bg=BG2).pack(anchor="w")
        tk.Label(info, text=f"{s.get('topic','')}  ·  {s.get('duration','')}", font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w")
        
        right = tk.Frame(row, bg=BG2)
        right.pack(side="right")
        
        if status == "pending":
            if is_mentor:
                tk.Button(right, text=" Decline ", font=FONT_XS, bg=SURFACE, fg=CORAL, relief="flat", padx=8, pady=4, cursor="hand2", command=lambda: self._update_session_status(s, "declined")).pack(side="left", padx=4)
                tk.Button(right, text=" Accept ✓ ", font=FONT_XS, bg=GOLD, fg="#1a1614", relief="flat", padx=8, pady=4, cursor="hand2", command=lambda: self._update_session_status(s, "upcoming")).pack(side="left")
            else:
                tk.Label(right, text="Awaiting Approval...", font=FONT_XS, fg=TEXT3, bg=BG2).pack(anchor="e")
        else:
            tk.Label(right, text=status.upper(), font=FONT_XS, fg=dot_color, bg=BG2).pack(anchor="e")

    def _update_session_status(self, session, new_status):
        session["status"] = new_status
        save_sessions(self.sessions_data)
        if new_status == "upcoming":
            self._toast("Session Accepted! ✅")
        else:
            self._toast("Session Declined.")
        self._show_page("sessions")

    def _request_session_dialog(self):
        win = tk.Toplevel(self)
        win.title("Request Session")
        win.geometry("420x480")
        win.configure(bg=BG2)
        win.grab_set()

        tk.Frame(win, bg=GOLD, height=4).pack(fill="x")
        tk.Label(win, text="Request a Session", font=FONT_H2, fg=TEXT, bg=BG2).pack(pady=(14,4), padx=20, anchor="w")
        tk.Label(win, text="Choose a mentor to request a session with:", font=FONT_SM, fg=TEXT2, bg=BG2).pack(padx=20, anchor="w", pady=(0,8))

        _, inner = scrollable(win, bg=BG2)

        mentors = [p for p in self.people if p.get("type") == "mentor"]
        if not mentors:
            tk.Label(inner, text="No mentors available on the platform yet.", font=FONT_SM, fg=TEXT3, bg=BG2).pack(pady=20)
            return

        for p in mentors:
            row = tk.Frame(inner, bg=BG3, cursor="hand2", pady=8, padx=12)
            row.pack(fill="x", padx=16, pady=3)
            tk.Label(row, text=p.get("avatar","👤"), font=("Helvetica",18), bg=BG3).pack(side="left", padx=(0,8))
            info = tk.Frame(row, bg=BG3)
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=f"{p.get('fname','')} {p.get('lname','')}", font=FONT_BOLD, fg=TEXT, bg=BG3).pack(anchor="w")
            tk.Label(info, text=p.get("role",""), font=FONT_XS, fg=TEXT2, bg=BG3).pack(anchor="w")
            
            tk.Button(row, text=" Request ", font=FONT_XS, bg=p.get("color",GOLD), fg="#1a1614", relief="flat",
                      padx=8, pady=4, cursor="hand2", command=lambda mn=p, w=win: self._send_session_request(mn, w)).pack(side="right")
            
            for w in (row, info):
                w.bind("<Enter>", lambda e, r=row: r.configure(bg=SURFACE))
                w.bind("<Leave>", lambda e, r=row: r.configure(bg=BG3))

    def _send_session_request(self, mentor, win):
        win.destroy()
        mentor_name = f"{mentor.get('fname')} {mentor.get('lname')}"
        mentee_name = f"{self.current_user.get('fname')} {self.current_user.get('lname')}"
        phone = mentor.get("phone", "").strip()
        
        new_sess = {
            "id": str(uuid.uuid4()),
            "mentee_id": self.current_user.get("id"),
            "mentor_id": mentor.get("id"),
            "mentee_name": mentee_name,
            "mentor_name": mentor_name,
            "topic": "Intro / General Mentorship",
            "duration": "30 Min",
            "status": "pending",
            "when": "TBD",
            "timestamp": datetime.now().isoformat()
        }
        self.sessions_data.append(new_sess)
        save_sessions(self.sessions_data)

        self._toast(f"Session request sent to {mentor_name}! ✅")
        self._show_page("sessions")
        
        if Client and phone and TWILIO_SID != "your_twilio_account_sid":
            try:
                if not phone.startswith("+"): print("Warning: Phone number should start with a country code (+).")
                client = Client(TWILIO_SID, TWILIO_AUTH)
                msg = f"Mentee-SAP Alert: Hello {mentor.get('fname')}, {mentee_name} has requested a mentorship session with you! Check the app to accept."
                client.messages.create(body=msg, from_=TWILIO_FROM, to=phone)
                print(f"SMS successfully sent to {phone}")
            except Exception as e:
                print(f"Failed to send SMS: {e}")
        else:
            print("Notice: SMS not sent. Please configure Twilio keys and ensure the mentor has a valid phone number saved in their profile.")

    # ─────────────────────────────────────────────────────────────────────────
    #  CAREER ADVISOR (Hidden API Backend)
    # ─────────────────────────────────────────────────────────────────────────
    def _mk_advisor(self):
        frame = tk.Frame(self, bg=BG)
        left = tk.Frame(frame, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(24,8), pady=20)

        top_header = tk.Frame(left, bg=BG)
        top_header.pack(fill="x", pady=(0, 10))
        tk.Label(top_header, text="Career Advisor", font=FONT_H1, fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(top_header, text="Get instant advice, interview prep, and mentor recommendations.", font=FONT_SM, fg=TEXT2, bg=BG).pack(anchor="w", pady=(2,0))

        outline_btn(top_header, " Clear Chat ", self._clear_chat).place(relx=1.0, rely=0.0, anchor="ne")

        qp_frame = tk.Frame(left, bg=BG)
        qp_frame.pack(fill="x", pady=(0,10))
        for lbl, msg in [
            ("Choose a mentor?", "How do I choose the right mentor for my goals?"),
            ("Eng → PM switch",  "Tips for transitioning from engineering to product management?"),
            ("Ace my sessions",  "How to make the most of my mentorship sessions?"),
            ("2025 skills",      "What skills should I build to stay relevant in 2025?"),
        ]:
            tk.Button(qp_frame, text=lbl, font=FONT_XS, bg=SURFACE, fg=TEXT2, bd=0, padx=10, pady=4, cursor="hand2", activebackground=BG3, activeforeground=GOLD, command=lambda m=msg: self._send_quick(m)).pack(side="left", padx=3)

        self.chat_display = scrolledtext.ScrolledText(left, font=FONT_BODY, bg=BG2, fg=TEXT, relief="flat", bd=0, wrap="word", state="disabled", padx=12, pady=12)
        self.chat_display.pack(fill="both", expand=True)
        self.chat_display.tag_configure("adv_lbl", foreground=TEXT3,  font=FONT_XS)
        self.chat_display.tag_configure("adv_msg", foreground=TEXT,   font=FONT_BODY)
        self.chat_display.tag_configure("usr_lbl", foreground=TEXT3,  font=FONT_XS, justify="right")
        self.chat_display.tag_configure("usr_msg", foreground=GOLD,   font=FONT_BOLD, justify="right")
        self.chat_display.tag_configure("err_msg", foreground=CORAL,  font=FONT_BODY)

        u = self.current_user
        self._append_chat("advisor", f"Hi {u.get('fname', 'there')}! 👋 I'm your Career Advisor.\nAsk me anything about careers, mentors, or skill-building.")

        inp = tk.Frame(left, bg=BG)
        inp.pack(fill="x", pady=(10,0))
        self.chat_entry = tk.Entry(inp, font=FONT_BODY, bg=BG2, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0)
        self.chat_entry.pack(side="left", fill="x", expand=True, ipady=8, ipadx=10, padx=(0,8))
        self.chat_entry.bind("<Return>", lambda e: self._send_chat())
        self.send_btn = gold_btn(inp, " Send ↑ ", self._send_chat)
        self.send_btn.pack(side="right")

        return frame

    def _send_quick(self, msg):
        self.chat_entry.delete(0, tk.END)
        self.chat_entry.insert(0, msg)
        self._send_chat()

    def _send_chat(self):
        msg = self.chat_entry.get().strip()
        if not msg: return
        
        self.chat_entry.delete(0, tk.END)
        self._append_chat("user", msg)
        self.chat_history.append({"role":"user","content":msg})
        self.send_btn.configure(state="disabled", text=" ... ")
        self._append_chat("advisor", "▌ Analyzing...")
        threading.Thread(target=self._call_api, daemon=True).start()

    def _call_api(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=SYSTEM_API_KEY)
            u = self.current_user

            system_instruction = (f"You are a professional Career Advisor on the Mentee-SAP platform. "
                                  f"User you are talking to: {u.get('fname','')} {u.get('lname','')} ({u.get('role','')}) — {u.get('type','user')}. "
                                  f"Help with career advice, mentor selection, and skill growth. Be warm, concise, and highly practical. "
                                  f"IMPORTANT: Never disclose that you are an AI, a language model, or powered by Google/Gemini. "
                                  f"Act completely as a human coach and platform staff member.")

            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction
            )

            gemini_history = []
            for msg in self.chat_history[:-1]:
                role = "model" if msg["role"] == "assistant" else "user"
                gemini_history.append({"role": role, "parts": [msg["content"]]})

            chat = model.start_chat(history=gemini_history)
            latest_msg = self.chat_history[-1]["content"]

            resp = chat.send_message(latest_msg)
            reply = resp.text

            self.chat_history.append({"role":"assistant","content":reply})
            self.after(0, self._replace_thinking, reply)
            
        except ImportError:
            self.after(0, self._replace_thinking, "⚠ System communication error: Please run 'pip install google-generativeai'", True)
        except Exception as e:
            err = str(e)
            self.after(0, self._replace_thinking, f"⚠ Connection Error: Could not reach the server right now.", True)

    def _replace_thinking(self, text, is_error=False):
        self.chat_display.configure(state="normal")
        content = self.chat_display.get("1.0", tk.END)
        idx = content.rfind("▌ Analyzing...")
        if idx >= 0:
            ls = content.rfind("\n", 0, idx)
            self.chat_display.delete(f"1.0 + {ls} chars", tk.END)
        self.chat_display.configure(state="disabled")
        self._append_chat("advisor", text, "err_msg" if is_error else None)
        self.send_btn.configure(state="normal", text=" Send ↑ ")

    def _append_chat(self, who, text, tag_override=None):
        self.chat_display.configure(state="normal")
        if who == "user":
            self.chat_display.insert(tk.END, f"\n{'You':>72}\n", "usr_lbl")
            self.chat_display.insert(tk.END, f"{text}\n\n", "usr_msg")
        else:
            self.chat_display.insert(tk.END, "\nAdvisor\n", "adv_lbl")
            self.chat_display.insert(tk.END, f"{text}\n\n", tag_override or "adv_msg")
        self.chat_display.configure(state="disabled")
        self.chat_display.see(tk.END)

    def _clear_chat(self):
        self.chat_history.clear()
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.configure(state="disabled")
        self._append_chat("advisor", f"Chat cleared. Hi again, {self.current_user.get('fname','there')}! 👋")

    # ─────────────────────────────────────────────────────────────────────────
    #  MY PROFILE
    # ─────────────────────────────────────────────────────────────────────────
    def _mk_profile(self):
        frame = tk.Frame(self, bg=BG)
        _, self._prof_inner = scrollable(frame, bg=BG)
        return frame

    def _refresh_profile(self):
        p = self.current_user if self.current_user and self.current_user.get("id") != "admin" else self.my_profile
        for w in self._prof_inner.winfo_children(): w.destroy()
        inner = self._prof_inner

        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", padx=30, pady=(20,10))
        av_box = tk.Frame(hdr, bg=BG3, width=80, height=80)
        av_box.pack(side="left", padx=(0,16)); av_box.pack_propagate(False)
        tk.Label(av_box, text=p.get("avatar","👤"), font=("Helvetica",36), bg=BG3).place(relx=0.5, rely=0.5, anchor="center")
        info = tk.Frame(hdr, bg=BG)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=f"{p.get('fname','')} {p.get('lname','')}", font=("Georgia",20,"bold"), fg=TEXT, bg=BG).pack(anchor="w")
        tk.Label(info, text=p.get("role",""), font=FONT_BODY, fg=TEXT2, bg=BG).pack(anchor="w")
        badges = tk.Frame(info, bg=BG)
        badges.pack(anchor="w", pady=4)
        for txt, col in [("My Profile",GOLD),(p.get("location","Unknown Location"),CORAL),(p.get("avail","Flexible"),SAGE2)]:
            tk.Label(badges, text=f"  {txt}  ", font=FONT_XS, fg=col, bg=BG2, padx=4, pady=2).pack(side="left", padx=3)
        gold_btn(hdr, " ✏  Edit Profile ", self._open_edit_profile).pack(side="right", anchor="n")

        divider(inner)
        cols = tk.Frame(inner, bg=BG)
        cols.pack(fill="x", padx=30, pady=8)
        lc = tk.Frame(cols, bg=BG); lc.pack(side="left", fill="both", expand=True, padx=(0,16))
        rc = tk.Frame(cols, bg=BG); rc.pack(side="left", fill="both", expand=True)

        tk.Label(lc, text="Growth Progress", font=FONT_H2, fg=TEXT, bg=BG).pack(anchor="w", pady=(0,8))
        for lbl, pct, color in [("Product Thinking",72,GOLD),("Leadership",58,SAGE),("Communication",85,CORAL),("Strategic Thinking",64,GOLD)]:
            box = tk.Frame(lc, bg=BG2, padx=14, pady=10); box.pack(fill="x", pady=4)
            top = tk.Frame(box, bg=BG2); top.pack(fill="x")
            tk.Label(top, text=lbl, font=FONT_SM, fg=TEXT, bg=BG2).pack(side="left")
            tk.Label(top, text=f"{pct}%", font=FONT_SM, fg=color, bg=BG2).pack(side="right")
            bar_bg = tk.Frame(box, bg=SURFACE, height=6); bar_bg.pack(fill="x", pady=(5,0))
            tk.Frame(bar_bg, bg=color, height=6).place(x=0, y=0, relwidth=pct/100, height=6)

        tk.Label(rc, text="Goals & Milestones", font=FONT_H2, fg=TEXT, bg=BG).pack(anchor="w", pady=(0,8))
        for title, sub, color in [("Complete 10 mentor sessions","7/10 done",SAGE),("Build portfolio","In progress",GOLD),(p.get("goal","Your goal here"),"Active goal",BLUE)]:
            row = tk.Frame(rc, bg=BG2, padx=12, pady=10); row.pack(fill="x", pady=4)
            dot = tk.Canvas(row, width=10, height=10, bg=BG2, highlightthickness=0)
            dot.create_oval(0,0,10,10, fill=color, outline=""); dot.pack(side="left", padx=(0,10))
            tk.Label(row, text=title, font=FONT_BOLD, fg=TEXT, bg=BG2).pack(anchor="w")
            tk.Label(row, text=sub,   font=FONT_XS,  fg=TEXT2, bg=BG2).pack(anchor="w")

        divider(inner)
        tk.Label(inner, text="Profile Details", font=FONT_H2, fg=TEXT, bg=BG).pack(anchor="w", padx=30, pady=(0,8))
        det = tk.Frame(inner, bg=BG2, padx=20, pady=16)
        det.pack(fill="x", padx=30, pady=(0,20))
        for lbl, val in [("Goal",p.get("goal","—")),("Skills",p.get("skills","—")),("Bio",p.get("bio","—")),("LinkedIn",p.get("linkedin","Not set") or "Not set")]:
            r = tk.Frame(det, bg=BG2); r.pack(fill="x", pady=4)
            tk.Label(r, text=f"{lbl}:", font=FONT_BOLD, fg=TEXT2, bg=BG2, width=10, anchor="w").pack(side="left")
            tk.Label(r, text=val, font=FONT_BODY, fg=TEXT, bg=BG2, wraplength=500, justify="left").pack(side="left")

    def _open_edit_profile(self):
        p = self.current_user if self.current_user and self.current_user.get("id") != "admin" else self.my_profile
        win = tk.Toplevel(self)
        win.title("Edit My Profile")
        win.geometry("560x660")
        win.configure(bg=BG2)
        win.grab_set()

        tk.Frame(win, bg=GOLD, height=4).pack(fill="x")
        tk.Label(win, text="Edit My Profile", font=FONT_H1, fg=TEXT, bg=BG2).pack(pady=(14,2), padx=24, anchor="w")
        tk.Label(win, text="Saved locally on your machine.", font=FONT_XS, fg=TEXT2, bg=BG2).pack(padx=24, anchor="w", pady=(0,8))

        _, form = scrollable(win, bg=BG2)
        entries = {}

        def field(parent, lbl, key):
            tk.Label(parent, text=lbl, font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8,2))
            e = tk.Entry(parent, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0)
            e.pack(fill="x", padx=24, ipady=6, ipadx=8)
            e.insert(0, p.get(key,""))
            entries[key] = e

        tk.Label(form, text="Avatar", font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8,4))
        av_row = tk.Frame(form, bg=BG2); av_row.pack(anchor="w", padx=24)
        sel_av = tk.StringVar(value=p.get("avatar","🧑‍💻"))
        av_btns = []
        def pick(val):
            sel_av.set(val)
            for b in av_btns:
                b.configure(bg=GOLD if b.cget("text")==val else BG3, fg="#1a1614" if b.cget("text")==val else TEXT)
        for av in AVATARS[:12]:
            b = tk.Button(av_row, text=av, font=("Helvetica",15), bg=GOLD if av==p.get("avatar") else BG3,
                          fg="#1a1614" if av==p.get("avatar") else TEXT, width=2, relief="flat", cursor="hand2", command=lambda v=av: pick(v))
            b.pack(side="left", padx=2)
            av_btns.append(b)

        r1 = tk.Frame(form, bg=BG2); r1.pack(fill="x")
        lf = tk.Frame(r1, bg=BG2); lf.pack(side="left", fill="x", expand=True)
        rf = tk.Frame(r1, bg=BG2); rf.pack(side="left", fill="x", expand=True)
        field(lf, "First Name", "fname"); field(rf, "Last Name", "lname")
        field(form, "Role / Title", "role")
        r2 = tk.Frame(form, bg=BG2); r2.pack(fill="x")
        lf2 = tk.Frame(r2, bg=BG2); lf2.pack(side="left", fill="x", expand=True)
        rf2 = tk.Frame(r2, bg=BG2); rf2.pack(side="left", fill="x", expand=True)
        field(lf2, "Location", "location"); field(rf2, "LinkedIn", "linkedin")

        tk.Label(form, text="Bio", font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8,2))
        bio_t = tk.Text(form, font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT, relief="flat", bd=0, height=3, wrap="word")
        bio_t.pack(fill="x", padx=24, ipady=4, ipadx=8)
        bio_t.insert("1.0", p.get("bio",""))

        field(form, "Career Goal", "goal")
        field(form, "Skills (comma separated)", "skills")

        tk.Label(form, text="Availability", font=FONT_XS, fg=TEXT2, bg=BG2).pack(anchor="w", padx=24, pady=(8,2))
        avail_v = tk.StringVar(value=p.get("avail","Evenings (6–10 PM)"))
        ttk.Combobox(form, textvariable=avail_v, state="readonly", values=["Weekends only","Evenings (6–10 PM)","Flexible","Full-time available"]).pack(fill="x", padx=24, ipady=4)
        tk.Frame(form, height=16, bg=BG2).pack()

        btn_row = tk.Frame(win, bg=BG2); btn_row.pack(side="bottom", fill="x", padx=24, pady=14)
        outline_btn(btn_row, " Cancel ", win.destroy).pack(side="right", padx=(8,0))

        def do_save():
            p["avatar"] = sel_av.get()
            for key in ["fname","lname","role","location","linkedin","goal","skills"]:
                v = entries[key].get().strip()
                if v: p[key] = v
            p["bio"]   = bio_t.get("1.0", tk.END).strip()
            p["avail"] = avail_v.get()
            
            if p.get("id") == "admin":
                save_my_profile(p)
            else:
                for i, person in enumerate(self.people):
                    if person.get("id") == p.get("id"):
                        self.people[i] = p
                        break
                save_people(self.people)

            win.destroy()
            self._refresh_profile()
            self.nav_pill.configure(text=f"  {p.get('avatar')}  {p.get('fname')} {p.get('lname','A')[0]}.  ")
            self._toast("Profile updated ✓")

        gold_btn(btn_row, " Save Changes ✓ ", do_save).pack(side="right")

    # ── Toast ─────────────────────────────────────────────────────────────────
    def _toast(self, msg, ms=2800):
        t = tk.Toplevel(self)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        t.configure(bg=SAGE)
        tk.Label(t, text=f"  {msg}  ", font=FONT_BOLD, fg="white", bg=SAGE, pady=8).pack()
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        t.update_idletasks()
        t.geometry(f"+{sw-t.winfo_reqwidth()-30}+{sh-t.winfo_reqheight()-60}")
        t.after(ms, t.destroy)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = MenteeSAP()
    style = ttk.Style(app)
    style.theme_use("default")
    style.configure("TScrollbar",  background=BG3, troughcolor=BG2, arrowcolor=TEXT3, bordercolor=BG2)
    style.configure("TCombobox",   fieldbackground=BG3, background=BG3, foreground=TEXT, selectbackground=SURFACE)
    style.map("TCombobox", fieldbackground=[("readonly", BG3)])
    app.mainloop()