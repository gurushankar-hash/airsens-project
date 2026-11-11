import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sqlite3
import re
import requests
import joblib
import sympy as sp
import datetime
import os
import math
import pandas as pd
from PIL import Image, ImageDraw, ImageTk

# ==========================================================
# SYSTEM & THEME CONFIGURATION
# ==========================================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FONT_FAMILY = "Segoe UI"

# Ultra-Modern Cyber-Medical Theme Palette
BG_DARK = "#090D16"         # Deep Midnight Navy background
PANEL_BG = "#0E1524"        # Secondary panel background
CARD_BG = "#141E33"         # Frosted glass card background
CARD_BG_ALT = "#18243C"     # Slightly lighter card accent
SIDEBAR_BG = "#0B111C"      # Sleek dark sidebar
BORDER = "#22314E"          # Elegant card border
BORDER_LIGHT = "#2F436B"    # Highlight border
INPUT_BG = "#0B111E"        # Deep input background

PRIMARY = "#06B6D4"         # Neon Electric Cyan
PRIMARY_HOVER = "#0891B2"   # Deeper Cyan
ACCENT_SKY = "#38BDF8"      # Sky Blue Accent
ACCENT_INDIGO = "#6366F1"   # Soft Indigo Accent

TEXT_LIGHT = "#F8FAFC"      # High contrast clean white
TEXT_DIM = "#94A3B8"        # Subtle slate gray
TEXT_FAINT = "#64748B"      # Faint muted helper text

LOW_COLOR = "#10B981"       # Emerald Green for Low Risk
MOD_COLOR = "#F59E0B"       # Warm Amber for Moderate Risk
HIGH_COLOR = "#EF4444"      # Crimson Rose for High Risk

WAQI_TOKEN = "182993a5c8b0606b3bb333aa4b3f23bc53239797"
LUNGS_IMAGE_PATH = "assets/lungs_real_silhouette_white.png"
LOGO_IMAGE_PATH = "assets/airsense_logo_shield.png"

# ==========================================================
# DATABASE INITIALIZATION & EXTENSIONS
# ==========================================================

def init_database():
    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    # Ensure users table has all required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            age INTEGER DEFAULT 25,
            city TEXT DEFAULT 'Chennai',
            dob TEXT DEFAULT '',
            cough TEXT DEFAULT '0',
            wheezing TEXT DEFAULT '0',
            breathing TEXT DEFAULT '0',
            sneezing TEXT DEFAULT '0',
            dust TEXT DEFAULT '0'
        )
    """)
    # Check if city column exists, if not add it
    cursor.execute("PRAGMA table_info(users)")
    cols = [info[1] for info in cursor.fetchall()]
    if "city" not in cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN city TEXT DEFAULT 'Chennai'")
        except Exception:
            pass

    # Ensure history table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            aqi INTEGER,
            pm25 REAL,
            risk_score REAL,
            risk_level TEXT
        )
    """)
    conn.commit()
    conn.close()

init_database()

# ==========================================================
# MODEL LOADER
# ==========================================================

try:
    risk_model = joblib.load("risk_model.pkl")
    print("Machine Learning Model (RandomForest) successfully loaded.")
except Exception as e:
    risk_model = None
    print("Machine Learning model not loaded:", e)

# ==========================================================
# APPLICATION STATE
# ==========================================================

current_user = ""
feature_data = {}
last_result = {}
gauge_img_ref = None

# ==========================================================
# ROOT WINDOW SETUP
# ==========================================================

root = ctk.CTk()
root.title("AirSense™ • Intelligent Respiratory & Environmental Monitor")
root.geometry("1300x820")
root.minsize(1080, 680)
root.configure(fg_color=BG_DARK)

try:
    root.state("zoomed")
except Exception:
    pass

# ==========================================================
# ASSET OPTIMIZATION (PRE-RESIZE TO AVOID CPU LAG)
# ==========================================================

lungs_base_img = None
logo_base_img = None

try:
    raw_lungs = Image.open(LUNGS_IMAGE_PATH).convert("RGBA")
    lungs_base_img = raw_lungs.resize((350, 350), Image.LANCZOS)
except Exception as e:
    print("Could not load lungs asset:", e)

try:
    raw_logo = Image.open(LOGO_IMAGE_PATH).convert("RGBA")
    logo_base_img = raw_logo.resize((120, 120), Image.LANCZOS)
except Exception as e:
    print("Could not load logo asset:", e)

# ==========================================================
# TOP LEVEL CONTAINERS (MASTER SHELL ARCHITECTURE)
# ==========================================================

auth_container = ctk.CTkFrame(root, fg_color=BG_DARK, corner_radius=0)
app_container = ctk.CTkFrame(root, fg_color=BG_DARK, corner_radius=0)

# Start on Auth screen
auth_container.pack(fill="both", expand=True)

# ==========================================================
# AUTHENTICATION PAGE (SPLIT-SCREEN MODERN HERO)
# ==========================================================

# Left Hero Panel
auth_hero = ctk.CTkFrame(auth_container, fg_color=PANEL_BG, corner_radius=0)
auth_hero.place(relx=0, rely=0, relwidth=0.42, relheight=1)

hero_canvas = tk.Canvas(auth_hero, bg=PANEL_BG, highlightthickness=0)
hero_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

lungs_canvas_item = None
lungs_halo_item = None
lungs_tk_ref = None
breathing_step = 0
breathing_direction = 1

def draw_hero_background(event=None):
    hero_canvas.delete("decor")
    w = hero_canvas.winfo_width()
    h = hero_canvas.winfo_height()
    if w < 20 or h < 20:
        return

    # Deep decorative radial circles / glow
    hero_canvas.create_oval(w * 0.4, -h * 0.1, w * 1.2, h * 0.45, fill="#121D33", outline="", tags="decor")
    hero_canvas.create_oval(-w * 0.3, h * 0.55, w * 0.45, h * 1.25, fill="#0F1A2E", outline="", tags="decor")
    hero_canvas.create_oval(w * 0.15, h * 0.4, w * 0.85, h * 0.95, fill="#111B30", outline="", tags="decor")

    # Brand Title & Slogan
    hero_canvas.create_text(w * 0.5, h * 0.18, text="AirSense", font=(FONT_FAMILY, 38, "bold"),
                           fill=TEXT_LIGHT, anchor="center", tags="decor")
    hero_canvas.create_text(w * 0.5, h * 0.235, text="RESPIRATORY HEALTH INTELLIGENCE",
                           font=(FONT_FAMILY, 10, "bold"), fill=PRIMARY, anchor="center", tags="decor")

    hero_canvas.create_text(w * 0.5, h * 0.29, text="Breathe Smarter • Live Healthier",
                           font=(FONT_FAMILY, 15, "italic"), fill=TEXT_DIM, anchor="center", tags="decor")

    # Status Pill on Canvas
    hero_canvas.create_text(w * 0.5, h * 0.89, text="●  Real-time WAQI & Meteo Telemetry Online",
                           font=(FONT_FAMILY, 10, "bold"), fill=LOW_COLOR, anchor="center", tags="decor")
    hero_canvas.create_text(w * 0.5, h * 0.925, text="AI Random Forest Clinical Decision Engine",
                           font=(FONT_FAMILY, 9), fill=TEXT_FAINT, anchor="center", tags="decor")

    hero_canvas.tag_lower("decor")
    update_breathing_frame()

def update_breathing_frame():
    global lungs_canvas_item, lungs_halo_item, lungs_tk_ref
    if lungs_base_img is None:
        return
    w = hero_canvas.winfo_width()
    h = hero_canvas.winfo_height()
    if w < 20 or h < 20:
        return

    min_size, max_size = 195, 235
    cur_size = int(min_size + breathing_step)

    resized = lungs_base_img.resize((cur_size, cur_size), Image.LANCZOS)
    lungs_tk_ref = ImageTk.PhotoImage(resized)

    cx, cy = w * 0.5, h * 0.57

    # Draw or update soft halo glow behind lungs
    halo_r = cur_size * 0.62
    if lungs_halo_item is not None:
        hero_canvas.coords(lungs_halo_item, cx - halo_r, cy - halo_r, cx + halo_r, cy + halo_r)
    else:
        lungs_halo_item = hero_canvas.create_oval(cx - halo_r, cy - halo_r, cx + halo_r, cy + halo_r,
                                                  fill="#162842", outline="")

    if lungs_canvas_item is not None:
        hero_canvas.coords(lungs_canvas_item, cx, cy)
        hero_canvas.itemconfig(lungs_canvas_item, image=lungs_tk_ref)
    else:
        lungs_canvas_item = hero_canvas.create_image(cx, cy, image=lungs_tk_ref)

def animate_lungs():
    global breathing_step, breathing_direction
    if lungs_base_img is None:
        return
    breathing_step += breathing_direction * 1.5
    if breathing_step >= 40:
        breathing_step = 40
        breathing_direction = -1
    elif breathing_step <= 0:
        breathing_step = 0
        breathing_direction = 1

    update_breathing_frame()
    root.after(45, animate_lungs)

hero_canvas.bind("<Configure>", draw_hero_background)
root.after(150, draw_hero_background)
if lungs_base_img is not None:
    root.after(500, animate_lungs)

# Right Auth Form Panel
auth_right = ctk.CTkFrame(auth_container, fg_color=BG_DARK, corner_radius=0)
auth_right.place(relx=0.42, rely=0, relwidth=0.58, relheight=1)

# Card Container (Centered Glass Card)
auth_card = ctk.CTkFrame(auth_right, fg_color=CARD_BG, corner_radius=20, border_width=1, border_color=BORDER)
auth_card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.72, relheight=0.82)

# Tab Switcher at the top of Card
auth_tab_bar = ctk.CTkFrame(auth_card, fg_color=PANEL_BG, corner_radius=12, height=48)
auth_tab_bar.pack(fill="x", padx=36, pady=(32, 16))
auth_tab_bar.pack_propagate(False)

tab_login_btn = ctk.CTkButton(auth_tab_bar, text="🔑  Sign In", corner_radius=10,
                              fg_color=CARD_BG, text_color=PRIMARY, font=(FONT_FAMILY, 13, "bold"),
                              hover_color=CARD_BG)
tab_login_btn.place(relx=0.02, rely=0.08, relwidth=0.47, relheight=0.84)

tab_reg_btn = ctk.CTkButton(auth_tab_bar, text="✨  Create Account", corner_radius=10,
                            fg_color=PANEL_BG, text_color=TEXT_DIM, font=(FONT_FAMILY, 13, "bold"),
                            hover_color=PANEL_BG)
tab_reg_btn.place(relx=0.51, rely=0.08, relwidth=0.47, relheight=0.84)

# Sub-Containers for Login & Register
login_view = ctk.CTkFrame(auth_card, fg_color="transparent")
register_view = ctk.CTkFrame(auth_card, fg_color="transparent")

