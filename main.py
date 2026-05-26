#!/usr/bin/env python3
"""
Poker Bot — CustomTkinter UI
Minimal dark theme · Monte Carlo equity · live advice
"""

import customtkinter as ctk
import tkinter as tk
import random, threading
from itertools import combinations
from collections import Counter

# ─── poker engine ─────────────────────────────────────────────────────────────

RANKS      = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
SUITS      = ['h','d','c','s']
RANK_VAL   = {r: i for i, r in enumerate(RANKS)}
SUIT_SYM   = {'h':'♥','d':'♦','c':'♣','s':'♠'}
SUIT_COLOR = {'h':'#e05555','d':'#e05555','c':'#c8d6e5','s':'#c8d6e5'}
HAND_NAMES = ["High Card","One Pair","Two Pair","Three of a Kind",
              "Straight","Flush","Full House","Four of a Kind","Straight Flush"]

def hand_rank(five):
    ranks = sorted([RANK_VAL[c[0]] for c in five], reverse=True)
    suits = [c[1] for c in five]
    cnt   = sorted(Counter(ranks).values(), reverse=True)
    flush = len(set(suits)) == 1
    st    = len(set(ranks)) == 5 and ranks[0] - ranks[4] == 4
    if set(ranks) == {RANK_VAL[r] for r in ['A','2','3','4','5']}: st = True
    if st and flush:     cat = 8
    elif cnt[0] == 4:    cat = 7
    elif cnt == [3,2]:   cat = 6
    elif flush:          cat = 5
    elif st:             cat = 4
    elif cnt[0] == 3:    cat = 3
    elif cnt[:2]==[2,2]: cat = 2
    elif cnt[0] == 2:    cat = 1
    else:                cat = 0
    return (cat, ranks)

def best_hand(cards):
    if len(cards) < 5: return None
    return max(hand_rank(c) for c in combinations(cards, 5))

def equity(hole, comm, n_opp, sims=2500):
    deck = [(r,s) for r in RANKS for s in SUITS
            if (r,s) not in set(hole)|set(comm)]
    need = 5 - len(comm)
    wins = ties = 0
    for _ in range(sims):
        draw  = random.sample(deck, need + 2*n_opp)
        board = comm + draw[:need]
        mine  = best_hand(hole + board)
        if not mine: continue
        opps  = [best_hand([draw[need+i*2], draw[need+i*2+1]] + board) for i in range(n_opp)]
        opps  = [o for o in opps if o]
        if   not opps:          wins += 1
        elif mine > max(opps):  wins += 1
        elif mine == max(opps): ties += 1
    return 100*wins/sims, 100*ties/sims

def make_advice(win, pot, call):
    po = pot/(pot+call) if call > 0 else None
    if win >= 70:                          return "RAISE",       "#4caf7d"
    if win >= 50:
        if po and win/100 > po:            return "CALL",        "#4caf7d"
        return                                    "CALL / RAISE", "#4caf7d"
    if win >= 30:
        if po and win/100 > po:            return "CALL",        "#e0a84f"
        return                                    "FOLD / BLUFF", "#e0a84f"
    return                                        "FOLD",         "#e05555"

# ─── theme ────────────────────────────────────────────────────────────────────

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG      = "#0d1117"
PANEL   = "#161b22"
BORDER  = "#30363d"
FG      = "#e6edf3"
FG_DIM  = "#8b949e"
ACCENT  = "#58a6ff"
GREEN   = "#4caf7d"
AMBER   = "#e0a84f"
RED     = "#e05555"

FONT_XS  = ("SF Pro Display", 10)
FONT_SM  = ("SF Pro Display", 12)
FONT_MD  = ("SF Pro Display", 14)
FONT_LG  = ("SF Pro Display", 16, "bold")
FONT_XL  = ("SF Pro Display", 26, "bold")
FONT_XXL = ("SF Pro Display", 42, "bold")

# ─── root ─────────────────────────────────────────────────────────────────────

root = ctk.CTk()
root.title("Poker Bot")
root.geometry("1100x820")
root.resizable(True, True)
root.configure(fg_color=BG)

# ─── state ────────────────────────────────────────────────────────────────────