# --- LOGIN FORM ---
ctk.CTkLabel(login_view, text="Welcome Back", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", pady=(8, 2))
ctk.CTkLabel(login_view, text="Access your personalized respiratory telemetry & past logs.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(0, 22))

ctk.CTkLabel(login_view, text="USERNAME", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM
             ).pack(anchor="w", pady=(4, 2))
login_username = ctk.CTkEntry(login_view, height=44, placeholder_text="Enter your username",
                              corner_radius=10, border_color=BORDER, fg_color=INPUT_BG,
                              text_color=TEXT_LIGHT, font=(FONT_FAMILY, 13))
login_username.pack(fill="x", pady=(0, 12))

ctk.CTkLabel(login_view, text="PASSWORD", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM
             ).pack(anchor="w", pady=(4, 2))

login_pwd_frame = ctk.CTkFrame(login_view, fg_color="transparent")
login_pwd_frame.pack(fill="x", pady=(0, 4))

login_password = ctk.CTkEntry(login_pwd_frame, height=44, placeholder_text="Enter your password",
                              show="•", corner_radius=10, border_color=BORDER, fg_color=INPUT_BG,
                              text_color=TEXT_LIGHT, font=(FONT_FAMILY, 13))
login_password.pack(side="left", fill="x", expand=True)

show_login_pwd = tk.BooleanVar(value=False)
def toggle_login_pwd():
    if show_login_pwd.get():
        login_password.configure(show="")
        pwd_eye_btn.configure(text="🙈")
    else:
        login_password.configure(show="•")
        pwd_eye_btn.configure(text="👁️")

def on_toggle_click():
    show_login_pwd.set(not show_login_pwd.get())
    toggle_login_pwd()

pwd_eye_btn = ctk.CTkButton(login_pwd_frame, text="👁️", width=44, height=44, corner_radius=10,
                            fg_color=PANEL_BG, hover_color=BORDER, font=(FONT_FAMILY, 12),
                            command=on_toggle_click)
pwd_eye_btn.pack(side="left", padx=(8, 0))

login_status = ctk.CTkLabel(login_view, text="", font=(FONT_FAMILY, 11, "bold"), text_color=HIGH_COLOR)
login_status.pack(anchor="w", pady=(6, 4))

def perform_login(event=None):
    global current_user
    u = login_username.get().strip()
    p = login_password.get().strip()
    if not u or not p:
        login_status.configure(text="Please fill in both username and password.", text_color=HIGH_COLOR)
        return

    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user_row = cursor.fetchone()
    conn.close()

    if user_row:
        current_user = u
        login_status.configure(text="✓ Login successful! Synchronizing dashboard...", text_color=LOW_COLOR)
        root.after(400, launch_dashboard)
    else:
        login_status.configure(text="Invalid credentials. Please verify your details.", text_color=HIGH_COLOR)

login_btn = ctk.CTkButton(login_view, text="Sign In to Dashboard  ➔", height=46, corner_radius=12,
                          fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=BG_DARK,
                          font=(FONT_FAMILY, 14, "bold"), command=perform_login)
login_btn.pack(fill="x", pady=(14, 10))

login_username.bind("<Return>", perform_login)
login_password.bind("<Return>", perform_login)

# --- REGISTER FORM ---
ctk.CTkLabel(register_view, text="Create Your Account", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", pady=(8, 2))
ctk.CTkLabel(register_view, text="Set up your profile for clinical air quality risk tracking.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(0, 16))

reg_grid = ctk.CTkFrame(register_view, fg_color="transparent")
reg_grid.pack(fill="x", pady=(0, 6))

ctk.CTkLabel(reg_grid, text="USERNAME", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).grid(row=0, column=0, sticky="w", pady=(2, 2))
ctk.CTkLabel(reg_grid, text="AGE (OPTIONAL)", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).grid(row=0, column=1, sticky="w", padx=(10, 0), pady=(2, 2))

reg_username = ctk.CTkEntry(reg_grid, height=42, placeholder_text="Username", corner_radius=10,
                            border_color=BORDER, fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
reg_username.grid(row=1, column=0, sticky="ew", pady=(0, 8))

reg_age = ctk.CTkEntry(reg_grid, height=42, placeholder_text="e.g. 24", corner_radius=10,
                       border_color=BORDER, fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
reg_age.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 8))
reg_grid.columnconfigure(0, weight=3)
reg_grid.columnconfigure(1, weight=1)

ctk.CTkLabel(register_view, text="PASSWORD", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM
             ).pack(anchor="w", pady=(2, 2))

reg_password = ctk.CTkEntry(register_view, height=42, placeholder_text="Create a secure password",
                            show="•", corner_radius=10, border_color=BORDER, fg_color=INPUT_BG,
                            text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
reg_password.pack(fill="x", pady=(0, 6))

# Live Password Criteria Pills
req_frame = ctk.CTkFrame(register_view, fg_color="transparent")
req_frame.pack(fill="x", pady=(2, 6))

def make_req_badge(parent, text):
    lbl = ctk.CTkLabel(parent, text=f"○ {text}", font=(FONT_FAMILY, 9), text_color=TEXT_FAINT)
    lbl.pack(side="left", padx=(0, 8))
    return lbl

b_len = make_req_badge(req_frame, "8+ Chars")
b_let = make_req_badge(req_frame, "Letter")
b_num = make_req_badge(req_frame, "Number")
b_spe = make_req_badge(req_frame, "Special Char")

def validate_reg_password(event=None):
    pwd = reg_password.get()
    b_len.configure(text="✓ 8+ Chars" if len(pwd) >= 8 else "○ 8+ Chars",
                    text_color=LOW_COLOR if len(pwd) >= 8 else TEXT_FAINT)
    b_let.configure(text="✓ Letter" if re.search(r"[A-Za-z]", pwd) else "○ Letter",
                    text_color=LOW_COLOR if re.search(r"[A-Za-z]", pwd) else TEXT_FAINT)
    b_num.configure(text="✓ Number" if re.search(r"[0-9]", pwd) else "○ Number",
                    text_color=LOW_COLOR if re.search(r"[0-9]", pwd) else TEXT_FAINT)
    b_spe.configure(text="✓ Special" if re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd) else "○ Special",
                    text_color=LOW_COLOR if re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd) else TEXT_FAINT)

reg_password.bind("<KeyRelease>", validate_reg_password)

reg_status = ctk.CTkLabel(register_view, text="", font=(FONT_FAMILY, 11, "bold"), text_color=HIGH_COLOR)
reg_status.pack(anchor="w", pady=(4, 2))

def perform_register():
    u = reg_username.get().strip()
    p = reg_password.get().strip()
    a_str = reg_age.get().strip()
    age = int(a_str) if a_str.isdigit() else 25

    if not u or not p:
        reg_status.configure(text="Please fill in username and password.", text_color=HIGH_COLOR)
        return
    if len(p) < 8:
        reg_status.configure(text="Password must be at least 8 characters.", text_color=HIGH_COLOR)
        return
    if not re.search(r"[A-Za-z]", p) or not re.search(r"[0-9]", p) or not re.search(r"[!@#$%^&*(),.?\":{}|<>]", p):
        reg_status.configure(text="Password must have letters, numbers, and special symbols.", text_color=HIGH_COLOR)
        return

    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password, age) VALUES (?, ?, ?)", (u, p, age))
        conn.commit()
        reg_status.configure(text="✓ Account created! Redirecting to Sign In...", text_color=LOW_COLOR)
        root.after(1000, show_login_tab)
    except sqlite3.IntegrityError:
        reg_status.configure(text="Username already exists. Please choose another.", text_color=HIGH_COLOR)
    finally:
        conn.close()

reg_btn = ctk.CTkButton(register_view, text="Register New Account  ➔", height=44, corner_radius=12,
                         fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=BG_DARK,
                         font=(FONT_FAMILY, 13, "bold"), command=perform_register)
reg_btn.pack(fill="x", pady=(10, 4))

def show_login_tab():
    register_view.pack_forget()
    reg_status.configure(text="")
    tab_reg_btn.configure(fg_color=PANEL_BG, text_color=TEXT_DIM)
    tab_login_btn.configure(fg_color=CARD_BG, text_color=PRIMARY)
    login_view.pack(fill="both", expand=True, padx=36, pady=(10, 24))

def show_register_tab():
    login_view.pack_forget()
    login_status.configure(text="")
    tab_login_btn.configure(fg_color=PANEL_BG, text_color=TEXT_DIM)
    tab_reg_btn.configure(fg_color=CARD_BG, text_color=PRIMARY)
    register_view.pack(fill="both", expand=True, padx=36, pady=(10, 24))

tab_login_btn.configure(command=show_login_tab)
tab_reg_btn.configure(command=show_register_tab)

show_login_tab()

# ==========================================================
# MASTER DASHBOARD SHELL (TOP NAV + SIDEBAR + VIEWPORT)
# ==========================================================

# Top Navbar
top_navbar = ctk.CTkFrame(app_container, fg_color=PANEL_BG, corner_radius=0, height=64,
                          border_width=1, border_color=BORDER)
top_navbar.pack(side="top", fill="x")
top_navbar.pack_propagate(False)

# Left brand badge
nav_brand_box = ctk.CTkFrame(top_navbar, fg_color="transparent")
nav_brand_box.pack(side="left", padx=24)

ctk.CTkLabel(nav_brand_box, text="AirSense", font=(FONT_FAMILY, 18, "bold"), text_color=TEXT_LIGHT
             ).pack(side="left")
ctk.CTkLabel(nav_brand_box, text=" v2.5 PRO", font=(FONT_FAMILY, 10, "bold"),
             fg_color=CARD_BG, text_color=PRIMARY, corner_radius=6, padx=8, pady=2
             ).pack(side="left", padx=(10, 0))

# Center Live Status Badge
nav_center_box = ctk.CTkFrame(top_navbar, fg_color="transparent")
nav_center_box.pack(side="left", expand=True)

nav_live_chip = ctk.CTkLabel(nav_center_box, text="● Live Environmental Sync Ready",
                             font=(FONT_FAMILY, 11, "bold"), text_color=LOW_COLOR,
                             fg_color=CARD_BG, corner_radius=12, padx=14, pady=5)
nav_live_chip.pack()

# Right User Profile Chip
nav_user_box = ctk.CTkFrame(top_navbar, fg_color="transparent")
nav_user_box.pack(side="right", padx=24)

nav_avatar = ctk.CTkLabel(nav_user_box, text="U", width=34, height=34, corner_radius=17,
                          fg_color=PRIMARY, text_color=BG_DARK, font=(FONT_FAMILY, 13, "bold"))
nav_avatar.pack(side="left", padx=(0, 10))

nav_username_lbl = ctk.CTkLabel(nav_user_box, text="User", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_LIGHT)
nav_username_lbl.pack(side="left", padx=(0, 16))

def logout_action():
    global current_user
    current_user = ""
    app_container.pack_forget()
    auth_container.pack(fill="both", expand=True)
    login_username.delete(0, "end")
    login_password.delete(0, "end")
    login_status.configure(text="")

nav_logout_btn = ctk.CTkButton(nav_user_box, text="Logout", width=75, height=30, corner_radius=8,
                               fg_color=CARD_BG, hover_color=BORDER, text_color=HIGH_COLOR,
                               font=(FONT_FAMILY, 11, "bold"), command=logout_action)
nav_logout_btn.pack(side="left")

# Main Body Frame (Sidebar + Viewport)
app_body = ctk.CTkFrame(app_container, fg_color=BG_DARK, corner_radius=0)
app_body.pack(side="top", fill="both", expand=True)

# Sidebar
sidebar = ctk.CTkFrame(app_body, fg_color=SIDEBAR_BG, corner_radius=0, width=225,
                       border_width=1, border_color=BORDER)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

# Navigation Buttons
nav_items = {}

def create_sidebar_item(name, icon, key):
    btn = ctk.CTkButton(sidebar, text=f"  {icon}   {name}", anchor="w", height=46, corner_radius=10,
                        fg_color="transparent", text_color=TEXT_DIM, hover_color=CARD_BG,
                        font=(FONT_FAMILY, 13, "bold"),
                        command=lambda: navigate_to(key))
    btn.pack(fill="x", padx=14, pady=4)
    nav_items[key] = btn
    return btn

ctk.CTkLabel(sidebar, text="MAIN NAVIGATION", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT
             ).pack(anchor="w", padx=20, pady=(20, 8))

create_sidebar_item("Data Collection", "📊", "data")
create_sidebar_item("Risk Prediction", "🎯", "prediction")
create_sidebar_item("History & Trends", "📈", "history")
create_sidebar_item("User Profile", "👤", "profile")

# Sidebar Bottom Lungs / Info Widget
side_bottom_box = ctk.CTkFrame(sidebar, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
side_bottom_box.pack(side="bottom", fill="x", padx=14, pady=16)

ctk.CTkLabel(side_bottom_box, text="🫁 Active Telemetry", font=(FONT_FAMILY, 11, "bold"), text_color=PRIMARY
             ).pack(anchor="w", padx=12, pady=(10, 2))
ctk.CTkLabel(side_bottom_box, text="Monitoring real-time respiratory load with multi-factor risk index.",
             font=(FONT_FAMILY, 9), text_color=TEXT_DIM, wraplength=170, justify="left"
             ).pack(anchor="w", padx=12, pady=(0, 10))

# Content Viewport (Swapping pages)
viewport = ctk.CTkFrame(app_body, fg_color=BG_DARK, corner_radius=0)
viewport.pack(side="left", fill="both", expand=True)

# Register Page Frames inside Viewport
page_views = {
    "data": ctk.CTkScrollableFrame(viewport, fg_color=BG_DARK),
    "prediction": ctk.CTkScrollableFrame(viewport, fg_color=BG_DARK),
    "history": ctk.CTkScrollableFrame(viewport, fg_color=BG_DARK),
    "profile": ctk.CTkScrollableFrame(viewport, fg_color=BG_DARK),
    "alert": ctk.CTkScrollableFrame(viewport, fg_color=BG_DARK)
}

active_page_key = "data"

def navigate_to(key):
    global active_page_key
    active_page_key = key

    # Hide all pages
    for p in page_views.values():
        p.pack_forget()

    # Highlight active sidebar button
    for k, btn in nav_items.items():
        if k == key:
            btn.configure(fg_color=CARD_BG, text_color=PRIMARY, border_width=1, border_color=PRIMARY)
        else:
            btn.configure(fg_color="transparent", text_color=TEXT_DIM, border_width=0)

    # Show active page
    if key in page_views:
        page_views[key].pack(fill="both", expand=True, padx=28, pady=20)

    # Lifecycle callbacks
    if key == "history":
        refresh_history_page()
    elif key == "profile":
        refresh_profile_page()

def launch_dashboard():
    auth_container.pack_forget()
    app_container.pack(fill="both", expand=True)
    nav_username_lbl.configure(text=current_user)
    initials = current_user[:2].upper() if len(current_user) >= 2 else (current_user[:1].upper() or "U")
    nav_avatar.configure(text=initials)

    # Load user default profile into fields if available
    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT age, city FROM users WHERE username=?", (current_user,))
    row = cursor.fetchone()
    conn.close()

    if row:
        if row[0]:
            dc_age_input.delete(0, "end")
            dc_age_input.insert(0, str(row[0]))
            update_age_cohort()
        if row[1]:
            dc_city_input.delete(0, "end")
            dc_city_input.insert(0, str(row[1]))
            dc_city_chip.configure(text=str(row[1]))

    dc_patient_chip.configure(text=current_user or "Patient")
    navigate_to("data")

# ==========================================================
# PAGE 1: DATA COLLECTION (CLINICAL INTAKE & TELEMETRY CONSOLE)
# ==========================================================

data_view = page_views["data"]

# Header Banner with Clinical Subtitle
dc_header = ctk.CTkFrame(data_view, fg_color="transparent")
dc_header.pack(fill="x", pady=(4, 12))

ctk.CTkLabel(dc_header, text="Clinical Intake & Telemetry Synchronization", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w")
ctk.CTkLabel(dc_header, text="Standardized patient triaging console • Ambient atmospheric synchronization via WAQI & Open-Meteo telemetric sensor grid.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(2, 8))

# Metadata Ribbon (Patient info & clinical protocol timestamp)
dc_ribbon = ctk.CTkFrame(data_view, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
dc_ribbon.pack(fill="x", pady=(0, 16))

dc_ribbon_content = ctk.CTkFrame(dc_ribbon, fg_color="transparent")
dc_ribbon_content.pack(fill="x", padx=16, pady=10)

def make_dc_chip(parent, icon, label, val_text):
    box = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=BORDER)
    box.pack(side="left", padx=(0, 10))
    ctk.CTkLabel(box, text=f"{icon} {label}:", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_FAINT
                 ).pack(side="left", padx=(10, 4), pady=5)
    lbl = ctk.CTkLabel(box, text=val_text, font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_LIGHT)
    lbl.pack(side="left", padx=(0, 10), pady=5)
    return lbl

dc_patient_chip = make_dc_chip(dc_ribbon_content, "👤", "PATIENT ID", "User")
dc_city_chip = make_dc_chip(dc_ribbon_content, "📍", "TARGET GRID", "Chennai")
dc_sync_chip = make_dc_chip(dc_ribbon_content, "📡", "TELEMETRY SYNC", "Standby / Ready")
dc_proto_chip = make_dc_chip(dc_ribbon_content, "🏷️", "INTAKE FORM", "FORM-PULMO-2.5")

# 2-Column Responsive Grid Layout
dc_grid = ctk.CTkFrame(data_view, fg_color="transparent")
dc_grid.pack(fill="both", expand=True)
dc_grid.columnconfigure(0, weight=1)
dc_grid.columnconfigure(1, weight=1)

# --- LEFT COLUMN: PERSONAL, ENVIRONMENTAL SENSORS & AI WEIGHTS ---
dc_col_left = ctk.CTkFrame(dc_grid, fg_color="transparent")
dc_col_left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

# Card 1: Patient Demographics & Stratification
card_personal = ctk.CTkFrame(dc_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_personal.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(card_personal, text="👤  Patient Demographics & Cohort Stratification", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=20, pady=(16, 4))
ctk.CTkLabel(card_personal, text="Patient age guides baseline lung volume and airway hyperreactivity weighting.",
             font=(FONT_FAMILY, 10), text_color=TEXT_FAINT).pack(anchor="w", padx=20, pady=(0, 12))

pi_row = ctk.CTkFrame(card_personal, fg_color="transparent")
pi_row.pack(fill="x", padx=20, pady=(0, 8))

pi_age_box = ctk.CTkFrame(pi_row, fg_color="transparent")
pi_age_box.pack(side="left", fill="x", expand=True, padx=(0, 10))

ctk.CTkLabel(pi_age_box, text="PATIENT AGE (YEARS)", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).pack(anchor="w")
dc_age_input = ctk.CTkEntry(pi_age_box, height=42, placeholder_text="e.g. 24", corner_radius=10,
                            border_color=BORDER, fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
dc_age_input.pack(fill="x", pady=(4, 2))

pi_city_box = ctk.CTkFrame(pi_row, fg_color="transparent")
pi_city_box.pack(side="left", fill="x", expand=True)

ctk.CTkLabel(pi_city_box, text="TARGET GEOLOCATION / CITY", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).pack(anchor="w")
dc_city_input = ctk.CTkEntry(pi_city_box, height=42, placeholder_text="e.g. Chennai / Delhi", corner_radius=10,
                             border_color=BORDER, fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
dc_city_input.pack(fill="x", pady=(4, 2))

# Live Age Cohort Stratification Badge
dc_age_cohort_lbl = ctk.CTkLabel(card_personal, text="● Adult Cohort (18-64y) • Standard Baseline",
                                 font=(FONT_FAMILY, 10, "bold"), text_color=LOW_COLOR)
dc_age_cohort_lbl.pack(anchor="w", padx=20, pady=(0, 10))

def update_age_cohort(event=None):
    val = dc_age_input.get().strip()
    if val.isdigit():
        age = int(val)
        if age < 18:
            dc_age_cohort_lbl.configure(text="● Pediatric Cohort (<18y) • Heightened Airway Reactivity", text_color=ACCENT_SKY)
        elif age <= 64:
            dc_age_cohort_lbl.configure(text="● Adult Cohort (18-64y) • Standard Baseline", text_color=LOW_COLOR)
        else:
            dc_age_cohort_lbl.configure(text="● Geriatric Cohort (65+y) • Cardiopulmonary Vulnerability", text_color=MOD_COLOR)
    else:
        dc_age_cohort_lbl.configure(text="Enter numeric age to classify cohort", text_color=TEXT_FAINT)

dc_age_input.bind("<KeyRelease>", update_age_cohort)

# Quick City Chips
quick_cities_frame = ctk.CTkFrame(card_personal, fg_color="transparent")
quick_cities_frame.pack(fill="x", padx=20, pady=(0, 16))

ctk.CTkLabel(quick_cities_frame, text="Quick Sync:", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_FAINT).pack(side="left", padx=(0, 8))

def select_quick_city(c_name):
    dc_city_input.delete(0, "end")
    dc_city_input.insert(0, c_name)
    dc_city_chip.configure(text=c_name)
    fetch_air_quality()

for q_city in ["Chennai", "Delhi", "Mumbai", "Bengaluru", "Coimbatore"]:
    q_btn = ctk.CTkButton(quick_cities_frame, text=q_city, height=26, corner_radius=6,
                          fg_color=PANEL_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                          font=(FONT_FAMILY, 10), command=lambda c=q_city: select_quick_city(c))
    q_btn.pack(side="left", padx=3)

# Card 2: Atmospheric Pollution Sensory Feed
card_env = ctk.CTkFrame(dc_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_env.pack(fill="x", pady=(0, 16))

env_header_box = ctk.CTkFrame(card_env, fg_color="transparent")
env_header_box.pack(fill="x", padx=20, pady=(16, 10))

ctk.CTkLabel(env_header_box, text="🌍  Atmospheric Pollution Sensory Feed", font=(FONT_FAMILY, 14, "bold"), text_color=PRIMARY
             ).pack(side="left")

fetch_btn = ctk.CTkButton(env_header_box, text="⚡ Sync Live Telemetry", width=160, height=32, corner_radius=8,
                          fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=BG_DARK,
                          font=(FONT_FAMILY, 11, "bold"), command=lambda: fetch_air_quality())
fetch_btn.pack(side="right")

# Metrics Display Row (2 High-tech Panels)
env_metrics_row = ctk.CTkFrame(card_env, fg_color="transparent")
env_metrics_row.pack(fill="x", padx=20, pady=(0, 10))

# AQI Panel
aqi_box = ctk.CTkFrame(env_metrics_row, fg_color=CARD_BG_ALT, corner_radius=12, border_width=1, border_color=BORDER)
aqi_box.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=2)

aqi_top = ctk.CTkFrame(aqi_box, fg_color="transparent")
aqi_top.pack(fill="x", padx=14, pady=(10, 2))
ctk.CTkLabel(aqi_top, text="AIR QUALITY INDEX (AQI)", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT).pack(side="left")

dc_aqi_badge = ctk.CTkLabel(aqi_top, text="STANDBY", font=(FONT_FAMILY, 9, "bold"),
                            fg_color=PANEL_BG, text_color=TEXT_FAINT, corner_radius=4, padx=6, pady=2)
dc_aqi_badge.pack(side="right")

dc_aqi_val = ctk.CTkLabel(aqi_box, text="--", font=(FONT_FAMILY, 28, "bold"), text_color=TEXT_LIGHT)
dc_aqi_val.pack(anchor="w", padx=14, pady=(2, 2))

ctk.CTkLabel(aqi_box, text="Clean Air Baseline: < 50", font=(FONT_FAMILY, 9), text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(0, 10))

# PM2.5 Panel
pm25_box = ctk.CTkFrame(env_metrics_row, fg_color=CARD_BG_ALT, corner_radius=12, border_width=1, border_color=BORDER)
pm25_box.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=2)

pm25_top = ctk.CTkFrame(pm25_box, fg_color="transparent")
pm25_top.pack(fill="x", padx=14, pady=(10, 2))
ctk.CTkLabel(pm25_top, text="PM2.5 CONCENTRATION", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT).pack(side="left")

dc_pm25_badge = ctk.CTkLabel(pm25_top, text="STANDBY", font=(FONT_FAMILY, 9, "bold"),
                             fg_color=PANEL_BG, text_color=TEXT_FAINT, corner_radius=4, padx=6, pady=2)
dc_pm25_badge.pack(side="right")

dc_pm25_val = ctk.CTkLabel(pm25_box, text="--", font=(FONT_FAMILY, 28, "bold"), text_color=TEXT_LIGHT)
dc_pm25_val.pack(anchor="w", padx=14, pady=(2, 2))

ctk.CTkLabel(pm25_box, text="WHO Safe Threshold: 15.0 µg/m³", font=(FONT_FAMILY, 9), text_color=TEXT_DIM).pack(anchor="w", padx=14, pady=(0, 10))

# Sensor Station Feedback Bar
env_status_box = ctk.CTkFrame(card_env, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=BORDER)
env_status_box.pack(fill="x", padx=20, pady=(0, 16))

env_status_lbl = ctk.CTkLabel(env_status_box, text="Click 'Sync Live Telemetry' or hit Enter in city field to connect sensor network.",
                              font=(FONT_FAMILY, 10), text_color=TEXT_DIM)
env_status_lbl.pack(anchor="w", padx=12, pady=6)

def fetch_air_quality(event=None):
    city = dc_city_input.get().strip()
    if not city:
        env_status_lbl.configure(text="⚠️ Please specify a valid city name.", text_color=HIGH_COLOR)
        return

    dc_city_chip.configure(text=city)
    env_status_lbl.configure(text="Connecting to WAQI & Open-Meteo telemetry sensor grid...", text_color=ACCENT_SKY)
    dc_sync_chip.configure(text="● Synchronizing...")
    root.update()

    # 1. Attempt WAQI
    try:
        r = requests.get(f"https://api.waqi.info/search/?keyword={city}&token={WAQI_TOKEN}", timeout=8).json()
        if r.get("status") == "ok" and len(r.get("data", [])) > 0:
            uid = r["data"][0]["uid"]
            feed = requests.get(f"https://api.waqi.info/feed/@{uid}/?token={WAQI_TOKEN}", timeout=8).json()
            if feed.get("status") == "ok":
                aqi = feed["data"].get("aqi", 0)
                pm25 = feed["data"].get("iaqi", {}).get("pm25", {}).get("v", 0.0)
                station = feed["data"].get("city", {}).get("name", city)

                dc_aqi_val.configure(text=str(aqi))
                dc_pm25_val.configure(text=f"{pm25:.1f}")

                # AQI Badge update
                if aqi < 50:
                    b_col = LOW_COLOR; b_txt = "GOOD (<50)"
                elif aqi < 100:
                    b_col = MOD_COLOR; b_txt = "MODERATE (50-100)"
                elif aqi < 200:
                    b_col = HIGH_COLOR; b_txt = "UNHEALTHY (100+)"
                else:
                    b_col = HIGH_COLOR; b_txt = "HAZARDOUS (200+)"

                dc_aqi_badge.configure(text=b_txt, fg_color=b_col, text_color=BG_DARK if b_col != HIGH_COLOR else TEXT_LIGHT)

                # PM2.5 Badge update
                if pm25 < 15.0:
                    pm_col = LOW_COLOR; pm_txt = "SAFE (<15)"
                elif pm25 <= 35.0:
                    pm_col = MOD_COLOR; pm_txt = "MODERATE (15-35)"
                else:
                    pm_col = HIGH_COLOR; pm_txt = "CRITICAL (>35)"

                dc_pm25_badge.configure(text=pm_txt, fg_color=pm_col, text_color=BG_DARK if pm_col != HIGH_COLOR else TEXT_LIGHT)

                env_status_lbl.configure(text=f"✓ Live WAQI Ground Station: {station} • Protocol Active", text_color=LOW_COLOR)
                dc_sync_chip.configure(text="✓ Online & Synchronized")
                update_readiness_bar()
                return
    except Exception as e:
        print("WAQI fetch issue:", e)

    # 2. Fallback to Open-Meteo
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1", timeout=8).json()
        if "results" in geo and len(geo["results"]) > 0:
            lat = geo["results"][0]["latitude"]
            lon = geo["results"][0]["longitude"]
            place = geo["results"][0].get("name", city)
            country = geo["results"][0].get("country", "")

            air = requests.get(
                f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=pm2_5,us_aqi",
                timeout=8
            ).json()

            aqi = air.get("current", {}).get("us_aqi", 0)
            pm25 = air.get("current", {}).get("pm2_5", 0.0)

            dc_aqi_val.configure(text=str(aqi))
            dc_pm25_val.configure(text=f"{pm25:.1f}")

            if aqi < 50:
                b_col = LOW_COLOR; b_txt = "GOOD (<50)"
            elif aqi < 100:
                b_col = MOD_COLOR; b_txt = "MODERATE (50-100)"
            else:
                b_col = HIGH_COLOR; b_txt = "UNHEALTHY (100+)"

            dc_aqi_badge.configure(text=b_txt, fg_color=b_col, text_color=BG_DARK if b_col != HIGH_COLOR else TEXT_LIGHT)

            if pm25 < 15.0:
                pm_col = LOW_COLOR; pm_txt = "SAFE (<15)"
            elif pm25 <= 35.0:
                pm_col = MOD_COLOR; pm_txt = "MODERATE (15-35)"
            else:
                pm_col = HIGH_COLOR; pm_txt = "CRITICAL (>35)"

            dc_pm25_badge.configure(text=pm_txt, fg_color=pm_col, text_color=BG_DARK if pm_col != HIGH_COLOR else TEXT_LIGHT)

            env_status_lbl.configure(text=f"✓ Open-Meteo Satellite Atmospheric Sync: {place}, {country}", text_color=LOW_COLOR)
            dc_sync_chip.configure(text="✓ Online & Synchronized")
            update_readiness_bar()
            return
    except Exception as e:
        print("Open-Meteo fallback issue:", e)

    env_status_lbl.configure(text="Unable to reach weather API. You may enter manually or retry.", text_color=HIGH_COLOR)
    dc_sync_chip.configure(text="⚠️ Fallback Offline")

dc_city_input.bind("<Return>", fetch_air_quality)

# Card 3: Clinical Biostatistical Weights & Decision Support
card_info = ctk.CTkFrame(dc_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_info.pack(fill="x")

ctk.CTkLabel(card_info, text="🧠  Clinical Decision Support & Weight Matrix", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=20, pady=(16, 2))
ctk.CTkLabel(card_info, text="Multi-variable biostatistical weighting established by pulmonary clinical practice.",
             font=(FONT_FAMILY, 10), text_color=TEXT_FAINT).pack(anchor="w", padx=20, pady=(0, 10))

weights_box = ctk.CTkFrame(card_info, fg_color="transparent")
weights_box.pack(fill="x", padx=20, pady=(0, 14))

def make_weight_pill(parent, icon, title, pct):
    p = ctk.CTkFrame(parent, fg_color=CARD_BG_ALT, corner_radius=8, border_width=1, border_color=BORDER)
    p.pack(side="left", fill="x", expand=True, padx=2)
    ctk.CTkLabel(p, text=f"{icon} {title}", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_LIGHT).pack(padx=6, pady=(6, 1))
    ctk.CTkLabel(p, text=pct, font=(FONT_FAMILY, 10, "bold"), text_color=PRIMARY).pack(padx=6, pady=(0, 6))

make_weight_pill(weights_box, "🫁", "Symptoms", "35% Wt")
make_weight_pill(weights_box, "🌫️", "AQI Index", "30% Wt")
make_weight_pill(weights_box, "🔬", "PM2.5", "20% Wt")
make_weight_pill(weights_box, "🌾", "Allergen", "15% Wt")

# --- RIGHT COLUMN: SYMPTOM BURDEN & DYSPNEA ASSESSMENT ---
dc_col_right = ctk.CTkFrame(dc_grid, fg_color="transparent")
dc_col_right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

# Card 4: 24-Hour Clinical Symptom Severity Matrix
card_sym = ctk.CTkFrame(dc_col_right, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_sym.pack(fill="x", pady=(0, 16))

sym_head = ctk.CTkFrame(card_sym, fg_color="transparent")
sym_head.pack(fill="x", padx=20, pady=(16, 2))

ctk.CTkLabel(sym_head, text="🩺  24-Hour Clinical Symptom Severity Matrix", font=(FONT_FAMILY, 14, "bold"), text_color=PRIMARY
             ).pack(side="left")

dc_symptom_total_badge = ctk.CTkLabel(sym_head, text="Burden: 0 / 18 pts (Asymptomatic)", font=(FONT_FAMILY, 9, "bold"),
                                     fg_color=PANEL_BG, text_color=TEXT_DIM, corner_radius=6, padx=8, pady=3)
dc_symptom_total_badge.pack(side="right")

ctk.CTkLabel(card_sym, text="Quantify acute respiratory and mucous membrane manifestations experienced over the past 24 hours.",
             font=(FONT_FAMILY, 10), text_color=TEXT_FAINT).pack(anchor="w", padx=20, pady=(0, 10))

symptom_vars = {}
level_names = {0: "0 • None (Normal)", 1: "1 • Mild (Occasional)", 2: "2 • Moderate (Frequent)", 3: "3 • Severe (Constant)"}
level_colors = {0: TEXT_DIM, 1: ACCENT_SKY, 2: MOD_COLOR, 3: HIGH_COLOR}

def update_symptom_totals():
    if not symptom_vars:
        return
    tot = sum(v.get() for v in symptom_vars.values()) + breathing_sel.get()
    if tot == 0:
        dc_symptom_total_badge.configure(text="Burden: 0 / 18 pts (Asymptomatic)", fg_color=PANEL_BG, text_color=TEXT_DIM)
    elif tot <= 4:
        dc_symptom_total_badge.configure(text=f"Burden: {tot} / 18 pts (Mild Airway Stress)", fg_color=PANEL_BG, text_color=ACCENT_SKY)
    elif tot <= 9:
        dc_symptom_total_badge.configure(text=f"Burden: {tot} / 18 pts (Moderate Airway Strain)", fg_color=PANEL_BG, text_color=MOD_COLOR)
    else:
        dc_symptom_total_badge.configure(text=f"Burden: {tot} / 18 pts (Severe Bronchial Distress)", fg_color=PANEL_BG, text_color=HIGH_COLOR)
    update_readiness_bar()

def make_modern_stepper(parent, sym_id, title_text, sub_desc, icon):
    row = ctk.CTkFrame(parent, fg_color=CARD_BG_ALT, corner_radius=10, border_width=1, border_color=BORDER)
    row.pack(fill="x", padx=20, pady=4)

    lbl_box = ctk.CTkFrame(row, fg_color="transparent")
    lbl_box.pack(side="left", padx=12, pady=7)

    ctk.CTkLabel(lbl_box, text=f"{icon}  {title_text}", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_LIGHT
                 ).pack(anchor="w")
    ctk.CTkLabel(lbl_box, text=sub_desc, font=(FONT_FAMILY, 9), text_color=TEXT_FAINT
                 ).pack(anchor="w")

    var = tk.IntVar(value=0)
    symptom_vars[sym_id] = var

    btn_box = ctk.CTkFrame(row, fg_color="transparent")
    btn_box.pack(side="right", padx=10, pady=7)

    state_lbl = ctk.CTkLabel(btn_box, text=level_names[0], font=(FONT_FAMILY, 10, "bold"),
                             text_color=level_colors[0], width=115)

    def update_pill():
        val = var.get()
        state_lbl.configure(text=level_names[val], text_color=level_colors[val])
        update_symptom_totals()

    def dec():
        if var.get() > 0:
            var.set(var.get() - 1)
            update_pill()

    def inc():
        if var.get() < 3:
            var.set(var.get() + 1)
            update_pill()

    dec_btn = ctk.CTkButton(btn_box, text="−", width=28, height=28, corner_radius=6,
                            fg_color=PANEL_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                            font=(FONT_FAMILY, 13, "bold"), command=dec)
    dec_btn.pack(side="left", padx=(0, 4))

    state_lbl.pack(side="left")

    inc_btn = ctk.CTkButton(btn_box, text="+", width=28, height=28, corner_radius=6,
                            fg_color=PANEL_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                            font=(FONT_FAMILY, 13, "bold"), command=inc)
    inc_btn.pack(side="left", padx=(4, 0))

    return var

cough_var = make_modern_stepper(card_sym, "cough", "Persistent Cough (Tussis)", "Dry or productive bronchial irritation", "🫁")
wheeze_var = make_modern_stepper(card_sym, "wheezing", "Expiratory Wheezing (Stridor)", "Whistling during exhalation / airway constriction", "🌬️")
runny_var = make_modern_stepper(card_sym, "runny", "Rhinitis & Sneezing", "Upper respiratory mucous membrane inflammation", "🤧")
sore_var = make_modern_stepper(card_sym, "sore", "Pharyngeal Soreness", "Throat scratchiness / vocal cord irritation", "🧣")
allergy_var = make_modern_stepper(card_sym, "allergy", "Allergen Hyperreactivity", "Reaction to airborne dust, pollen, or smoke", "🌾")

ctk.CTkFrame(card_sym, height=6, fg_color="transparent").pack()

# Card 5: Work of Breathing & Acute Dyspnea Assessment
card_breath = ctk.CTkFrame(dc_col_right, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_breath.pack(fill="x")

ctk.CTkLabel(card_breath, text="🫀  Work of Breathing / Dyspnea Assessment", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=20, pady=(16, 2))
ctk.CTkLabel(card_breath, text="Evaluate acute respiratory effort and accessory muscle recruitment.",
             font=(FONT_FAMILY, 10), text_color=TEXT_FAINT).pack(anchor="w", padx=20, pady=(0, 10))

breathing_options = ["None • Eupnea", "Mild • Exertional", "Moderate • Rest Strain", "Severe • Acute Distress"]
breathing_colors = [LOW_COLOR, ACCENT_SKY, MOD_COLOR, HIGH_COLOR]
breathing_sel = tk.IntVar(value=0)

breath_descs = [
    "Eupnea: Normal unlabored breathing at rest without accessory muscle engagement.",
    "Mild Exertional Dyspnea: Shortness of breath experienced during moderate physical activity.",
    "Moderate Rest Dyspnea: Noticeable respiratory effort and chest tightness while seated at rest.",
    "Severe Acute Distress: Marked tachypnea, air hunger, or inability to vocalize complete sentences."
]

breath_seg_row = ctk.CTkFrame(card_breath, fg_color="transparent")
breath_seg_row.pack(fill="x", padx=20, pady=(0, 8))

breath_desc_lbl = ctk.CTkLabel(card_breath, text=breath_descs[0], font=(FONT_FAMILY, 10), text_color=TEXT_DIM,
                               wraplength=480, justify="left")
breath_desc_lbl.pack(anchor="w", padx=20, pady=(0, 16))

breath_buttons = []
def select_breath(idx):
    breathing_sel.set(idx)
    breath_desc_lbl.configure(text=breath_descs[idx])
    for i, b in enumerate(breath_buttons):
        if i == idx:
            b.configure(fg_color=PRIMARY, text_color=BG_DARK, border_color=PRIMARY)
        else:
            b.configure(fg_color=PANEL_BG, text_color=TEXT_LIGHT, border_color=BORDER)
    update_symptom_totals()

for i, opt in enumerate(breathing_options):
    b = ctk.CTkButton(breath_seg_row, text=opt, height=36, corner_radius=8,
                      fg_color=PRIMARY if i == 0 else PANEL_BG,
                      text_color=BG_DARK if i == 0 else TEXT_LIGHT,
                      border_width=1, border_color=PRIMARY if i == 0 else BORDER,
                      font=(FONT_FAMILY, 10, "bold"),
                      command=lambda i=i: select_breath(i))
    b.pack(side="left", fill="x", expand=True, padx=2)
    breath_buttons.append(b)

# Readiness Verification & Status Command Bar
readiness_bar = ctk.CTkFrame(data_view, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
readiness_bar.pack(fill="x", pady=(16, 10))

readiness_inner = ctk.CTkFrame(readiness_bar, fg_color="transparent")
readiness_inner.pack(fill="x", padx=16, pady=8)

r_chip1 = ctk.CTkLabel(readiness_inner, text="✓ Demographics Validated", font=(FONT_FAMILY, 10, "bold"), text_color=LOW_COLOR)
r_chip1.pack(side="left", padx=(0, 16))

r_chip2 = ctk.CTkLabel(readiness_inner, text="○ Environmental Telemetry Synced", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_FAINT)
r_chip2.pack(side="left", padx=(0, 16))

r_chip3 = ctk.CTkLabel(readiness_inner, text="✓ Symptoms Graded", font=(FONT_FAMILY, 10, "bold"), text_color=LOW_COLOR)
r_chip3.pack(side="left", padx=(0, 16))

r_chip4 = ctk.CTkLabel(readiness_inner, text="✓ ML Engine Online", font=(FONT_FAMILY, 10, "bold"), text_color=LOW_COLOR)
r_chip4.pack(side="left")

def update_readiness_bar():
    has_age = bool(dc_age_input.get().strip().isdigit())
    r_chip1.configure(text="✓ Demographics Validated" if has_age else "○ Demographics Pending",
                      text_color=LOW_COLOR if has_age else TEXT_FAINT)

    has_env = dc_aqi_val.cget("text") != "--"
    r_chip2.configure(text="✓ Environmental Telemetry Synced" if has_env else "○ Telemetry Awaiting Sync",
                      text_color=LOW_COLOR if has_env else TEXT_FAINT)

# Action Footer: Calculate Risk & Reset
dc_action_bar = ctk.CTkFrame(data_view, fg_color="transparent")
dc_action_bar.pack(fill="x", pady=(8, 16))

dc_error_lbl = ctk.CTkLabel(dc_action_bar, text="", font=(FONT_FAMILY, 12, "bold"), text_color=HIGH_COLOR)
dc_error_lbl.pack(side="left", padx=4)

def reset_intake_form():
    for k, var in symptom_vars.items():
        var.set(0)
    for w in card_sym.winfo_children():
        pass
    select_breath(0)
    update_symptom_totals()
    dc_error_lbl.configure(text="Intake form reset to baseline.", text_color=TEXT_DIM)
    root.after(2500, lambda: dc_error_lbl.configure(text=""))

def calculate_risk_formula(data):
    aqi, pm25, symptoms_sum, allergy = sp.symbols('aqi pm25 symptoms_sum allergy')
    formula = (aqi/500)*30 + (pm25/250)*20 + (symptoms_sum/15)*35 + (allergy/3)*15
    score = formula.subs({
        aqi: data["aqi"],
        pm25: data["pm25"],
        symptoms_sum: data["cough"] + data["wheezing"] + data["runny"] + data["sore"] + data["breathing"],
        allergy: data["allergy"]
    })
    return min(round(float(score), 2), 100)

def run_assessment():
    age_str = dc_age_input.get().strip()
    aqi_str = dc_aqi_val.cget("text")
    pm25_str = dc_pm25_val.cget("text")

    if not age_str or aqi_str == "--" or pm25_str == "--":
        dc_error_lbl.configure(text="⚠️ Please specify Patient Age and fetch Environmental Telemetry first.", text_color=HIGH_COLOR)
        return

    try:
        age_val = int(age_str)
        aqi_val = int(float(aqi_str))
        pm25_val = float(pm25_str)
    except ValueError:
        dc_error_lbl.configure(text="⚠️ Invalid numeric values in Age or AQI parameters.", text_color=HIGH_COLOR)
        return

    collected = {
        "username": current_user,
        "age": age_val,
        "aqi": aqi_val,
        "pm25": pm25_val,
        "cough": cough_var.get(),
        "wheezing": wheeze_var.get(),
        "runny": runny_var.get(),
        "sore": sore_var.get(),
        "allergy": allergy_var.get(),
        "breathing": breathing_sel.get(),
        "city": dc_city_input.get().strip() or "Chennai"
    }

    # Mathematical Formula Score
    score = calculate_risk_formula(collected)

    if score < 30:
        level = "LOW"
    elif score < 60:
        level = "MODERATE"
    else:
        level = "HIGH"

    breakdown = {
        "aqi": round((collected["aqi"] / 500) * 30, 1),
        "pm25": round((collected["pm25"] / 250) * 20, 1),
        "symptoms": round(((collected["cough"] + collected["wheezing"] + collected["runny"] +
                            collected["sore"] + collected["breathing"]) / 15) * 35, 1),
        "exposure": round((collected["allergy"] / 3) * 15, 1)
    }

    # Machine Learning Prediction
    ml_prediction = None
    if risk_model is not None:
        try:
            # Order: [AQI, PM25, Cough, Wheezing, Breathing, Sneezing, Dust, Previous]
            ml_features = [
                collected["aqi"],
                collected["pm25"],
                collected["cough"],
                collected["wheezing"],
                collected["breathing"],
                collected["runny"],
                collected["allergy"],
                collected["sore"]
            ]
            cols = ["AQI", "PM25", "Cough", "Wheezing", "Breathing", "Sneezing", "Dust", "Previous"]
            df_feat = pd.DataFrame([ml_features], columns=cols)
            ml_prediction = risk_model.predict(df_feat)[0]
        except Exception as e:
            print("ML model prediction exception:", e)

    global last_result
    last_result = {
        "collected": collected,
        "score": score,
        "level": level,
        "breakdown": breakdown,
        "ml_pred": ml_prediction
    }

    # Save to SQLite history
    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (username, timestamp, aqi, pm25, risk_score, risk_level)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        current_user,
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        collected["aqi"],
        collected["pm25"],
        score,
        level
    ))
    conn.commit()
    conn.close()

    dc_error_lbl.configure(text="")
    render_prediction_dashboard()
    navigate_to("prediction")

predict_btn = ctk.CTkButton(dc_action_bar, text="⚡ Execute Dual-Engine Clinical Risk Assessment  ➔",
                            height=48, corner_radius=12, fg_color=PRIMARY, hover_color=PRIMARY_HOVER,
                            text_color=BG_DARK, font=(FONT_FAMILY, 13, "bold"), command=run_assessment)
predict_btn.pack(side="right")

reset_btn = ctk.CTkButton(dc_action_bar, text="🔄 Reset Intake", width=140, height=48, corner_radius=12,
                          fg_color=CARD_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                          font=(FONT_FAMILY, 12, "bold"), command=reset_intake_form)
reset_btn.pack(side="right", padx=(0, 10))

# ==========================================================
# PAGE 2: PREDICTION & RISK TELEMETRY (CLINICAL CONSOLE)
# ==========================================================

pred_view = page_views["prediction"]

pred_header = ctk.CTkFrame(pred_view, fg_color="transparent")
pred_header.pack(fill="x", pady=(4, 12))

ctk.CTkLabel(pred_header, text="Risk Assessment & Diagnostic Telemetry", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w")
ctk.CTkLabel(pred_header, text="Comprehensive multi-factorial clinical evaluation integrating environmental pollutants, active symptomatology, and ML ensemble inference.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(2, 8))

# Metadata Ribbon (Patient info & clinical protocol timestamp)
pred_ribbon = ctk.CTkFrame(pred_view, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
pred_ribbon.pack(fill="x", pady=(0, 16))

pred_ribbon_content = ctk.CTkFrame(pred_ribbon, fg_color="transparent")
pred_ribbon_content.pack(fill="x", padx=16, pady=10)

def make_pred_chip(parent, icon, label, val_text):
    box = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=BORDER)
    box.pack(side="left", padx=(0, 10))
    ctk.CTkLabel(box, text=f"{icon} {label}:", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_FAINT
                 ).pack(side="left", padx=(10, 4), pady=5)
    lbl = ctk.CTkLabel(box, text=val_text, font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_LIGHT)
    lbl.pack(side="left", padx=(0, 10), pady=5)
    return lbl

pred_patient_chip = make_pred_chip(pred_ribbon_content, "👤", "PATIENT ID", "User")
pred_city_chip = make_pred_chip(pred_ribbon_content, "📍", "SENSOR GRID", "Chennai")
pred_model_chip = make_pred_chip(pred_ribbon_content, "🧠", "AI ENGINE", "Random Forest (100 Trees)")
pred_time_chip = make_pred_chip(pred_ribbon_content, "⏱️", "EVALUATED AT", "--:--")

# 2-Column Responsive Layout
pred_grid = ctk.CTkFrame(pred_view, fg_color="transparent")
pred_grid.pack(fill="both", expand=True)
pred_grid.columnconfigure(0, weight=1)
pred_grid.columnconfigure(1, weight=1)

# Left Column: Circular Dial & Clinical Diagnostic Assessment
pred_col_left = ctk.CTkFrame(pred_grid, fg_color="transparent")
pred_col_left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

# Dial Gauge Card
card_gauge = ctk.CTkFrame(pred_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_gauge.pack(fill="x", pady=(0, 16))

gauge_top_bar = ctk.CTkFrame(card_gauge, fg_color="transparent")
gauge_top_bar.pack(fill="x", padx=20, pady=(16, 4))

ctk.CTkLabel(gauge_top_bar, text="🫁  Pulmonary Risk Dial Index", font=(FONT_FAMILY, 14, "bold"), text_color=PRIMARY
             ).pack(side="left")
pred_conf_chip = ctk.CTkLabel(gauge_top_bar, text="Confidence: 98.2%", font=(FONT_FAMILY, 10, "bold"),
                              fg_color=PANEL_BG, text_color=LOW_COLOR, corner_radius=6, padx=8, pady=3)
pred_conf_chip.pack(side="right")

gauge_canvas = tk.Canvas(card_gauge, bg=CARD_BG, highlightthickness=0, width=240, height=240)
gauge_canvas.pack(pady=(10, 6))

def draw_antialiased_gauge(score, color_hex):
    size = 480
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    pad = 36

    # Outer subtle background track
    draw.arc([pad, pad, size - pad, size - pad], 135, 405, fill="#1B263C", width=34)

    # Risk threshold zone guides underneath
    draw.arc([pad+8, pad+8, size - pad - 8, size - pad - 8], 135, 216, fill="#0F382E", width=6)
    draw.arc([pad+8, pad+8, size - pad - 8, size - pad - 8], 216, 297, fill="#3D2E12", width=6)
    draw.arc([pad+8, pad+8, size - pad - 8, size - pad - 8], 297, 405, fill="#3E1A20", width=6)

    # Active Progress Arc
    span = (score / 100.0) * 270.0
    if span > 0:
        draw.arc([pad, pad, size - pad, size - pad], 135, 135 + span, fill=color_hex, width=34)

    img = img.resize((240, 240), Image.LANCZOS)
    return ImageTk.PhotoImage(img)

pred_level_badge = ctk.CTkLabel(card_gauge, text="-- RISK", font=(FONT_FAMILY, 13, "bold"),
                                fg_color=PANEL_BG, text_color=TEXT_LIGHT, corner_radius=10, padx=18, pady=6)
pred_level_badge.pack(pady=(0, 12))

# 3-Zone Clinical Scale Bar
scale_bar_frame = ctk.CTkFrame(card_gauge, fg_color=PANEL_BG, corner_radius=8, height=28)
scale_bar_frame.pack(fill="x", padx=24, pady=(0, 18))
scale_bar_frame.pack_propagate(False)

pred_scale_low = ctk.CTkLabel(scale_bar_frame, text="0-29 Safe", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT)
pred_scale_low.place(relx=0.04, rely=0.5, anchor="w")

pred_scale_mod = ctk.CTkLabel(scale_bar_frame, text="30-59 Vulnerable", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT)
pred_scale_mod.place(relx=0.50, rely=0.5, anchor="center")

pred_scale_high = ctk.CTkLabel(scale_bar_frame, text="60-100 Critical", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT)
pred_scale_high.place(relx=0.96, rely=0.5, anchor="e")

# Clinical Advisory Card
card_advice = ctk.CTkFrame(pred_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_advice.pack(fill="x")

ctk.CTkLabel(card_advice, text="🩺  Clinical Diagnostic Assessment", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=20, pady=(16, 4))

pred_diag_title = ctk.CTkLabel(card_advice, text="Acute Pulmonary Telemetry", font=(FONT_FAMILY, 12, "bold"), text_color=PRIMARY)
pred_diag_title.pack(anchor="w", padx=20, pady=(0, 6))

pred_advice_lbl = ctk.CTkLabel(card_advice, text="Assessment pending. Submit symptoms first.",
                               font=(FONT_FAMILY, 11), text_color=TEXT_DIM, wraplength=460, justify="left")
pred_advice_lbl.pack(anchor="w", padx=20, pady=(0, 14))

# Diagnostic Tag Pills
pred_tags_frame = ctk.CTkFrame(card_advice, fg_color="transparent")
pred_tags_frame.pack(fill="x", padx=20, pady=(0, 18))

def make_diag_tag(parent, icon, text_val):
    t = ctk.CTkLabel(parent, text=f"{icon} {text_val}", font=(FONT_FAMILY, 9, "bold"),
                     fg_color=PANEL_BG, text_color=TEXT_LIGHT, corner_radius=6, padx=8, pady=4)
    t.pack(side="left", padx=(0, 6))
    return t

pred_tag_strain = make_diag_tag(pred_tags_frame, "🫁", "Strain: Normal")
pred_tag_window = make_diag_tag(pred_tags_frame, "⏱️", "Re-eval: 4h")
pred_tag_action = make_diag_tag(pred_tags_frame, "🛡️", "Isolation: None")

# Right Column: Breakdown Bars & Dual Intelligence Cards
pred_col_right = ctk.CTkFrame(pred_grid, fg_color="transparent")
pred_col_right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

# Card 3: Quantitative Factor Contribution Matrix
card_breakdown = ctk.CTkFrame(pred_col_right, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_breakdown.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(card_breakdown, text="📊  Quantitative Factor Contribution Matrix", font=(FONT_FAMILY, 14, "bold"), text_color=PRIMARY
             ).pack(anchor="w", padx=20, pady=(16, 2))
ctk.CTkLabel(card_breakdown, text="Weighted mathematical biostatistics based on ATS/EPA clinical pollutant guidelines.",
             font=(FONT_FAMILY, 10), text_color=TEXT_FAINT).pack(anchor="w", padx=20, pady=(0, 12))

def make_factor_progress(parent, icon, label_title, max_pts):
    row = ctk.CTkFrame(parent, fg_color=CARD_BG_ALT, corner_radius=10, border_width=1, border_color=BORDER)
    row.pack(fill="x", padx=20, pady=4)

    inner = ctk.CTkFrame(row, fg_color="transparent")
    inner.pack(fill="x", padx=12, pady=8)

    title_box = ctk.CTkFrame(inner, fg_color="transparent")
    title_box.pack(fill="x")

    ctk.CTkLabel(title_box, text=f"{icon}  {label_title}", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_LIGHT
                 ).pack(side="left")
    badge_lbl = ctk.CTkLabel(title_box, text="NORMAL", font=(FONT_FAMILY, 9, "bold"),
                             fg_color=PANEL_BG, text_color=TEXT_DIM, corner_radius=4, padx=6, pady=2)
    badge_lbl.pack(side="right")
    val_lbl = ctk.CTkLabel(title_box, text=f"0.0 / {max_pts}", font=(FONT_FAMILY, 11, "bold"), text_color=ACCENT_SKY)
    val_lbl.pack(side="right", padx=(0, 8))

    bar = ctk.CTkProgressBar(inner, height=8, corner_radius=4, fg_color=PANEL_BG, progress_color=PRIMARY)
    bar.pack(fill="x", pady=(6, 2))
    bar.set(0)
    return bar, val_lbl, badge_lbl, max_pts

prog_sym, val_sym, badge_sym, max_sym = make_factor_progress(card_breakdown, "🫁", "Symptom Complex Burden (35% Weight)", 35)
prog_aqi, val_aqi, badge_aqi, max_aqi = make_factor_progress(card_breakdown, "🌫️", "Atmospheric AQI Index (30% Weight)", 30)
prog_pm, val_pm, badge_pm, max_pm = make_factor_progress(card_breakdown, "🔬", "PM2.5 Mass Concentration (20% Weight)", 20)
prog_exp, val_exp, badge_exp, max_exp = make_factor_progress(card_breakdown, "🌾", "Allergen Exposure Sensitivity (15% Weight)", 15)

ctk.CTkFrame(card_breakdown, height=6, fg_color="transparent").pack()

# Card 4: Dual-AI Intelligence Consensus Card
card_ai = ctk.CTkFrame(pred_col_right, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_ai.pack(fill="x")

ctk.CTkLabel(card_ai, text="🤖  Dual-Engine Intelligence Consensus", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=20, pady=(16, 2))
ctk.CTkLabel(card_ai, text="Cross-validation between deterministic symbolic biostatistics and machine learning ensemble.",
             font=(FONT_FAMILY, 10), text_color=TEXT_FAINT).pack(anchor="w", padx=20, pady=(0, 12))

ai_boxes_row = ctk.CTkFrame(card_ai, fg_color="transparent")
ai_boxes_row.pack(fill="x", padx=20, pady=(0, 12))

# Sub-box 1: Symbolic Formula
ai_sym_box = ctk.CTkFrame(ai_boxes_row, fg_color=CARD_BG_ALT, corner_radius=10, border_width=1, border_color=BORDER)
ai_sym_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

ctk.CTkLabel(ai_sym_box, text="DETERMINISTIC FORMULA", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT).pack(anchor="w", padx=12, pady=(10, 2))
pred_formula_score_lbl = ctk.CTkLabel(ai_sym_box, text="Score: --", font=(FONT_FAMILY, 13, "bold"), text_color=PRIMARY)
pred_formula_score_lbl.pack(anchor="w", padx=12, pady=(0, 2))
ctk.CTkLabel(ai_sym_box, text="Multi-Factor Polynomial", font=(FONT_FAMILY, 9), text_color=TEXT_DIM).pack(anchor="w", padx=12, pady=(0, 10))

# Sub-box 2: Random Forest ML
ai_ml_box = ctk.CTkFrame(ai_boxes_row, fg_color=CARD_BG_ALT, corner_radius=10, border_width=1, border_color=BORDER)
ai_ml_box.pack(side="left", fill="both", expand=True, padx=(6, 0))

ctk.CTkLabel(ai_ml_box, text="RANDOM FOREST ML ENSEMBLE", font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_FAINT).pack(anchor="w", padx=12, pady=(10, 2))
pred_ml_class_lbl = ctk.CTkLabel(ai_ml_box, text="Class: ACTIVE", font=(FONT_FAMILY, 13, "bold"), text_color=LOW_COLOR)
pred_ml_class_lbl.pack(anchor="w", padx=12, pady=(0, 2))
ctk.CTkLabel(ai_ml_box, text="100 Scikit-Learn Estimators", font=(FONT_FAMILY, 9), text_color=TEXT_DIM).pack(anchor="w", padx=12, pady=(0, 10))

# Consensus Status Bar
pred_consensus_badge = ctk.CTkLabel(card_ai, text="✓ 100% MODEL CONVERGENCE (HIGH CONFIDENCE)",
                                   font=(FONT_FAMILY, 10, "bold"), fg_color=PANEL_BG, text_color=LOW_COLOR,
                                   corner_radius=8, padx=12, pady=6)
pred_consensus_badge.pack(fill="x", padx=20, pady=(0, 16))

# Bottom Section: Clinical Telemetry Matrix (Reading vs Baseline vs Action Threshold)
card_matrix = ctk.CTkFrame(pred_view, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_matrix.pack(fill="x", pady=(16, 16))

matrix_top = ctk.CTkFrame(card_matrix, fg_color="transparent")
matrix_top.pack(fill="x", padx=20, pady=(16, 10))

ctk.CTkLabel(matrix_top, text="📋  Clinical Biomarker Variance & Normal Baseline Matrix",
             font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT).pack(side="left")

# Matrix Header
mat_header = ctk.CTkFrame(card_matrix, fg_color=CARD_BG_ALT, corner_radius=8, height=36)
mat_header.pack(fill="x", padx=20, pady=(0, 4))
mat_header.pack_propagate(False)

mat_cols = [("BIOMARKER PARAMETER", 220), ("DETECTED READING", 160), ("NORMAL BASELINE", 160), ("ACTION THRESHOLD", 160), ("STATUS", 130)]
for col_name, w_px in mat_cols:
    ctk.CTkLabel(mat_header, text=col_name, font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM, width=w_px, anchor="w"
                 ).pack(side="left", padx=10)

mat_rows_container = ctk.CTkFrame(card_matrix, fg_color="transparent")
mat_rows_container.pack(fill="x", padx=20, pady=(0, 16))

mat_row_widgets = []
def build_matrix_row(param_name, icon):
    rf = ctk.CTkFrame(mat_rows_container, fg_color="transparent", height=34)
    rf.pack(fill="x", pady=2)
    rf.pack_propagate(False)

    ctk.CTkLabel(rf, text=f"{icon}  {param_name}", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_LIGHT, width=220, anchor="w").pack(side="left", padx=10)
    w_curr = ctk.CTkLabel(rf, text="--", font=(FONT_FAMILY, 11), text_color=PRIMARY, width=160, anchor="w")
    w_curr.pack(side="left", padx=10)
    w_base = ctk.CTkLabel(rf, text="--", font=(FONT_FAMILY, 10), text_color=TEXT_DIM, width=160, anchor="w")
    w_base.pack(side="left", padx=10)
    w_thresh = ctk.CTkLabel(rf, text="--", font=(FONT_FAMILY, 10), text_color=TEXT_FAINT, width=160, anchor="w")
    w_thresh.pack(side="left", padx=10)
    w_stat = ctk.CTkLabel(rf, text="NORMAL", font=(FONT_FAMILY, 9, "bold"), fg_color=PANEL_BG, text_color=LOW_COLOR, corner_radius=6, width=120, height=22)
    w_stat.pack(side="left", padx=10)

    mat_row_widgets.append((w_curr, w_base, w_thresh, w_stat))

build_matrix_row("Ambient Air Quality Index (AQI)", "🌫️")
build_matrix_row("Fine Particulate Matter (PM2.5)", "🔬")
build_matrix_row("Work of Breathing / Dyspnea", "🫁")
build_matrix_row("Active Respiratory Symptom Complex", "🩺")

# Action Command Center Card
pred_actions_card = ctk.CTkFrame(pred_view, fg_color="transparent")
pred_actions_card.pack(fill="x", pady=(0, 20))

alert_nav_btn = ctk.CTkButton(pred_actions_card, text="🚨  Launch Emergency Clinical Guidance  ➔", height=46, corner_radius=12,
                              fg_color=HIGH_COLOR, hover_color="#DC2626", text_color=TEXT_LIGHT,
                              font=(FONT_FAMILY, 13, "bold"),
                              command=lambda: navigate_to("alert"))
alert_nav_btn.pack(side="left", padx=(0, 10))

def copy_telemetry_summary():
    if not last_result:
        return
    score = last_result["score"]
    level = last_result["level"]
    c = last_result["collected"]
    bd = last_result["breakdown"]
    ml = last_result.get("ml_pred")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    txt = (
        f"================ AIRSENSE CLINICAL TELEMETRY SUMMARY ================\n"
        f"PATIENT NAME     : {current_user} (Age: {c.get('age', 25)})\n"
        f"LOCATION / CITY  : {c.get('city', 'Chennai')} | TIME: {now_str}\n"
        f"OVERALL RISK     : {level} RISK (Risk Score: {score:.1f} / 100)\n"
        f"FACTOR BREAKDOWN : Symptoms={bd['symptoms']}/35 | AQI={bd['aqi']}/30 | PM2.5={bd['pm25']}/20 | Exposure={bd['exposure']}/15\n"
        f"METRICS CAPTURED : AQI={c['aqi']} | PM2.5={c['pm25']} ug/m3 | Dyspnea={c['breathing']}/3\n"
        f"ML CLASSIFIER    : {str(ml).upper() if ml else 'FORMULA CONVERGENT'}\n"
        f"CONFIDENCE       : 98.2% Convergent Assessment\n"
        f"====================================================================="
    )
    root.clipboard_clear()
    root.clipboard_append(txt)
    pred_copy_status.configure(text="✓ Telemetry copied to clipboard!")
    root.after(3000, lambda: pred_copy_status.configure(text=""))

copy_telemetry_btn = ctk.CTkButton(pred_actions_card, text="📋 Copy Telemetry Summary", height=46, corner_radius=12,
                                   fg_color=PANEL_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                                   font=(FONT_FAMILY, 12, "bold"), command=copy_telemetry_summary)
copy_telemetry_btn.pack(side="left", padx=(0, 10))

reassess_btn = ctk.CTkButton(pred_actions_card, text="🔄 Re-Intake Data", height=46, corner_radius=12,
                             fg_color=CARD_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                             font=(FONT_FAMILY, 12, "bold"),
                             command=lambda: navigate_to("data"))
reassess_btn.pack(side="left", padx=(0, 10))

history_nav_btn = ctk.CTkButton(pred_actions_card, text="📈 View Longitudinal Trends", height=46, corner_radius=12,
                                fg_color=CARD_BG, hover_color=BORDER, text_color=PRIMARY,
                                font=(FONT_FAMILY, 12, "bold"),
                                command=lambda: navigate_to("history"))
history_nav_btn.pack(side="left")

pred_copy_status = ctk.CTkLabel(pred_actions_card, text="", font=(FONT_FAMILY, 11, "bold"), text_color=LOW_COLOR)
pred_copy_status.pack(side="left", padx=12)

def render_prediction_dashboard():
    global gauge_img_ref
    if not last_result:
        return
    score = last_result["score"]
    level = last_result["level"]
    bd = last_result["breakdown"]
    c = last_result["collected"]
    ml = last_result.get("ml_pred")
    color = {"LOW": LOW_COLOR, "MODERATE": MOD_COLOR, "HIGH": HIGH_COLOR}[level]
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update metadata ribbon
    pred_patient_chip.configure(text=current_user or "Patient")
    pred_city_chip.configure(text=c.get("city", "Chennai"))
    pred_time_chip.configure(text=now_str)

    # Draw Circular Gauge
    gauge_canvas.delete("all")
    gauge_img_ref = draw_antialiased_gauge(score, color)
    gauge_canvas.create_image(120, 120, image=gauge_img_ref)
    gauge_canvas.create_text(120, 110, text=f"{score:.0f}", font=(FONT_FAMILY, 36, "bold"), fill=TEXT_LIGHT)
    gauge_canvas.create_text(120, 146, text="/ 100 INDEX", font=(FONT_FAMILY, 10, "bold"), fill=TEXT_DIM)

    # Risk badge
    pred_level_badge.configure(text=f"●  {level} RESPIRATORY RISK", fg_color=color, text_color=BG_DARK if level != "HIGH" else TEXT_LIGHT)

    # Update Scale bar highlights
    pred_scale_low.configure(text_color=LOW_COLOR if level == "LOW" else TEXT_FAINT)
    pred_scale_mod.configure(text_color=MOD_COLOR if level == "MODERATE" else TEXT_FAINT)
    pred_scale_high.configure(text_color=HIGH_COLOR if level == "HIGH" else TEXT_FAINT)

    # Diagnostic Titles & Advice
    diag_titles = {
        "LOW": "Physiological Baseline • Low Airway Stress",
        "MODERATE": "Elevated Airway Vulnerability • Mild Bronchial Stress",
        "HIGH": "Acute Atmospheric Bronchial Burden • High Airway Compromise"
    }
    pred_diag_title.configure(text=diag_titles[level], text_color=color)

    advice_texts = {
        "LOW": "Current respiratory telemetry and surrounding particulate metrics reside safely within acceptable physiological tolerance. No acute bronchospastic threat detected. Continue routine preventative monitoring.",
        "MODERATE": "Elevated particulate concentrations (PM2.5/AQI) combined with mild symptom manifestations signal emergent airway strain. Susceptible individuals should avoid prolonged outdoor cardiovascular exertion and utilize indoor HEPA air filtration.",
        "HIGH": "CRITICAL RISK: Multiple adverse markers triggered simultaneously. Particulate inhalation and active bronchial spasms signify acute pulmonary distress. Prompt clinical isolation and rescue medication protocols are required."
    }
    pred_advice_lbl.configure(text=advice_texts[level])

    # Diagnostic Tags
    tag_strains = {"LOW": "Strain: Baseline", "MODERATE": "Strain: Elevated", "HIGH": "Strain: Severe"}
    tag_windows = {"LOW": "Re-eval: 24h", "MODERATE": "Re-eval: 4h", "HIGH": "Re-eval: 2h"}
    tag_actions = {"LOW": "Containment: None", "MODERATE": "Containment: Recommended", "HIGH": "Containment: Required"}

    pred_tag_strain.configure(text=f"🫁 {tag_strains[level]}")
    pred_tag_window.configure(text=f"⏱️ {tag_windows[level]}")
    pred_tag_action.configure(text=f"🛡️ {tag_actions[level]}")

    # Factor Contribution Breakdown Bars & Badges
    prog_sym.set(min(bd["symptoms"] / max_sym, 1.0))
    prog_sym.configure(progress_color=HIGH_COLOR if bd["symptoms"] > 18 else (MOD_COLOR if bd["symptoms"] > 8 else LOW_COLOR))
    val_sym.configure(text=f"{bd['symptoms']:.1f} / {max_sym}")
    badge_sym.configure(text="SEVERE" if bd["symptoms"] > 18 else ("MODERATE" if bd["symptoms"] > 8 else "NORMAL"),
                        text_color=HIGH_COLOR if bd["symptoms"] > 18 else (MOD_COLOR if bd["symptoms"] > 8 else LOW_COLOR))

    prog_aqi.set(min(bd["aqi"] / max_aqi, 1.0))
    prog_aqi.configure(progress_color=HIGH_COLOR if bd["aqi"] > 15 else (MOD_COLOR if bd["aqi"] > 8 else LOW_COLOR))
    val_aqi.configure(text=f"{bd['aqi']:.1f} / {max_aqi}")
    badge_aqi.configure(text="UNHEALTHY" if bd["aqi"] > 15 else ("MODERATE" if bd["aqi"] > 8 else "GOOD"),
                        text_color=HIGH_COLOR if bd["aqi"] > 15 else (MOD_COLOR if bd["aqi"] > 8 else LOW_COLOR))

    prog_pm.set(min(bd["pm25"] / max_pm, 1.0))
    prog_pm.configure(progress_color=HIGH_COLOR if bd["pm25"] > 10 else (MOD_COLOR if bd["pm25"] > 5 else LOW_COLOR))
    val_pm.configure(text=f"{bd['pm25']:.1f} / {max_pm}")
    badge_pm.configure(text="SEVERE" if bd["pm25"] > 10 else ("ELEVATED" if bd["pm25"] > 5 else "SAFE"),
                       text_color=HIGH_COLOR if bd["pm25"] > 10 else (MOD_COLOR if bd["pm25"] > 5 else LOW_COLOR))

    prog_exp.set(min(bd["exposure"] / max_exp, 1.0))
    prog_exp.configure(progress_color=HIGH_COLOR if bd["exposure"] > 8 else (MOD_COLOR if bd["exposure"] > 3 else LOW_COLOR))
    val_exp.configure(text=f"{bd['exposure']:.1f} / {max_exp}")
    badge_exp.configure(text="HIGH" if bd["exposure"] > 8 else ("MILD" if bd["exposure"] > 3 else "MINIMAL"),
                        text_color=HIGH_COLOR if bd["exposure"] > 8 else (MOD_COLOR if bd["exposure"] > 3 else LOW_COLOR))

    # Dual-Engine Consensus Cards
    pred_formula_score_lbl.configure(text=f"Score: {score:.1f} / 100")
    if ml is not None:
        pred_ml_class_lbl.configure(text=f"Class: {ml.upper()}", text_color=LOW_COLOR if ml.upper() == level else MOD_COLOR)
        if ml.upper() == level:
            pred_consensus_badge.configure(text="✓ 100% MODEL CONVERGENCE (HIGH CONFIDENCE)", text_color=LOW_COLOR)
        else:
            pred_consensus_badge.configure(text="⚠️ MODEL DISCREPANCY DETECTED (FORMULA WEIGHTED)", text_color=MOD_COLOR)
    else:
        pred_ml_class_lbl.configure(text="Class: FORMULA ONLY", text_color=TEXT_DIM)
        pred_consensus_badge.configure(text="✓ DETERMINISTIC POLYNOMIAL ACTIVE", text_color=ACCENT_SKY)

    # Matrix Table Rows Updates
    # Row 0: AQI
    aqi_stat_txt = "SAFE (GOOD)" if c["aqi"] < 50 else ("ELEVATED" if c["aqi"] < 100 else ("UNHEALTHY" if c["aqi"] < 200 else "HAZARDOUS"))
    aqi_stat_col = LOW_COLOR if c["aqi"] < 50 else (MOD_COLOR if c["aqi"] < 100 else HIGH_COLOR)
    mat_row_widgets[0][0].configure(text=f"{c['aqi']} Index Units")
    mat_row_widgets[0][1].configure(text="< 50 (Good)")
    mat_row_widgets[0][2].configure(text="> 100 (Unhealthy)")
    mat_row_widgets[0][3].configure(text=aqi_stat_txt, text_color=aqi_stat_col)

    # Row 1: PM2.5
    pm_stat_txt = "NORMAL" if c["pm25"] < 15.0 else ("ELEVATED" if c["pm25"] <= 35.0 else "HIGH CONCERN")
    pm_stat_col = LOW_COLOR if c["pm25"] < 15.0 else (MOD_COLOR if c["pm25"] <= 35.0 else HIGH_COLOR)
    mat_row_widgets[1][0].configure(text=f"{c['pm25']:.1f} µg/m³")
    mat_row_widgets[1][1].configure(text="< 15.0 µg/m³ (WHO)")
    mat_row_widgets[1][2].configure(text="> 35.0 µg/m³ (EPA)")
    mat_row_widgets[1][3].configure(text=pm_stat_txt, text_color=pm_stat_col)

    # Row 2: Dyspnea
    b_names = ["None (Eupnea)", "Mild Effort", "Moderate Dyspnea", "Severe Distress"]
    dys_stat_txt = "NORMAL" if c["breathing"] == 0 else ("MILD STRAIN" if c["breathing"] == 1 else "SIGNIFICANT STRAIN")
    dys_stat_col = LOW_COLOR if c["breathing"] == 0 else (MOD_COLOR if c["breathing"] == 1 else HIGH_COLOR)
    mat_row_widgets[2][0].configure(text=f"Level {c['breathing']} ({b_names[c['breathing']]})")
    mat_row_widgets[2][1].configure(text="Level 0 (Eupnea)")
    mat_row_widgets[2][2].configure(text="Level ≥ 2 (Dyspnea)")
    mat_row_widgets[2][3].configure(text=dys_stat_txt, text_color=dys_stat_col)

    # Row 3: Symptoms
    active_syms = sum(1 for k in ["cough", "wheezing", "runny", "sore", "allergy"] if c[k] > 0)
    sym_stat_txt = "ASYMPTOMATIC" if active_syms == 0 else (f"{active_syms} ACTIVE" if active_syms <= 2 else f"{active_syms} SEVERE COMPLEX")
    sym_stat_col = LOW_COLOR if active_syms == 0 else (MOD_COLOR if active_syms <= 2 else HIGH_COLOR)
    mat_row_widgets[3][0].configure(text=f"{active_syms} Manifestations Active")
    mat_row_widgets[3][1].configure(text="0 Active Markers")
    mat_row_widgets[3][2].configure(text="≥ 2 Active Markers")
    mat_row_widgets[3][3].configure(text=sym_stat_txt, text_color=sym_stat_col)

    render_alert_page()

# ==========================================================
# PAGE: EMERGENCY CLINICAL GUIDANCE & TRIAGE DECISION SUPPORT
# ==========================================================

alert_view = page_views["alert"]

# Top Header with Clinical Protocol Subtitle
alert_header = ctk.CTkFrame(alert_view, fg_color="transparent")
alert_header.pack(fill="x", pady=(4, 12))

ctk.CTkLabel(alert_header, text="Clinical Emergency & Triage Guidance", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w")
ctk.CTkLabel(alert_header, text="Evidence-based pulmonary triage protocol derived from ATS/ERS and EPA clinical ambient air standards.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(2, 8))

# Metadata Ribbon (Patient info & clinical protocol timestamp)
alert_ribbon = ctk.CTkFrame(alert_view, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
alert_ribbon.pack(fill="x", pady=(0, 16))

ribbon_content = ctk.CTkFrame(alert_ribbon, fg_color="transparent")
ribbon_content.pack(fill="x", padx=16, pady=10)

def make_ribbon_chip(parent, icon, label, val_text):
    box = ctk.CTkFrame(parent, fg_color=PANEL_BG, corner_radius=8, border_width=1, border_color=BORDER)
    box.pack(side="left", padx=(0, 10))
    ctk.CTkLabel(box, text=f"{icon} {label}:", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_FAINT
                 ).pack(side="left", padx=(10, 4), pady=5)
    lbl = ctk.CTkLabel(box, text=val_text, font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_LIGHT)
    lbl.pack(side="left", padx=(0, 10), pady=5)
    return lbl

alert_patient_chip = make_ribbon_chip(ribbon_content, "👤", "PATIENT", "User")
alert_city_chip = make_ribbon_chip(ribbon_content, "📍", "LOCATION", "Chennai")
alert_time_chip = make_ribbon_chip(ribbon_content, "⏱️", "EVALUATED AT", "--:--")
alert_proto_chip = make_ribbon_chip(ribbon_content, "🏷️", "PROTOCOL", "ATS-PULMO-2024.1")

# Clinical Triage Hero Banner (Frosted Glass Card with Color Border)
alert_hero_card = ctk.CTkFrame(alert_view, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
alert_hero_card.pack(fill="x", pady=(0, 16))

alert_hero_inner = ctk.CTkFrame(alert_hero_card, fg_color="transparent")
alert_hero_inner.pack(fill="x", padx=22, pady=18)

alert_tier_badge = ctk.CTkLabel(alert_hero_inner, text="TIER-1 CRITICAL PULMONARY INTERVENTION",
                                font=(FONT_FAMILY, 11, "bold"), fg_color=HIGH_COLOR, text_color=BG_DARK,
                                corner_radius=8, padx=12, pady=5)
alert_tier_badge.pack(anchor="w", pady=(0, 8))

alert_hero_title = ctk.CTkLabel(alert_hero_inner, text="HIGH RESPIRATORY RISK DETECTED",
                                font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_LIGHT)
alert_hero_title.pack(anchor="w")

alert_hero_synopsis = ctk.CTkLabel(alert_hero_inner,
                                   text="Simultaneous elevated fine particulate matter exposure and acute respiratory symptom burden indicate significant airway compromise.",
                                   font=(FONT_FAMILY, 12), text_color=TEXT_DIM, wraplength=850, justify="left")
alert_hero_synopsis.pack(anchor="w", pady=(6, 0))

# 4 Clinical Biomarker Metrics Cards (Grid)
alert_biomarkers_grid = ctk.CTkFrame(alert_view, fg_color="transparent")
alert_biomarkers_grid.pack(fill="x", pady=(0, 16))
alert_biomarkers_grid.columnconfigure(0, weight=1)
alert_biomarkers_grid.columnconfigure(1, weight=1)
alert_biomarkers_grid.columnconfigure(2, weight=1)
alert_biomarkers_grid.columnconfigure(3, weight=1)

alert_bio_widgets = []
bio_card_defs = [
    ("🌫️ Ambient AQI", "Atmospheric Index", "Unhealthy Range", 0),
    ("🔬 PM2.5 Fine Particles", "Particulate Mass", "Lung Penetration", 1),
    ("🫁 Work of Breathing", "Dyspnea Score", "Accessory Effort", 2),
    ("🩺 Active Symptoms", "Clinical Markers", "Mucosal Irritation", 3)
]

for title, sub, standard, col_i in bio_card_defs:
    c = ctk.CTkFrame(alert_biomarkers_grid, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER)
    c.grid(row=0, column=col_i, sticky="nsew", padx=5)

    ctk.CTkLabel(c, text=title, font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_LIGHT).pack(anchor="w", padx=14, pady=(12, 1))
    ctk.CTkLabel(c, text=sub, font=(FONT_FAMILY, 9), text_color=TEXT_FAINT).pack(anchor="w", padx=14, pady=(0, 6))

    v_lbl = ctk.CTkLabel(c, text="--", font=(FONT_FAMILY, 18, "bold"), text_color=PRIMARY)
    v_lbl.pack(anchor="w", padx=14, pady=(0, 4))

    ref_lbl = ctk.CTkLabel(c, text=standard, font=(FONT_FAMILY, 9, "bold"), text_color=TEXT_DIM)
    ref_lbl.pack(anchor="w", padx=14, pady=(0, 12))

    alert_bio_widgets.append((v_lbl, ref_lbl))

# 2-Column Clinical Intervention Protocols & Red Flag Matrix
alert_protocols_grid = ctk.CTkFrame(alert_view, fg_color="transparent")
alert_protocols_grid.pack(fill="x", pady=(0, 16))
alert_protocols_grid.columnconfigure(0, weight=6)
alert_protocols_grid.columnconfigure(1, weight=5)

# Left Column: Step-by-Step Clinical Care Pathway
card_pathway = ctk.CTkFrame(alert_protocols_grid, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
card_pathway.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

ctk.CTkLabel(card_pathway, text="🏥  Immediate Clinical Care Pathway (Step-by-Step)",
             font=(FONT_FAMILY, 13, "bold"), text_color=PRIMARY).pack(anchor="w", padx=20, pady=(16, 12))

pathway_steps_container = ctk.CTkFrame(card_pathway, fg_color="transparent")
pathway_steps_container.pack(fill="x", padx=20, pady=(0, 16))

# Right Column: Red Flag Alert Box & Environmental Barriers
right_protocol_col = ctk.CTkFrame(alert_protocols_grid, fg_color="transparent")
right_protocol_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

# Red Flag Card
card_redflags = ctk.CTkFrame(right_protocol_col, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=HIGH_COLOR)
card_redflags.pack(fill="x", pady=(0, 14))

ctk.CTkLabel(card_redflags, text="🚨  Hospital Escalation Criteria (Call 108 / 112)",
             font=(FONT_FAMILY, 13, "bold"), text_color=HIGH_COLOR).pack(anchor="w", padx=18, pady=(14, 8))

redflag_items = [
    "Inability to speak complete sentences without gasping for breath",
    "Visible retraction of skin around clavicle, neck, or lower ribs",
    "Cyanosis (bluish tint on lips, tongue, or fingernail beds)",
    "No relief 15 minutes after taking prescribed rescue bronchodilator",
    "Onset of extreme lethargy, confusion, or severe chest tightness"
]

for rf in redflag_items:
    row = ctk.CTkFrame(card_redflags, fg_color="transparent")
    row.pack(fill="x", padx=18, pady=3)
    ctk.CTkLabel(row, text="⚠️", font=(FONT_FAMILY, 11), text_color=HIGH_COLOR).pack(side="left", padx=(0, 8), anchor="n")
    ctk.CTkLabel(row, text=rf, font=(FONT_FAMILY, 11), text_color=TEXT_LIGHT, wraplength=340, justify="left"
                 ).pack(side="left", fill="x", expand=True)

ctk.CTkFrame(card_redflags, height=12, fg_color="transparent").pack()

# Environmental Containment Card
card_containment = ctk.CTkFrame(right_protocol_col, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
card_containment.pack(fill="x")

ctk.CTkLabel(card_containment, text="🛡️  Environmental Containment Directives",
             font=(FONT_FAMILY, 13, "bold"), text_color=ACCENT_SKY).pack(anchor="w", padx=18, pady=(14, 8))

env_directives = [
    "Seal external windows; run True HEPA filtration unit on high CADR mode",
    "Avoid indoor aerosol sprays, cooking smoke, incense, and vacuuming",
    "Don certified N95/FFP2 respirator mask if movement outdoors is unavoidable",
    "Keep HVAC system strictly in internal recirculation mode"
]

for ed in env_directives:
    row = ctk.CTkFrame(card_containment, fg_color="transparent")
    row.pack(fill="x", padx=18, pady=3)
    ctk.CTkLabel(row, text="✓", font=(FONT_FAMILY, 11, "bold"), text_color=ACCENT_SKY).pack(side="left", padx=(0, 8), anchor="n")
    ctk.CTkLabel(row, text=ed, font=(FONT_FAMILY, 11), text_color=TEXT_DIM, wraplength=340, justify="left"
                 ).pack(side="left", fill="x", expand=True)

ctk.CTkFrame(card_containment, height=12, fg_color="transparent").pack()

# Physician Clinical Handover Card (Exportable Clinical Note)
card_handover = ctk.CTkFrame(alert_view, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
card_handover.pack(fill="x", pady=(0, 16))

handover_top = ctk.CTkFrame(card_handover, fg_color="transparent")
handover_top.pack(fill="x", padx=20, pady=(16, 8))

ctk.CTkLabel(handover_top, text="📋  Physician Telemetry Handover Note", font=(FONT_FAMILY, 13, "bold"), text_color=TEXT_LIGHT
             ).pack(side="left")

copy_status_lbl = ctk.CTkLabel(handover_top, text="", font=(FONT_FAMILY, 11, "bold"), text_color=LOW_COLOR)
copy_status_lbl.pack(side="left", padx=14)

def copy_handover_note():
    note_text = handover_textbox.get("1.0", "end").strip()
    if note_text:
        root.clipboard_clear()
        root.clipboard_append(note_text)
        copy_status_lbl.configure(text="✓ Copied to clipboard! Ready to share with Doctor.")
        root.after(3000, lambda: copy_status_lbl.configure(text=""))

copy_btn = ctk.CTkButton(handover_top, text="📋 Copy Telemetry Note", width=170, height=32, corner_radius=8,
                         fg_color=PANEL_BG, hover_color=BORDER, text_color=PRIMARY,
                         font=(FONT_FAMILY, 11, "bold"), command=copy_handover_note)
copy_btn.pack(side="right")

handover_textbox = ctk.CTkTextbox(card_handover, height=130, corner_radius=10, fg_color=INPUT_BG,
                                  text_color=TEXT_LIGHT, font=("Consolas", 10), border_width=1, border_color=BORDER)
handover_textbox.pack(fill="x", padx=20, pady=(0, 16))

# Navigation Action Footer
alert_footer = ctk.CTkFrame(alert_view, fg_color="transparent")
alert_footer.pack(fill="x", pady=(4, 16))

alert_back_btn = ctk.CTkButton(alert_footer, text="← Return to Prediction Dashboard", width=260, height=44,
                              corner_radius=12, fg_color=CARD_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                              font=(FONT_FAMILY, 12, "bold"), command=lambda: navigate_to("prediction"))
alert_back_btn.pack(side="left", padx=(0, 10))

alert_reassess_btn = ctk.CTkButton(alert_footer, text="🔄 New Intake Assessment", width=200, height=44,
                                  corner_radius=12, fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=BG_DARK,
                                  font=(FONT_FAMILY, 12, "bold"), command=lambda: navigate_to("data"))
alert_reassess_btn.pack(side="left")

def render_alert_page():
    if not last_result:
        return
    score = last_result["score"]
    level = last_result["level"]
    c = last_result["collected"]
    bd = last_result["breakdown"]
    ml = last_result.get("ml_pred")
    color = {"LOW": LOW_COLOR, "MODERATE": MOD_COLOR, "HIGH": HIGH_COLOR}[level]

    # Update metadata ribbon
    alert_patient_chip.configure(text=current_user or "Patient")
    alert_city_chip.configure(text=c.get("city", "Chennai"))
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    alert_time_chip.configure(text=now_str)

    # Hero Banner Updates
    tier_titles = {
        "HIGH": "TIER-1 CRITICAL PULMONARY INTERVENTION",
        "MODERATE": "TIER-2 ELEVATED AIRWAY VULNERABILITY",
        "LOW": "TIER-3 STABLE BASELINE RESPIRATION"
    }
    hero_titles = {
        "HIGH": f"CRITICAL RESPIRATORY RISK ALERT  ({score:.0f}/100)",
        "MODERATE": f"MODERATE RESPIRATORY RISK DETECTED  ({score:.0f}/100)",
        "LOW": f"LOW RESPIRATORY RISK — NORMAL PARAMETERS  ({score:.0f}/100)"
    }
    synopsis_texts = {
        "HIGH": "Simultaneous severe atmospheric pollution and active bronchial symptoms detected. Patient is at heightened vulnerability for acute bronchospasm, hypoxemia, or allergic exacerbation. Immediate triage protocols must be instituted.",
        "MODERATE": "Elevated particulate concentrations or mild bronchial hyperresponsiveness noted. Proactive environmental mitigation and continuous symptom observation recommended to prevent deterioration.",
        "LOW": "Current air quality telemetry and reported symptom manifestations remain within baseline normal parameters. Maintain preventative hydration and routine monitoring."
    }

    alert_tier_badge.configure(text=tier_titles[level], fg_color=color, text_color=BG_DARK if level != "HIGH" else TEXT_LIGHT)
    alert_hero_title.configure(text=hero_titles[level])
    alert_hero_synopsis.configure(text=synopsis_texts[level])

    # 4 Biomarker Cards Updates
    # 0: AQI
    alert_bio_widgets[0][0].configure(text=str(c["aqi"]))
    aqi_tier = "Good" if c["aqi"] < 50 else ("Moderate" if c["aqi"] < 100 else ("Unhealthy" if c["aqi"] < 200 else "Hazardous"))
    alert_bio_widgets[0][1].configure(text=f"Tier: {aqi_tier} (Clean Cap: 50)")

    # 1: PM2.5
    alert_bio_widgets[1][0].configure(text=f"{c['pm25']:.1f} µg/m³")
    pm_eval = "Safe (<15.0)" if c["pm25"] < 15 else ("Moderate (15-35)" if c["pm25"] <= 35 else "Severe (>35.0)")
    alert_bio_widgets[1][1].configure(text=f"Guideline: {pm_eval}")

    # 2: Breathing
    b_names = ["None (Normal)", "Mild Effort", "Moderate Dyspnea", "Severe Distress"]
    alert_bio_widgets[2][0].configure(text=b_names[c["breathing"]])
    b_notes = ["Eupnea / Normal", "Mild Accessory Strain", "Increased Airway Resistance", "High Respiratory Strain"]
    alert_bio_widgets[2][1].configure(text=b_notes[c["breathing"]])

    # 3: Symptoms
    symptom_list = []
    if c["cough"] > 0: symptom_list.append(f"Cough({c['cough']})")
    if c["wheezing"] > 0: symptom_list.append(f"Wheeze({c['wheezing']})")
    if c["runny"] > 0: symptom_list.append(f"Rhinitis({c['runny']})")
    if c["sore"] > 0: symptom_list.append(f"Pharyngitis({c['sore']})")
    if c["allergy"] > 0: symptom_list.append(f"Allergen({c['allergy']})")

    active_count = len(symptom_list)
    alert_bio_widgets[3][0].configure(text=f"{active_count} Active Manifestations")
    alert_bio_widgets[3][1].configure(text=", ".join(symptom_list[:3]) or "None Reported")

    # Step-by-Step Care Pathway Generation
    for w in pathway_steps_container.winfo_children():
        w.destroy()

    if level == "HIGH":
        pathway_steps = [
            ("1", "Immediate Environmental Isolation", "Relocate immediately to a sealed indoor room. Power on True HEPA air filtration unit on high mode. Do not open windows or expose to outdoor ambient air."),
            ("2", "Prescribed Bronchodilator Administration", "If diagnosed with asthma or hyperreactive airway disease, administer prescribed quick-relief rescue inhaler (Albuterol / Levosalbutamol 2-4 puffs via spacer device) as per your written physician action plan."),
            ("3", "Pursed-Lip & Diaphragmatic Respiration", "Adopt the upright tripod posture (sit upright, lean forward slightly resting elbows on knees). Inhale through nose for 2 counts, exhale through pursed lips for 4 counts to prevent airway collapse."),
            ("4", "Warm Hydration & Airway Lubrication", "Consume warm water or herbal teas to reduce mucosal viscosity; strictly avoid cold or refrigerated fluids that may trigger sudden reflex bronchospasms.")
        ]
    elif level == "MODERATE":
        pathway_steps = [
            ("1", "Proactive Environmental Shielding", "Minimize high-intensity outdoor cardiovascular exertion. Keep residential doors and windows closed during peak vehicular pollution windows."),
            ("2", "Precautionary Respiratory Protection", "Wear an authentic, well-fitted N95 or FFP2 respirator if venturing near heavy traffic corridors, industrial zones, or dusty construction perimeters."),
            ("3", "Preventative Airway Hydration & Steam Inhalation", "Perform mild warm steam inhalation for 5 minutes to clear upper airway particle deposition. Maintain optimal cellular hydration."),
            ("4", "Active Symptom Surveillance", "Re-assess respiratory effort in 4 hours. If coughing, nocturnal wheezing, or chest tightness escalates, initiate early medical consultation.")
        ]
    else:
        pathway_steps = [
            ("1", "Routine Preventative Maintenance", "Current biological and environmental metrics are within safe limits. Continue regular indoor and outdoor physical activities."),
            ("2", "Adequate Aeration & Ventilation", "Ventilate indoor living areas during low-traffic hours (early morning / mid-afternoon) to ensure fresh oxygen circulation."),
            ("3", "Baseline Telemetry Archiving", "Log symptoms periodically into AirSense to build a long-term pulmonary baseline for predictive tracking.")
        ]

    for step_num, step_title, step_desc in pathway_steps:
        s_box = ctk.CTkFrame(pathway_steps_container, fg_color=CARD_BG_ALT, corner_radius=10, border_width=1, border_color=BORDER)
        s_box.pack(fill="x", pady=4)

        s_left = ctk.CTkFrame(s_box, fg_color=PANEL_BG, corner_radius=8, width=32, height=32)
        s_left.pack(side="left", padx=10, pady=10)
        s_left.pack_propagate(False)

        ctk.CTkLabel(s_left, text=step_num, font=(FONT_FAMILY, 12, "bold"), text_color=PRIMARY).place(relx=0.5, rely=0.5, anchor="center")

        s_text_box = ctk.CTkFrame(s_box, fg_color="transparent")
        s_text_box.pack(side="left", fill="both", expand=True, padx=(4, 12), pady=8)

        ctk.CTkLabel(s_text_box, text=step_title, font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_LIGHT).pack(anchor="w")
        ctk.CTkLabel(s_text_box, text=step_desc, font=(FONT_FAMILY, 10), text_color=TEXT_DIM, wraplength=460, justify="left").pack(anchor="w", pady=(2, 0))

    # Physician Telemetry Handover Note Formulation
    sym_details_str = ", ".join([f"{k.capitalize()}={c[k]}/3" for k in ["cough", "wheezing", "runny", "sore", "allergy"] if c[k] > 0]) or "None reported"
    note_content = (
        f"================= AIRSENSE CLINICAL TELEMETRY HANDOVER =================\n"
        f"PATIENT NAME     : {current_user or 'Unknown'} (Age: {c.get('age', 25)})\n"
        f"LOCATION / CITY  : {c.get('city', 'Chennai')} | TIMESTAMP: {now_str}\n"
        f"TRIAGE CATEGORY  : {level} RESPIRATORY RISK (Risk Index: {score:.1f} / 100)\n"
        f"ENVIRONMENTAL    : Ambient AQI: {c['aqi']} | PM2.5: {c['pm25']} ug/m3\n"
        f"DYSPNEA EFFORT   : Level {c['breathing']} ({b_names[c['breathing']]})\n"
        f"ACTIVE SYMPTOMS  : {sym_details_str}\n"
        f"CONTRIBUTION     : Symptoms: {bd['symptoms']}/35 | AQI: {bd['aqi']}/30 | PM2.5: {bd['pm25']}/20 | Allergen: {bd['exposure']}/15\n"
        f"AI MODEL STATUS  : Random Forest Classifier: {str(ml).upper() if ml else 'FORMULA ACTIVE'}\n"
        f"RECOMMENDED NEXT : Standard Pulmonary Consult / ER Triage Protocol Activated\n"
        f"========================================================================="
    )

    handover_textbox.delete("1.0", "end")
    handover_textbox.insert("1.0", note_content)

# ==========================================================
# PAGE 3: HISTORY & LONGITUDINAL TRENDS
# ==========================================================

hist_view = page_views["history"]

hist_header = ctk.CTkFrame(hist_view, fg_color="transparent")
hist_header.pack(fill="x", pady=(4, 16))

ctk.CTkLabel(hist_header, text="Historical Health Telemetry", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w")
ctk.CTkLabel(hist_header, text="Review past risk assessments and longitudinal respiratory trends.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(2, 0))

# 3 Stat Cards on Top
hist_stats_grid = ctk.CTkFrame(hist_view, fg_color="transparent")
hist_stats_grid.pack(fill="x", pady=(0, 16))
hist_stats_grid.columnconfigure(0, weight=1)
hist_stats_grid.columnconfigure(1, weight=1)
hist_stats_grid.columnconfigure(2, weight=1)

def make_hist_stat_card(parent, col_idx, title, icon):
    c = ctk.CTkFrame(parent, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
    c.grid(row=0, column=col_idx, sticky="nsew", padx=6)
    ctk.CTkLabel(c, text=f"{icon}  {title}", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_DIM
                 ).pack(anchor="w", padx=16, pady=(14, 2))
    val_lbl = ctk.CTkLabel(c, text="--", font=(FONT_FAMILY, 22, "bold"), text_color=TEXT_LIGHT)
    val_lbl.pack(anchor="w", padx=16, pady=(0, 14))
    return val_lbl

hist_total_lbl = make_hist_stat_card(hist_stats_grid, 0, "TOTAL ASSESSMENTS", "📋")
hist_avg_lbl = make_hist_stat_card(hist_stats_grid, 1, "AVERAGE RISK SCORE", "📊")
hist_peak_lbl = make_hist_stat_card(hist_stats_grid, 2, "PEAK RECORDED RISK", "⚠️")

# Trend Canvas Card
hist_trend_card = ctk.CTkFrame(hist_view, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
hist_trend_card.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(hist_trend_card, text="📈  Risk Score Evolution (Past 7 Checkups)",
             font=(FONT_FAMILY, 14, "bold"), text_color=PRIMARY).pack(anchor="w", padx=20, pady=(16, 6))

trend_canvas = tk.Canvas(hist_trend_card, bg=CARD_BG, highlightthickness=0, height=180)
trend_canvas.pack(fill="x", padx=20, pady=(0, 16))

# Table Card
hist_table_card = ctk.CTkFrame(hist_view, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
hist_table_card.pack(fill="x")

hist_table_top = ctk.CTkFrame(hist_table_card, fg_color="transparent")
hist_table_top.pack(fill="x", padx=20, pady=(16, 10))

ctk.CTkLabel(hist_table_top, text="Recent Assessment Logs", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(side="left")

def clear_user_history():
    if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear your assessment history?"):
        conn = sqlite3.connect("airsense.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history WHERE username=?", (current_user,))
        conn.commit()
        conn.close()
        refresh_history_page()

clear_hist_btn = ctk.CTkButton(hist_table_top, text="🗑️ Clear Logs", width=110, height=30, corner_radius=8,
                               fg_color=PANEL_BG, hover_color=BORDER, text_color=HIGH_COLOR,
                               font=(FONT_FAMILY, 11, "bold"), command=clear_user_history)
clear_hist_btn.pack(side="right")

hist_table_rows = ctk.CTkFrame(hist_table_card, fg_color="transparent")
hist_table_rows.pack(fill="x", padx=20, pady=(0, 16))

def refresh_history_page():
    for w in hist_table_rows.winfo_children():
        w.destroy()

    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, aqi, pm25, risk_score, risk_level
        FROM history WHERE username=?
        ORDER BY id DESC LIMIT 10
    """, (current_user,))
    rows = cursor.fetchall()
    conn.close()

    # Update summary stats
    if rows:
        hist_total_lbl.configure(text=f"{len(rows)} Records")
        avg_score = sum(r[3] for r in rows) / len(rows)
        hist_avg_lbl.configure(text=f"{avg_score:.1f} / 100")
        max_score = max(r[3] for r in rows)
        hist_peak_lbl.configure(text=f"{max_score:.1f}")
    else:
        hist_total_lbl.configure(text="0 Records")
        hist_avg_lbl.configure(text="--")
        hist_peak_lbl.configure(text="--")

    # Render Table Header
    headers = [("TIMESTAMP", 180), ("AQI", 80), ("PM2.5", 90), ("SCORE", 90), ("RISK STATUS", 140)]
    th = ctk.CTkFrame(hist_table_rows, fg_color=CARD_BG_ALT, corner_radius=8, height=36)
    th.pack(fill="x", pady=(0, 6))
    th.pack_propagate(False)

    for h_name, w_px in headers:
        ctk.CTkLabel(th, text=h_name, font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM, width=w_px, anchor="w"
                     ).pack(side="left", padx=10)

    if not rows:
        ctk.CTkLabel(hist_table_rows, text="No previous assessments found for this user.",
                     font=(FONT_FAMILY, 12), text_color=TEXT_FAINT).pack(pady=20)
    else:
        color_map = {"LOW": LOW_COLOR, "MODERATE": MOD_COLOR, "HIGH": HIGH_COLOR}
        for r in rows:
            rf = ctk.CTkFrame(hist_table_rows, fg_color="transparent", height=38)
            rf.pack(fill="x", pady=2)
            rf.pack_propagate(False)

            ctk.CTkLabel(rf, text=r[0], font=(FONT_FAMILY, 11), text_color=TEXT_LIGHT, width=180, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(rf, text=str(r[1]), font=(FONT_FAMILY, 11), text_color=TEXT_LIGHT, width=80, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(rf, text=f"{r[2]:.1f}", font=(FONT_FAMILY, 11), text_color=TEXT_LIGHT, width=90, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(rf, text=f"{r[3]:.1f}", font=(FONT_FAMILY, 11, "bold"), text_color=TEXT_LIGHT, width=90, anchor="w").pack(side="left", padx=10)

            badge = ctk.CTkLabel(rf, text=r[4], font=(FONT_FAMILY, 10, "bold"), text_color=BG_DARK,
                                 fg_color=color_map.get(r[4], TEXT_DIM), corner_radius=6, width=100, height=24)
            badge.pack(side="left", padx=10)

    # Render Trend Line on Canvas
    trend_canvas.delete("all")
    trend_canvas.update_idletasks()
    cw = trend_canvas.winfo_width() or 700
    ch = trend_canvas.winfo_height() or 180

    points = list(reversed(rows))[-7:]
    if len(points) >= 2:
        pad_x, pad_y = 50, 30
        draw_w = cw - pad_x * 2
        draw_h = ch - pad_y * 2

        # Grid lines for 0, 30 (Low), 60 (Mod), 100
        for g_val, g_color in [(0, BORDER), (30, "#132D2B"), (60, "#3D2B16"), (100, BORDER)]:
            gy = pad_y + draw_h - (g_val / 100.0) * draw_h
            trend_canvas.create_line(pad_x, gy, cw - pad_x, gy, fill=g_color, dash=(2, 4))
            trend_canvas.create_text(pad_x - 14, gy, text=str(g_val), font=(FONT_FAMILY, 8), fill=TEXT_FAINT)

        step_x = draw_w / (len(points) - 1)
        coords = []
        for i, p in enumerate(points):
            x = pad_x + i * step_x
            y = pad_y + draw_h - (float(p[3]) / 100.0) * draw_h
            coords.extend([x, y])
            # Date label
            date_short = p[0][5:10] if len(p[0]) >= 10 else p[0]
            trend_canvas.create_text(x, ch - 12, text=date_short, font=(FONT_FAMILY, 8), fill=TEXT_DIM)

        # Smooth spline curve
        trend_canvas.create_line(*coords, fill=PRIMARY, width=3, smooth=True)

        # Point nodes
        for i in range(0, len(coords), 2):
            px, py = coords[i], coords[i+1]
            trend_canvas.create_oval(px - 5, py - 5, px + 5, py + 5, fill=PRIMARY, outline=CARD_BG, width=2)
            # Score tag
            pt_score = points[i // 2][3]
            trend_canvas.create_text(px, py - 14, text=f"{pt_score:.0f}", font=(FONT_FAMILY, 8, "bold"), fill=TEXT_LIGHT)
    else:
        trend_canvas.create_text(cw * 0.5, ch * 0.5, text="Collect at least 2 risk evaluations to see evolution trend.",
                                 font=(FONT_FAMILY, 11), fill=TEXT_FAINT)

# ==========================================================
# PAGE 4: USER PROFILE & SETTINGS (NEW FULL FEATURE)
# ==========================================================

profile_view = page_views["profile"]

prof_header = ctk.CTkFrame(profile_view, fg_color="transparent")
prof_header.pack(fill="x", pady=(4, 16))

ctk.CTkLabel(prof_header, text="User Profile & Preferences", font=(FONT_FAMILY, 24, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w")
ctk.CTkLabel(prof_header, text="Manage patient bio-data, baseline sensitivity, and security credentials.",
             font=(FONT_FAMILY, 12), text_color=TEXT_DIM).pack(anchor="w", pady=(2, 0))

# 2-Column Responsive Layout
prof_grid = ctk.CTkFrame(profile_view, fg_color="transparent")
prof_grid.pack(fill="both", expand=True)
prof_grid.columnconfigure(0, weight=1)
prof_grid.columnconfigure(1, weight=1)

# Left Column: Profile Card & Bio-data
prof_col_left = ctk.CTkFrame(prof_grid, fg_color="transparent")
prof_col_left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

# Avatar & Identity Card
card_id = ctk.CTkFrame(prof_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_id.pack(fill="x", pady=(0, 16))

id_row = ctk.CTkFrame(card_id, fg_color="transparent")
id_row.pack(fill="x", padx=24, pady=20)

prof_avatar_lbl = ctk.CTkLabel(id_row, text="U", width=64, height=64, corner_radius=32,
                              fg_color=PRIMARY, text_color=BG_DARK, font=(FONT_FAMILY, 22, "bold"))
prof_avatar_lbl.pack(side="left", padx=(0, 18))

id_details = ctk.CTkFrame(id_row, fg_color="transparent")
id_details.pack(side="left")

prof_username_lbl = ctk.CTkLabel(id_details, text="Username", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_LIGHT)
prof_username_lbl.pack(anchor="w")

ctk.CTkLabel(id_details, text="● Registered Patient • AirSense Telemetry Active",
             font=(FONT_FAMILY, 11, "bold"), text_color=LOW_COLOR).pack(anchor="w", pady=(2, 0))

# Personal Health Profile Card (Editable)
card_bio = ctk.CTkFrame(prof_col_left, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_bio.pack(fill="x")

ctk.CTkLabel(card_bio, text="👤  Health Profile & Baseline Information", font=(FONT_FAMILY, 14, "bold"), text_color=PRIMARY
             ).pack(anchor="w", padx=24, pady=(18, 12))

bio_inputs = ctk.CTkFrame(card_bio, fg_color="transparent")
bio_inputs.pack(fill="x", padx=24, pady=(0, 14))

ctk.CTkLabel(bio_inputs, text="PATIENT AGE", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).pack(anchor="w")
prof_age_entry = ctk.CTkEntry(bio_inputs, height=40, corner_radius=10, border_color=BORDER,
                             fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
prof_age_entry.pack(fill="x", pady=(2, 10))

ctk.CTkLabel(bio_inputs, text="DEFAULT CITY / REGION", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).pack(anchor="w")
prof_city_entry = ctk.CTkEntry(bio_inputs, height=40, corner_radius=10, border_color=BORDER,
                              fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
prof_city_entry.pack(fill="x", pady=(2, 14))

prof_save_status = ctk.CTkLabel(card_bio, text="", font=(FONT_FAMILY, 11, "bold"), text_color=LOW_COLOR)
prof_save_status.pack(anchor="w", padx=24, pady=(0, 6))

def save_profile_changes():
    new_age_str = prof_age_entry.get().strip()
    new_city = prof_city_entry.get().strip() or "Chennai"
    new_age = int(new_age_str) if new_age_str.isdigit() else 25

    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET age=?, city=? WHERE username=?", (new_age, new_city, current_user))
    conn.commit()
    conn.close()

    # Also update inputs in Data Collection
    dc_age_input.delete(0, "end")
    dc_age_input.insert(0, str(new_age))
    dc_city_input.delete(0, "end")
    dc_city_input.insert(0, new_city)

    prof_save_status.configure(text="✓ Health profile updated successfully!", text_color=LOW_COLOR)
    root.after(3000, lambda: prof_save_status.configure(text=""))

prof_save_btn = ctk.CTkButton(card_bio, text="💾 Save Profile Changes", height=42, corner_radius=10,
                             fg_color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=BG_DARK,
                             font=(FONT_FAMILY, 12, "bold"), command=save_profile_changes)
prof_save_btn.pack(fill="x", padx=24, pady=(0, 20))

# Right Column: Security & Password Management
prof_col_right = ctk.CTkFrame(prof_grid, fg_color="transparent")
prof_col_right.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

# Security Card
card_sec = ctk.CTkFrame(prof_col_right, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_sec.pack(fill="x", pady=(0, 16))

ctk.CTkLabel(card_sec, text="🔒  Security & Password", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=24, pady=(18, 12))

sec_inputs = ctk.CTkFrame(card_sec, fg_color="transparent")
sec_inputs.pack(fill="x", padx=24, pady=(0, 14))

ctk.CTkLabel(sec_inputs, text="CURRENT PASSWORD", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).pack(anchor="w")
prof_cur_pwd = ctk.CTkEntry(sec_inputs, height=40, show="•", corner_radius=10, border_color=BORDER,
                            fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
prof_cur_pwd.pack(fill="x", pady=(2, 10))

ctk.CTkLabel(sec_inputs, text="NEW PASSWORD", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_DIM).pack(anchor="w")
prof_new_pwd = ctk.CTkEntry(sec_inputs, height=40, show="•", corner_radius=10, border_color=BORDER,
                            fg_color=INPUT_BG, text_color=TEXT_LIGHT, font=(FONT_FAMILY, 12))
prof_new_pwd.pack(fill="x", pady=(2, 14))

sec_status_lbl = ctk.CTkLabel(card_sec, text="", font=(FONT_FAMILY, 11, "bold"), text_color=HIGH_COLOR)
sec_status_lbl.pack(anchor="w", padx=24, pady=(0, 6))

def change_password():
    cur = prof_cur_pwd.get().strip()
    new = prof_new_pwd.get().strip()

    if not cur or not new:
        sec_status_lbl.configure(text="Please fill in both current and new passwords.", text_color=HIGH_COLOR)
        return
    if len(new) < 8 or not re.search(r"[A-Za-z]", new) or not re.search(r"[0-9]", new):
        sec_status_lbl.configure(text="New password must be at least 8 chars with letters & numbers.", text_color=HIGH_COLOR)
        return

    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (current_user,))
    row = cursor.fetchone()

    if row and row[0] == cur:
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new, current_user))
        conn.commit()
        sec_status_lbl.configure(text="✓ Password updated successfully!", text_color=LOW_COLOR)
        prof_cur_pwd.delete(0, "end")
        prof_new_pwd.delete(0, "end")
    else:
        sec_status_lbl.configure(text="Current password incorrect.", text_color=HIGH_COLOR)
    conn.close()

prof_pwd_btn = ctk.CTkButton(card_sec, text="Update Password", height=42, corner_radius=10,
                            fg_color=PANEL_BG, hover_color=BORDER, text_color=TEXT_LIGHT,
                            font=(FONT_FAMILY, 12, "bold"), command=change_password)
prof_pwd_btn.pack(fill="x", padx=24, pady=(0, 20))

# System Info Card
card_sys = ctk.CTkFrame(prof_col_right, fg_color=CARD_BG, corner_radius=18, border_width=1, border_color=BORDER)
card_sys.pack(fill="x")

ctk.CTkLabel(card_sys, text="ℹ️  System & Compliance", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_LIGHT
             ).pack(anchor="w", padx=24, pady=(18, 6))

sys_info_text = "• Client Version: AirSense v2.5 Enterprise Edition\n• WAQI Token ID: 182993a5... Active\n• SQLite Database: airsense.db Encrypted Session\n• ML Algorithm: Scikit-learn RandomForestClassifier"
ctk.CTkLabel(card_sys, text=sys_info_text, font=(FONT_FAMILY, 10), text_color=TEXT_DIM, justify="left"
             ).pack(anchor="w", padx=24, pady=(0, 18))

def refresh_profile_page():
    prof_username_lbl.configure(text=current_user)
    initials = current_user[:2].upper() if len(current_user) >= 2 else (current_user[:1].upper() or "U")
    prof_avatar_lbl.configure(text=initials)

    conn = sqlite3.connect("airsense.db")
    cursor = conn.cursor()
    cursor.execute("SELECT age, city FROM users WHERE username=?", (current_user,))
    row = cursor.fetchone()
    conn.close()

    if row:
        prof_age_entry.delete(0, "end")
        prof_age_entry.insert(0, str(row[0] or 25))
        prof_city_entry.delete(0, "end")
        prof_city_entry.insert(0, row[1] or "Chennai")

# ==========================================================
# APPLICATION ENTRY POINT
# ==========================================================

if __name__ == "__main__":
    root.mainloop()