hole       = []
community  = []
street_idx = 0
STREETS      = ["Pre-Flop", "Flop", "Turn", "River"]
STREET_CARDS = [0, 3, 1, 1]
opp_rows   = []

# ─── helpers ──────────────────────────────────────────────────────────────────

def used_cards():
    return set(hole) | set(community)

def _lighten(col, delta=20):
    r,g,b = int(col[1:3],16), int(col[3:5],16), int(col[5:7],16)
    return f"#{min(255,r+delta):02x}{min(255,g+delta):02x}{min(255,b+delta):02x}"

def _round_rect_pts(x1, y1, x2, y2, r):
    return [x1+r,y1, x2-r,y1, x2,y1+r, x2,y2-r,
            x2-r,y2, x1+r,y2, x1,y2-r, x1,y1+r]

# ─── card tile ────────────────────────────────────────────────────────────────

def draw_card_tile(parent, value=None, size=(58, 80)):
    W, H = size
    try:
        bg = parent.cget("fg_color")
        if isinstance(bg, (list, tuple)): bg = bg[1]
    except Exception:
        bg = BG
    cv = tk.Canvas(parent, width=W, height=H, bg=bg, highlightthickness=0)
    if value:
        rank, suit = value
        fc  = SUIT_COLOR[suit]
        sym = SUIT_SYM[suit]
        cv.create_polygon(_round_rect_pts(1,1,W-1,H-1,6), fill=PANEL, outline=fc, smooth=True)
        cv.create_text(5, 4, text=rank, anchor="nw", font=("SF Pro Display",9,"bold"), fill=fc)
        cv.create_text(W//2, H//2+4, text=sym, font=("SF Pro Display",20), fill=fc, anchor="center")
    else:
        cv.create_polygon(_round_rect_pts(1,1,W-1,H-1,6), fill=BG, outline=BORDER, smooth=True)
        cv.create_text(W//2, H//2, text="?", font=("SF Pro Display",18), fill=BORDER, anchor="center")
    return cv

# ─── card picker ──────────────────────────────────────────────────────────────

def open_picker(title, current, callback, n=1):
    """
    Modal card picker. Blocks until the user clicks Confirm.
    The OS close button is disabled — only Confirm saves the selection.
    """
    win = ctk.CTkToplevel(root)
    win.title(title)
    win.configure(fg_color=BG)
    win.geometry("760x520")
    win.resizable(False, False)

    # ── Block OS close button — user MUST click Confirm to save ──────────────
    # Intercept the close event and do nothing, so state is never half-saved.
    win.protocol("WM_DELETE_WINDOW", lambda: None)

    # Bring to front and keep on top of root
    win.transient(root)
    win.grab_set()
    win.lift()
    win.focus_force()

    # local mutable selection list
    selected = list(current)
    taken    = used_cards() - set(current)   # cards already on the board/hand

    # ── header ────────────────────────────────────────────────────────────────
    ctk.CTkLabel(win, text=title,
                 font=FONT_LG, text_color=FG).pack(pady=(18,2))
    hint_lbl = ctk.CTkLabel(win,
                 text=f"Select {n} card{'s' if n>1 else ''}  ·  click a card to toggle",
                 font=FONT_SM, text_color=FG_DIM)
    hint_lbl.pack()

    # ── preview strip ─────────────────────────────────────────────────────────
    prev_frame = ctk.CTkFrame(win, fg_color=BG)
    prev_frame.pack(pady=10)

    def refresh_preview():
        for w in prev_frame.winfo_children():
            w.destroy()
        for i in range(n):
            v = selected[i] if i < len(selected) else None
            draw_card_tile(prev_frame, v, size=(54,74)).pack(side="left", padx=6)

    refresh_preview()

    grid_outer = ctk.CTkFrame(win, fg_color=BG)
    grid_outer.pack(fill="both", expand=True, padx=20, pady=4)

    grid_frame = tk.Frame(grid_outer, bg=BG)
    grid_frame.pack()

    # Build / rebuild the entire grid (called after every toggle)
    def build_grid():
        for w in grid_frame.winfo_children():
            w.destroy()

        for ci, suit in enumerate(SUITS):
            for ri, rank in enumerate(RANKS):
                card    = (rank, suit)
                is_taken   = card in taken
                is_selected = card in selected

                if is_taken:
                    bg_c, fc, ol = "#0a0d12", BORDER, BORDER
                elif is_selected:
                    bg_c, fc, ol = "#1a3050", SUIT_COLOR[suit], ACCENT
                else:
                    bg_c, fc, ol = "#1a1f2a", SUIT_COLOR[suit], SUIT_COLOR[suit]

                cell = tk.Canvas(grid_frame, width=48, height=64,
                                 bg=BG, highlightthickness=0,
                                 cursor="" if is_taken else "hand2")
                cell.grid(row=ci, column=ri, padx=2, pady=2)
                cell.create_polygon(_round_rect_pts(1,1,47,63,5),
                                    fill=bg_c, outline=ol, smooth=True)
                cell.create_text(4, 3, text=rank, anchor="nw",
                                 font=("SF Pro Display",8,"bold"), fill=fc)
                cell.create_text(24, 38, text=SUIT_SYM[suit],
                                 font=("SF Pro Display",14), fill=fc, anchor="center")

                if not is_taken:
                    def on_click(c=card):
                        if c in selected:
                            selected.remove(c)
                        elif len(selected) < n:
                            selected.append(c)
                        refresh_preview()
                        build_grid()
                        # update confirm button state
                        if len(selected) == n:
                            confirm_btn.configure(fg_color=ACCENT,
                                                  hover_color=_lighten(ACCENT),
                                                  state="normal")
                        else:
                            confirm_btn.configure(fg_color=BORDER,
                                                  hover_color=BORDER,
                                                  state="disabled")

                    cell.bind("<Button-1>", lambda e, f=on_click: f())

    build_grid()

    # ── confirm button ────────────────────────────────────────────────────────
    def confirm():
        if len(selected) == n:
            callback(list(selected))   # pass a copy so local list can't mutate
            win.grab_release()
            win.destroy()

    # Start disabled if nothing pre-selected
    initial_state  = "normal"  if len(selected) == n else "disabled"
    initial_color  = ACCENT    if len(selected) == n else BORDER

    confirm_btn = ctk.CTkButton(
        win, text=f"Confirm  ✓", command=confirm,
        font=FONT_MD, fg_color=initial_color,
        hover_color=_lighten(initial_color),
        text_color="white", height=44, corner_radius=8,
        state=initial_state)
    confirm_btn.pack(pady=(6, 16))

    # Also add an explicit Cancel that doesn't save anything
    ctk.CTkButton(
        win, text="Cancel", command=lambda: [win.grab_release(), win.destroy()],
        font=FONT_SM, fg_color="transparent", hover_color="#2d1a1a",
        text_color=FG_DIM, height=28, corner_radius=8).pack(pady=(0, 10))

    win.wait_window()   # block until destroyed

# ─── main layout ──────────────────────────────────────────────────────────────

# top bar
topbar = ctk.CTkFrame(root, fg_color=BG, height=64)
topbar.pack(fill="x", padx=30, pady=(20,0))
topbar.pack_propagate(False)
ctk.CTkLabel(topbar, text="♠  POKER BOT", font=FONT_XL, text_color=FG).pack(side="left", pady=10)
street_lbl = ctk.CTkLabel(topbar, text="PRE-FLOP", font=FONT_LG, text_color=ACCENT)
street_lbl.pack(side="right", pady=10)

ctk.CTkFrame(root, height=1, fg_color=BORDER).pack(fill="x")

body = ctk.CTkFrame(root, fg_color=BG)
body.pack(fill="both", expand=True, padx=30, pady=20)
body.columnconfigure(0, weight=1)
body.columnconfigure(1, weight=1)
body.rowconfigure(0, weight=1)

left  = ctk.CTkFrame(body, fg_color=BG)
right = ctk.CTkFrame(body, fg_color=BG)
left.grid(row=0, column=0, sticky="nsew", padx=(0,12))
right.grid(row=0, column=1, sticky="nsew", padx=(12,0))

# ─── section helper ────────────────────────────────────────────────────────────

def section(parent, title):
    f = ctk.CTkFrame(parent, fg_color=PANEL, corner_radius=10)
    f.pack(fill="x", pady=(0,14))
    ctk.CTkLabel(f, text=title, font=FONT_XS, text_color=FG_DIM).pack(anchor="w", padx=16, pady=(12,4))
    return f

# ─── LEFT ─────────────────────────────────────────────────────────────────────

# hole cards
hole_sec = section(left, "YOUR HAND")
hole_row = ctk.CTkFrame(hole_sec, fg_color=PANEL)
hole_row.pack(padx=16, pady=(0,4))

def refresh_hole():
    for w in hole_row.winfo_children(): w.destroy()
    shown = hole if hole else [None, None]
    for c in shown[:2]:
        draw_card_tile(hole_row, c, size=(64, 88)).pack(side="left", padx=5)

refresh_hole()

def set_hole(cards):
    global hole
    hole = cards
    refresh_hole()
    run_analysis()

ctk.CTkButton(hole_sec, text="Pick Cards",
    command=lambda: open_picker("Your Hole Cards", hole, set_hole, 2),
    font=FONT_SM, fg_color=ACCENT, hover_color=_lighten(ACCENT),
    text_color="white", height=36, corner_radius=8).pack(padx=16, pady=(4,14))

# community cards
comm_sec = section(left, "COMMUNITY CARDS")
comm_row = ctk.CTkFrame(comm_sec, fg_color=PANEL)
comm_row.pack(padx=16, pady=(0,4))

def refresh_comm():
    for w in comm_row.winfo_children(): w.destroy()
    shown = community + [None] * (5 - len(community))
    for c in shown:
        draw_card_tile(comm_row, c, size=(58, 80)).pack(side="left", padx=4)

refresh_comm()

def pick_comm():
    n = STREET_CARDS[street_idx]
    if n == 0: return

    def cb(cards):
        global community
        if street_idx == 1:
            community = cards          # flop: set all 3
        else:
            for c in cards:            # turn/river: append
                if c not in community:
                    community.append(c)
        refresh_comm()
        run_analysis()

    open_picker(f"Deal — {STREETS[street_idx]}", [], cb, n)

ctk.CTkButton(comm_sec, text="Deal Community Cards",
    command=pick_comm, font=FONT_SM, fg_color="#1f2d40",
    hover_color="#2a3d55", text_color=ACCENT, height=36, corner_radius=8,
    border_width=1, border_color=ACCENT).pack(padx=16, pady=(4,14))

# bet info
pot_sec  = section(left, "BET INFO")
pot_var  = ctk.StringVar(value="0")
call_var = ctk.StringVar(value="0")
for lbl_txt, var in [("Pot Size", pot_var), ("Amount to Call", call_var)]:
    row = ctk.CTkFrame(pot_sec, fg_color=PANEL)
    row.pack(fill="x", padx=16, pady=4)
    ctk.CTkLabel(row, text=lbl_txt, font=FONT_SM, text_color=FG_DIM,
                 width=130, anchor="w").pack(side="left")
    ctk.CTkEntry(row, textvariable=var, width=110, font=FONT_MD,
                 fg_color="#0d1117", border_color=BORDER, text_color=FG,
                 corner_radius=6).pack(side="right", pady=6)
    var.trace_add("write", lambda *a: run_analysis())
ctk.CTkFrame(pot_sec, height=10, fg_color=PANEL).pack()

# street nav
nav = ctk.CTkFrame(left, fg_color=BG)
nav.pack(fill="x", pady=(0,8))

def prev_street():
    global street_idx
    if street_idx > 0:
        street_idx -= 1
        street_lbl.configure(text=STREETS[street_idx].upper())
        run_analysis()

def next_street():
    global street_idx
    if street_idx < 3:
        street_idx += 1
        street_lbl.configure(text=STREETS[street_idx].upper())

def new_hand():
    global hole, community, street_idx
    hole = []; community = []; street_idx = 0
    refresh_hole(); refresh_comm()
    street_lbl.configure(text="PRE-FLOP")
    pot_var.set("0"); call_var.set("0")
    result_lbl.configure(text="—", text_color=FG_DIM)
    hand_lbl.configure(text="")
    win_lbl.configure(text="—%")
    tie_lbl.configure(text="—%")
    po_lbl.configure(text="—%")
    bar_canvas.coords(bar_win,  0, 0, 0, 22)
    bar_canvas.coords(bar_tie, 0, 0, 0, 22)
    for od in opp_rows:
        od["move_var"].set("?")
        od["bet_var"].set("0")

ctk.CTkButton(nav, text="◀ Prev", command=prev_street,
    font=FONT_SM, fg_color=PANEL, hover_color=BORDER,
    text_color=FG_DIM, height=36, corner_radius=8, width=90).pack(side="left")
ctk.CTkButton(nav, text="Next ▶", command=next_street,
    font=FONT_SM, fg_color=PANEL, hover_color=BORDER,
    text_color=FG_DIM, height=36, corner_radius=8, width=90).pack(side="left", padx=8)
ctk.CTkButton(nav, text="New Hand", command=new_hand,
    font=FONT_SM, fg_color="#2d1a1a", hover_color="#3d2020",
    text_color=RED, height=36, corner_radius=8, width=100).pack(side="right")

# ─── RIGHT ────────────────────────────────────────────────────────────────────

# analysis
an_sec = section(right, "ANALYSIS")
result_lbl = ctk.CTkLabel(an_sec, text="—", font=FONT_XXL, text_color=FG_DIM)
result_lbl.pack(pady=(8,2))
hand_lbl = ctk.CTkLabel(an_sec, text="", font=FONT_MD, text_color=FG_DIM)
hand_lbl.pack(pady=(0,10))

stats_row = ctk.CTkFrame(an_sec, fg_color=PANEL)
stats_row.pack(fill="x", padx=16, pady=(0,8))
for i in range(3): stats_row.columnconfigure(i, weight=1)

def stat_col(parent, col, header, val_txt, val_color):
    ctk.CTkLabel(parent, text=header, font=FONT_XS, text_color=FG_DIM).grid(row=0, column=col, pady=(10,2))
    lbl = ctk.CTkLabel(parent, text=val_txt, font=FONT_LG, text_color=val_color)
    lbl.grid(row=1, column=col, pady=(0,10))
    return lbl

win_lbl = stat_col(stats_row, 0, "WIN",      "—%", GREEN)
tie_lbl = stat_col(stats_row, 1, "TIE",      "—%", AMBER)
po_lbl  = stat_col(stats_row, 2, "POT ODDS", "—%", FG_DIM)

BAR_W = 360
bar_canvas = tk.Canvas(an_sec, width=BAR_W, height=22,
                        bg=PANEL, highlightthickness=0)
bar_canvas.pack(padx=16, pady=(0,4))
bar_canvas.create_rectangle(0, 0, BAR_W, 22, fill="#0d1117", outline="")
bar_win = bar_canvas.create_rectangle(0, 0, 0, 22, fill=GREEN, outline="")
bar_tie = bar_canvas.create_rectangle(0, 0, 0, 22, fill=AMBER, outline="")
ctk.CTkLabel(an_sec, text="█ win   █ tie",
             font=FONT_XS, text_color=FG_DIM).pack(pady=(0,14))

# opponents
opp_sec    = section(right, "OPPONENTS")
opp_scroll = ctk.CTkScrollableFrame(opp_sec, fg_color=PANEL, height=260)
opp_scroll.pack(fill="x", padx=4, pady=(0,4))

hdr = ctk.CTkFrame(opp_scroll, fg_color=PANEL)
hdr.pack(fill="x", padx=8, pady=(4,2))
for txt, w in [("Player",90), ("Move",120), ("Bet",80)]:
    ctk.CTkLabel(hdr, text=txt, font=FONT_XS, text_color=FG_DIM,
                 width=w, anchor="w").pack(side="left", padx=4)

MOVES = ["?","fold","check","call","raise","allin"]

def add_opponent(name=None):
    idx   = len(opp_rows) + 1
    pname = name or f"Player {idx}"
    mv    = ctk.StringVar(value="?")
    bv    = ctk.StringVar(value="0")

    row = ctk.CTkFrame(opp_scroll, fg_color="#0f141c", corner_radius=6)
    row.pack(fill="x", padx=8, pady=3)

    ctk.CTkLabel(row, text=pname, font=FONT_SM, text_color=FG,
                 width=90, anchor="w").pack(side="left", padx=8, pady=8)

    ctk.CTkOptionMenu(row, variable=mv, values=MOVES,
        font=FONT_SM, fg_color="#161b22", button_color=BORDER,
        button_hover_color=ACCENT, text_color=FG, dropdown_fg_color="#161b22",
        dropdown_text_color=FG, dropdown_hover_color=BORDER,
        width=110, command=lambda *a: run_analysis()).pack(side="left", padx=4)

    ctk.CTkEntry(row, textvariable=bv, width=80, font=FONT_SM,
                 fg_color="#0d1117", border_color=BORDER,
                 text_color=FG, corner_radius=6).pack(side="left", padx=4)
    bv.trace_add("write", lambda *a: run_analysis())

    entry_data = {"frame": row, "name": pname, "move_var": mv, "bet_var": bv}

    def remove():
        opp_rows.remove(entry_data)
        row.destroy()
        run_analysis()

    ctk.CTkButton(row, text="✕", command=remove, width=28, height=28,
                  fg_color="transparent", hover_color="#2d1a1a",
                  text_color=FG_DIM, font=FONT_SM).pack(side="right", padx=6)

    opp_rows.append(entry_data)
    return entry_data

btn_row = ctk.CTkFrame(opp_sec, fg_color=PANEL)
btn_row.pack(fill="x", padx=8, pady=(0,12))
ctk.CTkButton(btn_row, text="+ Add Player", command=add_opponent,
    font=FONT_SM, fg_color="transparent", hover_color="#1a2535",
    text_color=ACCENT, border_width=1, border_color=ACCENT,
    height=34, corner_radius=8).pack(side="left", padx=8)

for i in range(1, 3):
    add_opponent(f"Player {i}")



_busy = False

def run_analysis(*_):
    global _busy
    if _busy or len(hole) < 2: return
    _busy = True
    result_lbl.configure(text="…", text_color=FG_DIM)

    _hole  = list(hole)
    _comm  = list(community)
    _n     = max(1, len(opp_rows))
    try:    _pot  = float(pot_var.get())
    except: _pot  = 0
    try:    _call = float(call_var.get())
    except: _call = 0

    def worker():
        global _busy
        try:
            w, t     = equity(_hole, _comm, _n)
            rec, col = make_advice(w, _pot, _call)
            po       = (_pot/(_pot+_call)*100) if _call > 0 else None
            bh       = best_hand(_hole + _comm)
            hn       = HAND_NAMES[bh[0]] if bh else ""
            root.after(0, lambda: _update(w, t, po, rec, col, hn))
        finally:
            _busy = False

    threading.Thread(target=worker, daemon=True).start()

def _update(w, t, po, rec, col, hn):
    win_lbl.configure(text=f"{w:.0f}%", text_color=GREEN)
    tie_lbl.configure(text=f"{t:.0f}%", text_color=AMBER)
    po_lbl.configure(text=f"{po:.0f}%" if po else "—", text_color=FG_DIM)
    result_lbl.configure(text=rec, text_color=col)
    hand_lbl.configure(text=hn)
    wx = int(BAR_W * w / 100)
    tx = int(BAR_W * t / 100)
    bar_canvas.coords(bar_win,  0, 0, wx,    22)
    bar_canvas.coords(bar_tie, wx, 0, wx+tx, 22)


ctk.CTkFrame(root, height=1, fg_color=BORDER).pack(fill="x", side="bottom")
sbar = ctk.CTkFrame(root, fg_color="#0a0d13", height=32)
sbar.pack(fill="x", side="bottom")
ctk.CTkLabel(sbar,
    text="Cards: rank+suit  ·  e.g.  Ah  Kd  10s  Qc  ·  Suits: h=♥  d=♦  c=♣  s=♠",
    font=FONT_XS, text_color=FG_DIM).pack(pady=7)

root.mainloop()