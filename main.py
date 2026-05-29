import customtkinter as ctk
import tkinter as tk
import random, threading
from itertools import combinations
from collections import Counter

# configuration data constants
CARD_RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
CARD_SUITS = ['h','d','c','s']
RANK_VALUE_MAP = {rank: index for index, rank in enumerate(CARD_RANKS)}
SUIT_SYMBOLS = {'h':'♥','d':'♦','c':'♣','s':'♠'}
SUIT_COLORS = {'h':'#e05555','d':'#e05555','c':'#c8d6e5','s':'#c8d6e5'}
POKER_HAND_NAMES = ["High Card", "One Pair", "Two Pair", "Three of a Kind",
                    "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"]

# mathematical evaluation engine
def evaluate_five_card_hand(five_card_combination):
    card_ranks = sorted([RANK_VALUE_MAP[card[0]] for card in five_card_combination], reverse=True)
    card_suits = [card[1] for card in five_card_combination]
    rank_frequencies = sorted(Counter(card_ranks).values(), reverse=True)
    
    is_flush = len(set(card_suits)) == 1
    is_straight = len(set(card_ranks)) == 5 and card_ranks[0] - card_ranks[4] == 4
    
    if set(card_ranks) == {RANK_VALUE_MAP[rank] for rank in ['A','2','3','4','5']}: 
        is_straight = True
        
    if is_straight and is_flush:           hand_category = 8
    elif rank_frequencies[0] == 4:         hand_category = 7
    elif rank_frequencies == [3, 2]:       hand_category = 6
    elif is_flush:                         hand_category = 5
    elif is_straight:                      hand_category = 4
    elif rank_frequencies[0] == 3:         hand_category = 3
    elif rank_frequencies[:2] == [2, 2]:   hand_category = 2
    elif rank_frequencies[0] == 2:         hand_category = 1
    else:                                  hand_category = 0
        
    return (hand_category, card_ranks)

def find_best_five_card_hand(all_available_cards):
    if len(all_available_cards) < 5: return None
    return max(evaluate_five_card_hand(combination) for combination in combinations(all_available_cards, 5))

# simulation computation logic
def calculate_win_probability(my_hole_cards, current_community_cards, total_opponents, total_simulations=2500):
    fresh_deck = [(rank, suit) for rank in CARD_RANKS for suit in CARD_SUITS
                  if (rank, suit) not in set(my_hole_cards) | set(current_community_cards)]
    needed_community_cards = 5 - len(current_community_cards)
    win_count = tie_count = 0
    
    for _ in range(total_simulations):
        simulated_draw = random.sample(fresh_deck, max(0, needed_community_cards + 2 * total_opponents))
        simulated_board = current_community_cards + simulated_draw[:needed_community_cards]
        my_best_hand = find_best_five_card_hand(my_hole_cards + simulated_board)
        if not my_best_hand: continue
            
        opponents_best_hands = [
            find_best_five_card_hand([simulated_draw[needed_community_cards + opponent_index * 2], 
                                      simulated_draw[needed_community_cards + opponent_index * 2 + 1]] + simulated_board) 
            for opponent_index in range(total_opponents)
        ]
        opponents_best_hands = [hand for hand in opponents_best_hands if hand]
        
        if not opponents_best_hands:                  win_count += 1
        elif my_best_hand > max(opponents_best_hands):  win_count += 1
        elif my_best_hand == max(opponents_best_hands): tie_count += 1
            
    return 100 * win_count / total_simulations, 100 * tie_count / total_simulations

# game strategy optimization
def generate_strategy_advice(win_percentage, total_pot, cost_to_call):
    pot_odds_ratio = total_pot / (total_pot + cost_to_call) if cost_to_call > 0 else None
    if win_percentage >= 70: return "RAISE", "#4caf7d"
    if win_percentage >= 50:
        if pot_odds_ratio and (win_percentage / 100) > pot_odds_ratio: return "CALL", "#4caf7d"
        return "CALL / RAISE", "#4caf7d"
    if win_percentage >= 30:
        if pot_odds_ratio and (win_percentage / 100) > pot_odds_ratio: return "CALL", "#e0a84f"
        return "FOLD / BLUFF", "#e0a84f"
    return "FOLD", "#e05555"

# interface presentation styles
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COLOR_BACKGROUND = "#0d1117"
COLOR_PANEL      = "#161b22"
COLOR_BORDER     = "#30363d"
COLOR_FOREGROUND = "#e6edf3"
COLOR_FG_DIMMED  = "#8b949e"
COLOR_ACCENT     = "#58a6ff"
COLOR_GREEN      = "#4caf7d"
COLOR_AMBER      = "#e0a84f"
COLOR_RED        = "#e05555"

FONT_EXTRA_SMALL = ("SF Pro Display", 10)
FONT_SMALL       = ("SF Pro Display", 12)
FONT_MEDIUM      = ("SF Pro Display", 14)
FONT_LARGE       = ("SF Pro Display", 16, "bold")
FONT_EXTRA_LARGE = ("SF Pro Display", 26, "bold")
FONT_MASSIVE     = ("SF Pro Display", 42, "bold")

# application frame layout
root_window = ctk.CTk()
root_window.title("Automated Poker Bot Flow (25 Chips Max)")
root_window.geometry("1100x820")
root_window.resizable(True, True)
root_window.configure(fg_color=COLOR_BACKGROUND)

# execution state tracking
my_hole_cards = []
community_cards = []
current_street_index = 0
STREET_NAMES = ["Pre-Flop", "Flop", "Turn", "River"]
STREET_CARD_THRESHOLDS = [0, 3, 4, 5]
opponent_ui_rows = []
dead_pot = 0.0

# utility mathematical layout helpers
def get_all_used_cards():
    return set(my_hole_cards) | set(community_cards)

def lighten_color(hex_color, brightness_increase=20):
    red_channel, green_channel, blue_channel = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"#{min(255, red_channel + brightness_increase):02x}{min(255, green_channel + brightness_increase):02x}{min(255, blue_channel + brightness_increase):02x}"

def calculate_rounded_rectangle_points(x1, y1, x2, y2, radius):
    return [x1 + radius, y1, x2 - radius, y1, x2, y1 + radius, x2, y2 - radius,
            x2 - radius, y2, x1 + radius, y2, x1, y2 - radius, x1, y1 + radius]

def construct_stat_reporting_column(parent_container, column_index, column_header, default_text, standard_color):
    ctk.CTkLabel(parent_container, text=column_header, font=FONT_EXTRA_SMALL, text_color=COLOR_FG_DIMMED).grid(row=0, column=column_index, pady=(10, 2))
    reporting_label = ctk.CTkLabel(parent_container, text=default_text, font=FONT_LARGE, text_color=standard_color)
    reporting_label.grid(row=1, column=column_index, pady=(0, 10))
    return reporting_label

# vector graphics card rendering
def draw_card_tile(parent_widget, card_value=None, dimensions=(58, 80)):
    width_size, height_size = dimensions
    try:
        background_color = parent_widget.cget("fg_color")
        if isinstance(background_color, (list, tuple)): background_color = background_color[1]
    except Exception:
        background_color = COLOR_BACKGROUND
        
    card_canvas = tk.Canvas(parent_widget, width=width_size, height=height_size, bg=background_color, highlightthickness=0)
    
    if card_value:
        rank, suit = card_value
        suit_color = SUIT_COLORS[suit]
        suit_symbol = SUIT_SYMBOLS[suit]
        card_canvas.create_polygon(calculate_rounded_rectangle_points(1, 1, width_size - 1, height_size - 1, 6), fill=COLOR_PANEL, outline=suit_color, smooth=True)
        card_canvas.create_text(5, 4, text=rank, anchor="nw", font=("SF Pro Display", 9, "bold"), fill=suit_color)
        card_canvas.create_text(width_size // 2, height_size // 2 + 4, text=suit_symbol, font=("SF Pro Display", 20), fill=suit_color, anchor="center")
    else:
        card_canvas.create_polygon(calculate_rounded_rectangle_points(1, 1, width_size - 1, height_size - 1, 6), fill=COLOR_BACKGROUND, outline=COLOR_BORDER, smooth=True)
        card_canvas.create_text(width_size // 2, height_size // 2, text="?", font=("SF Pro Display", 18), fill=COLOR_BORDER, anchor="center")
    return card_canvas

# interactive card window logic
def open_card_picker_window(window_title, currently_selected, save_callback, number_of_cards_to_select=1):
    picker_window = ctk.CTkToplevel(root_window)
    picker_window.title(window_title)
    picker_window.configure(fg_color=COLOR_BACKGROUND)
    picker_window.geometry("760x520")
    picker_window.resizable(False, False)

    picker_window.protocol("WM_DELETE_WINDOW", lambda: None)
    picker_window.transient(root_window)
    picker_window.grab_set()
    picker_window.lift()
    picker_window.focus_force()

    temporary_selection = list(currently_selected)
    already_used_cards = get_all_used_cards() - set(currently_selected)

    ctk.CTkLabel(picker_window, text=window_title, font=FONT_LARGE, text_color=COLOR_FOREGROUND).pack(pady=(18, 2))
    hint_label = ctk.CTkLabel(picker_window, text=f"Select {number_of_cards_to_select} card{'s' if number_of_cards_to_select > 1 else ''}", font=FONT_SMALL, text_color=COLOR_FG_DIMMED)
    hint_label.pack()

    preview_frame = ctk.CTkFrame(picker_window, fg_color=COLOR_BACKGROUND)
    preview_frame.pack(pady=10)

    def update_preview_display():
        for child_widget in preview_frame.winfo_children(): child_widget.destroy()
        for index in range(number_of_cards_to_select):
            card_value = temporary_selection[index] if index < len(temporary_selection) else None
            draw_card_tile(preview_frame, card_value, dimensions=(54, 74)).pack(side="left", padx=6)

    update_preview_display()

    outer_grid_frame = ctk.CTkFrame(picker_window, fg_color=COLOR_BACKGROUND)
    outer_grid_frame.pack(fill="both", expand=True, padx=20, pady=4)
    inner_grid_frame = tk.Frame(outer_grid_frame, bg=COLOR_BACKGROUND)
    inner_grid_frame.pack()

    def generate_card_grid():
        for child_widget in inner_grid_frame.winfo_children(): child_widget.destroy()
        for suit_index, suit_letter in enumerate(CARD_SUITS):
            for rank_index, rank_letter in enumerate(CARD_RANKS):
                card_tuple = (rank_letter, suit_letter)
                is_card_taken = card_tuple in already_used_cards
                is_card_selected = card_tuple in temporary_selection

                if is_card_taken:      background_color, text_color, outline_color = "#0a0d12", COLOR_BORDER, COLOR_BORDER
                elif is_card_selected: background_color, text_color, outline_color = "#1a3050", SUIT_COLORS[suit_letter], COLOR_ACCENT
                else:                  background_color, text_color, outline_color = "#1a1f2a", SUIT_COLORS[suit_letter], SUIT_COLORS[suit_letter]

                card_cell = tk.Canvas(inner_grid_frame, width=48, height=64, bg=COLOR_BACKGROUND, highlightthickness=0, cursor="" if is_card_taken else "hand2")
                card_cell.grid(row=suit_index, column=rank_index, padx=2, pady=2)
                card_cell.create_polygon(calculate_rounded_rectangle_points(1, 1, 47, 63, 5), fill=background_color, outline=outline_color, smooth=True)
                card_cell.create_text(4, 3, text=rank_letter, anchor="nw", font=("SF Pro Display", 8, "bold"), fill=text_color)
                card_cell.create_text(24, 38, text=SUIT_SYMBOLS[suit_letter], font=("SF Pro Display", 14), fill=text_color, anchor="center")

                if not is_card_taken:
                    def handle_card_click(clicked_card=card_tuple):
                        if clicked_card in temporary_selection: temporary_selection.remove(clicked_card)
                        elif len(temporary_selection) < number_of_cards_to_select: temporary_selection.append(clicked_card)
                        update_preview_display()
                        generate_card_grid()
                        if len(temporary_selection) == number_of_cards_to_select:
                            confirm_button.configure(fg_color=COLOR_ACCENT, hover_color=lighten_color(COLOR_ACCENT), state="normal")
                        else:
                            confirm_button.configure(fg_color=COLOR_BORDER, hover_color=COLOR_BORDER, state="disabled")
                    card_cell.bind("<Button-1>", lambda event, cb=handle_card_click: cb())

    generate_card_grid()

    def process_confirmation():
        if len(temporary_selection) == number_of_cards_to_select:
            save_callback(list(temporary_selection))
            picker_window.grab_release()
            picker_window.destroy()

    initial_window_state = "normal" if len(temporary_selection) == number_of_cards_to_select else "disabled"
    initial_window_color = COLOR_ACCENT if len(temporary_selection) == number_of_cards_to_select else COLOR_BORDER

    confirm_button = ctk.CTkButton(picker_window, text="Confirm  ✓", command=process_confirmation, font=FONT_MEDIUM, fg_color=initial_window_color, state=initial_window_state)
    confirm_button.pack(pady=(6, 16))
    picker_window.wait_window()

# user interface assembly
top_bar_frame = ctk.CTkFrame(root_window, fg_color=COLOR_BACKGROUND, height=64)
top_bar_frame.pack(fill="x", padx=30, pady=(20, 0))
top_bar_frame.pack_propagate(False)
ctk.CTkLabel(top_bar_frame, text="pokey wokey bot", font=FONT_EXTRA_LARGE, text_color=COLOR_FOREGROUND).pack(side="left", pady=10)
street_display_label = ctk.CTkLabel(top_bar_frame, text="PRE-FLOP", font=FONT_LARGE, text_color=COLOR_ACCENT)
street_display_label.pack(side="right", pady=10)

ctk.CTkFrame(root_window, height=1, fg_color=COLOR_BORDER).pack(fill="x")

body_wrapper_frame = ctk.CTkFrame(root_window, fg_color=COLOR_BACKGROUND)
body_wrapper_frame.pack(fill="both", expand=True, padx=30, pady=20)
body_wrapper_frame.columnconfigure(0, weight=1)
body_wrapper_frame.columnconfigure(1, weight=1)

left_column_frame = ctk.CTkFrame(body_wrapper_frame, fg_color=COLOR_BACKGROUND)
right_column_frame = ctk.CTkFrame(body_wrapper_frame, fg_color=COLOR_BACKGROUND)
left_column_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
right_column_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

def create_ui_section(parent_container, section_title):
    section_frame = ctk.CTkFrame(parent_container, fg_color=COLOR_PANEL, corner_radius=10)
    section_frame.pack(fill="x", pady=(0, 14))
    ctk.CTkLabel(section_frame, text=section_title, font=FONT_EXTRA_SMALL, text_color=COLOR_FG_DIMMED).pack(anchor="w", padx=16, pady=(12, 4))
    return section_frame

# player panel generation
hole_cards_section = create_ui_section(left_column_frame, "YOUR HAND")
hole_cards_display_row = ctk.CTkFrame(hole_cards_section, fg_color=COLOR_PANEL)
hole_cards_display_row.pack(padx=16, pady=(0, 4))

def refresh_hole_cards_display():
    for child_widget in hole_cards_display_row.winfo_children(): child_widget.destroy()
    visible_cards = my_hole_cards if my_hole_cards else [None, None]
    for card_data in visible_cards[:2]:
        draw_card_tile(hole_cards_display_row, card_data, dimensions=(64, 88)).pack(side="left", padx=5)

def save_and_analyze_hole_cards(selected_cards):
    global my_hole_cards
    my_hole_cards = selected_cards
    refresh_hole_cards_display()
    enforce_game_flow_rules()
    start_poker_analysis()

pick_hole_cards_button = ctk.CTkButton(
    hole_cards_section, text="Pick Cards",
    command=lambda: open_card_picker_window("Your Hole Cards", my_hole_cards, save_and_analyze_hole_cards, 2),
    font=FONT_SMALL, fg_color=COLOR_ACCENT, hover_color=lighten_color(COLOR_ACCENT), text_color="white", height=36, corner_radius=8
)
pick_hole_cards_button.pack(padx=16, pady=(4, 14))
refresh_hole_cards_display()

community_section = create_ui_section(left_column_frame, "COMMUNITY CARDS")
community_cards_display_row = ctk.CTkFrame(community_section, fg_color=COLOR_PANEL)
community_cards_display_row.pack(padx=16, pady=(0, 4))

def refresh_community_cards_display():
    for child_widget in community_cards_display_row.winfo_children(): child_widget.destroy()
    visible_table_cards = community_cards + [None] * (5 - len(community_cards))
    for card_data in visible_table_cards:
        draw_card_tile(community_cards_display_row, card_data, dimensions=(58, 80)).pack(side="left", padx=4)

def handle_deal_community_cards():
    target_total = STREET_CARD_THRESHOLDS[current_street_index]
    needed_to_deal = target_total - len(community_cards)
    if needed_to_deal <= 0: return

    def save_and_analyze_community_cards(newly_dealt_cards):
        global community_cards
        for single_card in newly_dealt_cards:
            if single_card not in community_cards:
                community_cards.append(single_card)
        refresh_community_cards_display()
        enforce_game_flow_rules()
        start_poker_analysis()

    open_card_picker_window(f"Deal — {STREET_NAMES[current_street_index]}", [], save_and_analyze_community_cards, needed_to_deal)

deal_community_button = ctk.CTkButton(
    community_section, text="Deal Community Cards",
    command=handle_deal_community_cards, font=FONT_SMALL, fg_color="#1f2d40",
    hover_color="#2a3d55", text_color=COLOR_ACCENT, height=36, corner_radius=8, border_width=1, border_color=COLOR_ACCENT
)
deal_community_button.pack(padx=16, pady=(4, 14))
refresh_community_cards_display()

bet_info_section = create_ui_section(left_column_frame, "BET INFO (AUTOMATED TRACKING)")

your_bet_variable = ctk.StringVar(value="0")
pot_size_display_var = ctk.StringVar(value="0")
amount_to_call_display_var = ctk.StringVar(value="0")

your_bet_row = ctk.CTkFrame(bet_info_section, fg_color=COLOR_PANEL)
your_bet_row.pack(fill="x", padx=16, pady=4)
ctk.CTkLabel(your_bet_row, text="Your Bet (This Street)", font=FONT_SMALL, text_color=COLOR_FOREGROUND, width=150, anchor="w").pack(side="left")
your_bet_entry = ctk.CTkEntry(your_bet_row, textvariable=your_bet_variable, width=110, font=FONT_MEDIUM, fg_color="#0d1117", border_color=COLOR_BORDER, text_color=COLOR_FOREGROUND, corner_radius=6)
your_bet_entry.pack(side="right", pady=6)
your_bet_variable.trace_add("write", lambda *args: start_poker_analysis())

for label_text, associated_var, text_color in [("Calculated Pot Size", pot_size_display_var, COLOR_FOREGROUND), ("Amount to Call", amount_to_call_display_var, COLOR_AMBER)]:
    data_display_row = ctk.CTkFrame(bet_info_section, fg_color=COLOR_PANEL)
    data_display_row.pack(fill="x", padx=16, pady=4)
    ctk.CTkLabel(data_display_row, text=label_text, font=FONT_SMALL, text_color=COLOR_FG_DIMMED, width=150, anchor="w").pack(side="left")
    ctk.CTkLabel(data_display_row, textvariable=associated_var, font=FONT_LARGE, text_color=text_color).pack(side="right", pady=6)

ctk.CTkFrame(bet_info_section, height=10, fg_color=COLOR_PANEL).pack()

navigation_button_frame = ctk.CTkFrame(left_column_frame, fg_color=COLOR_BACKGROUND)
navigation_button_frame.pack(fill="x", pady=(0, 8))

def step_to_next_street():
    global current_street_index, dead_pot
    try:    user_chips = float(your_bet_variable.get())
    except: user_chips = 0.0
        
    opponents_chips = 0.0
    for row_data in opponent_ui_rows:
        try:
            opponents_chips += float(row_data["bet_variable"].get())
            row_data["bet_variable"].set("0")
            if row_data["move_variable"].get() != "fold":
                row_data["move_variable"].set("?")
        except: pass
            
    dead_pot += (user_chips + opponents_chips)
    your_bet_variable.set("0")
    
    if current_street_index < 3:
        current_street_index += 1
        street_display_label.configure(text=STREET_NAMES[current_street_index].upper())
        enforce_game_flow_rules()
        start_poker_analysis()

def reset_entire_hand_state():
    global my_hole_cards, community_cards, current_street_index, dead_pot
    my_hole_cards = []
    community_cards = []
    current_street_index = 0
    dead_pot = 0.0
    
    refresh_hole_cards_display()
    refresh_community_cards_display()
    street_display_label.configure(text="PRE-FLOP")
    your_bet_variable.set("0")
    pot_size_display_var.set("0")
    amount_to_call_display_var.set("0")
    
    advice_result_label.configure(text="—", text_color=COLOR_FG_DIMMED)
    hand_name_label.configure(text="")
    win_percentage_label.configure(text="—%")
    tie_percentage_label.configure(text="—%")
    pot_odds_label.configure(text="—%")
    probability_bar_canvas.coords(win_bar_rectangle, 0, 0, 0, 22)
    probability_bar_canvas.coords(tie_bar_rectangle, 0, 0, 0, 22)
    
    for row_data in opponent_ui_rows:
        row_data["move_variable"].set("?")
        row_data["bet_variable"].set("0")
    enforce_game_flow_rules()

next_street_button = ctk.CTkButton(navigation_button_frame, text="Next Street ▶", command=step_to_next_street, font=FONT_SMALL, fg_color=COLOR_PANEL, hover_color=COLOR_BORDER, text_color=COLOR_FOREGROUND, height=36, corner_radius=8, width=120)
next_street_button.pack(side="left")
ctk.CTkButton(navigation_button_frame, text="Reset Hand", command=reset_entire_hand_state, font=FONT_SMALL, fg_color="#2d1a1a", hover_color="#3d2020", text_color=COLOR_RED, height=36, corner_radius=8, width=100).pack(side="right")

# data metrics visualization panels
analysis_section = create_ui_section(right_column_frame, "ANALYSIS")
advice_result_label = ctk.CTkLabel(analysis_section, text="—", font=FONT_MASSIVE, text_color=COLOR_FG_DIMMED)
advice_result_label.pack(pady=(8, 2))
hand_name_label = ctk.CTkLabel(analysis_section, text="", font=FONT_MEDIUM, text_color=COLOR_FG_DIMMED)
hand_name_label.pack(pady=(0, 10))

statistics_grid_row = ctk.CTkFrame(analysis_section, fg_color=COLOR_PANEL)
statistics_grid_row.pack(fill="x", padx=16, pady=(0, 8))
for col_idx in range(3): statistics_grid_row.columnconfigure(col_idx, weight=1)

win_percentage_label = construct_stat_reporting_column(statistics_grid_row, 0, "WIN", "—%", COLOR_GREEN)
tie_percentage_label = construct_stat_reporting_column(statistics_grid_row, 1, "TIE", "—%", COLOR_AMBER)
pot_odds_label       = construct_stat_reporting_column(statistics_grid_row, 2, "POT ODDS", "—%", COLOR_FG_DIMMED)

TOTAL_BAR_WIDTH = 360
probability_bar_canvas = tk.Canvas(analysis_section, width=TOTAL_BAR_WIDTH, height=22, bg=COLOR_PANEL, highlightthickness=0)
probability_bar_canvas.pack(padx=16, pady=(0, 4))
probability_bar_canvas.create_rectangle(0, 0, TOTAL_BAR_WIDTH, 22, fill="#0d1117", outline="")
win_bar_rectangle = probability_bar_canvas.create_rectangle(0, 0, 0, 22, fill=COLOR_GREEN, outline="")
tie_bar_rectangle = probability_bar_canvas.create_rectangle(0, 0, 0, 22, fill=COLOR_AMBER, outline="")
ctk.CTkLabel(analysis_section, text="█ win   █ tie", font=FONT_EXTRA_SMALL, text_color=COLOR_FG_DIMMED).pack(pady=(0, 14))

opponents_section = create_ui_section(right_column_frame, "OPPONENTS")
opponents_scrollable_frame = ctk.CTkScrollableFrame(opponents_section, fg_color=COLOR_PANEL, height=260)
opponents_scrollable_frame.pack(fill="x", padx=4, pady=(0, 4))

opponents_list_header = ctk.CTkFrame(opponents_scrollable_frame, fg_color=COLOR_PANEL)
opponents_list_header.pack(fill="x", padx=8, pady=(4, 2))
for title, w in [("Player", 90), ("Move", 120), ("Bet", 80)]:
    ctk.CTkLabel(opponents_list_header, text=title, font=FONT_EXTRA_SMALL, text_color=COLOR_FG_DIMMED, width=w, anchor="w").pack(side="left", padx=4)

AVAILABLE_MOVE_OPTIONS = ["?", "fold", "check", "call", "raise", "allin"]

def append_new_opponent_tracking_row(explicit_name=None):
    assigned_index = len(opponent_ui_rows) + 1
    player_display_name = explicit_name or f"Player {assigned_index}"
    move_variable = ctk.StringVar(value="?")
    bet_variable = ctk.StringVar(value="0")

    row_container_frame = ctk.CTkFrame(opponents_scrollable_frame, fg_color="#0f141c", corner_radius=6)
    row_container_frame.pack(fill="x", padx=8, pady=3)

    ctk.CTkLabel(row_container_frame, text=player_display_name, font=FONT_SMALL, text_color=COLOR_FOREGROUND, width=90, anchor="w").pack(side="left", padx=8, pady=8)

    ctk.CTkOptionMenu(
        row_container_frame, variable=move_variable, values=AVAILABLE_MOVE_OPTIONS,
        font=FONT_SMALL, fg_color="#161b22", button_color=COLOR_BORDER, width=110, command=lambda *args: start_poker_analysis()
    ).pack(side="left", padx=4)

    bet_entry = ctk.CTkEntry(row_container_frame, textvariable=bet_variable, width=80, font=FONT_SMALL, fg_color="#0d1117", border_color=COLOR_BORDER, text_color=COLOR_FOREGROUND, corner_radius=6)
    bet_entry.pack(side="left", padx=4)
    bet_variable.trace_add("write", lambda *args: start_poker_analysis())

    opponent_row_data_dictionary = {"frame": row_container_frame, "name": player_display_name, "move_variable": move_variable, "bet_variable": bet_variable}

    def remove_opponent_from_list():
        opponent_ui_rows.remove(opponent_row_data_dictionary)
        row_container_frame.destroy()
        start_poker_analysis()

    ctk.CTkButton(row_container_frame, text="✕", command=remove_opponent_from_list, width=28, height=28, fg_color="transparent", hover_color="#2d1a1a", text_color=COLOR_FG_DIMMED, font=FONT_SMALL).pack(side="right", padx=6)
    opponent_ui_rows.append(opponent_row_data_dictionary)
    return opponent_row_data_dictionary

opponents_action_row = ctk.CTkFrame(opponents_section, fg_color=COLOR_PANEL)
opponents_action_row.pack(fill="x", padx=8, pady=(0, 12))
ctk.CTkButton(opponents_action_row, text="+ Add Player", command=append_new_opponent_tracking_row, font=FONT_SMALL, fg_color="transparent", hover_color="#1a2535", text_color=COLOR_ACCENT, border_width=1, border_color=COLOR_ACCENT, height=34, corner_radius=8).pack(side="left", padx=8)

for structural_index in range(1, 3):
    append_new_opponent_tracking_row(f"Player {structural_index}")

# workflow control logic
def enforce_game_flow_rules():
    target_board_count = STREET_CARD_THRESHOLDS[current_street_index]
    
    if current_street_index == 0:
        pick_hole_cards_button.configure(state="normal", fg_color=COLOR_ACCENT)
        deal_community_button.configure(state="disabled", border_color=COLOR_BORDER, text_color=COLOR_FG_DIMMED)
        if len(my_hole_cards) == 2:
            next_street_button.configure(state="normal", fg_color=COLOR_PANEL)
        else:
            next_street_button.configure(state="disabled", fg_color="#11141a")
    else:
        pick_hole_cards_button.configure(state="disabled", fg_color=COLOR_BORDER)
        
        if len(community_cards) < target_board_count:
            deal_community_button.configure(state="normal", border_color=COLOR_ACCENT, text_color=COLOR_ACCENT)
            next_street_button.configure(state="disabled", fg_color="#11141a")
        else:
            deal_community_button.configure(state="disabled", border_color=COLOR_BORDER, text_color=COLOR_FG_DIMMED)
            if current_street_index < 3:
                next_street_button.configure(state="normal", fg_color=COLOR_PANEL)
            else:
                next_street_button.configure(state="disabled", fg_color="#11141a")

# math simulation worker threads
is_simulation_running = False

def start_poker_analysis(*_args):
    global is_simulation_running
    
    try:    user_current_bet = float(your_bet_variable.get())
    except: user_current_bet = 0.0

    opponent_bets_list = []
    for row_data in opponent_ui_rows:
        try:
            if row_data["move_variable"].get() != "fold":
                opponent_bets_list.append(float(row_data["bet_variable"].get()))
        except: pass

    if user_current_bet > 25.0: user_current_bet = 25.0; your_bet_variable.set("25")

    current_highest_table_bet = max([user_current_bet] + opponent_bets_list) if ([user_current_bet] + opponent_bets_list) else 0.0
    auto_calculated_amount_to_call = max(0.0, current_highest_table_bet - user_current_bet)
    
    current_street_pot_total = user_current_bet + sum(opponent_bets_list)
    auto_calculated_total_pot = dead_pot + current_street_pot_total

    pot_size_display_var.set(f"{auto_calculated_total_pot:.0f} chips")
    amount_to_call_display_var.set(f"{auto_calculated_amount_to_call:.0f} chips")

    if is_simulation_running or len(my_hole_cards) < 2: return
    is_simulation_running = True
    advice_result_label.configure(text="…", text_color=COLOR_FG_DIMMED)

    frozen_hole  = list(my_hole_cards)
    frozen_comm  = list(community_cards)
    opp_count    = max(1, len([r for r in opponent_ui_rows if r["move_variable"].get() != "fold"]))

    def background_simulation_worker():
        global is_simulation_running
        try:
            win_pct, tie_pct = calculate_win_probability(frozen_hole, frozen_comm, opp_count)
            advice_text, advice_color = generate_strategy_advice(win_pct, auto_calculated_total_pot, auto_calculated_amount_to_call)
            pot_odds_pct = (auto_calculated_total_pot / (auto_calculated_total_pot + auto_calculated_amount_to_call) * 100) if auto_calculated_amount_to_call > 0 else None
            
            best_attained_combination = find_best_five_card_hand(frozen_hole + frozen_comm)
            evaluated_hand_name = POKER_HAND_NAMES[best_attained_combination[0]] if best_attained_combination else ""
            
            root_window.after(0, lambda: update_ui_with_results(win_pct, tie_pct, pot_odds_pct, advice_text, advice_color, evaluated_hand_name))
        finally:
            is_simulation_running = False

    threading.Thread(target=background_simulation_worker, daemon=True).start()

def update_ui_with_results(win_percentage, tie_percentage, pot_odds, advice_text, advice_color, hand_name):
    win_percentage_label.configure(text=f"{win_percentage:.0f}%", text_color=COLOR_GREEN)
    tie_percentage_label.configure(text=f"{tie_percentage:.0f}%", text_color=COLOR_AMBER)
    pot_odds_label.configure(text=f"{pot_odds:.0f}%" if pot_odds else "—", text_color=COLOR_FG_DIMMED)
    advice_result_label.configure(text=advice_text, text_color=advice_color)
    hand_name_label.configure(text=hand_name)
    
    win_bar_width = int(TOTAL_BAR_WIDTH * win_percentage / 100)
    tie_bar_width = int(TOTAL_BAR_WIDTH * tie_percentage / 100)
    probability_bar_canvas.coords(win_bar_rectangle, 0, 0, win_bar_width, 22)
    probability_bar_canvas.coords(tie_bar_rectangle, win_bar_width, 0, win_bar_width + tie_bar_width, 22)

enforce_game_flow_rules()

# desktop execution entry point
ctk.CTkFrame(root_window, height=1, fg_color=COLOR_BORDER).pack(fill="x", side="bottom")
status_bar_frame = ctk.CTkFrame(root_window, fg_color="#0a0d13", height=32)
status_bar_frame.pack(fill="x", side="bottom")
ctk.CTkLabel(status_bar_frame, text="Automated Calculations Active  ·  Max Stack 25 Chips Per Player Rule Applied", font=FONT_EXTRA_SMALL, text_color=COLOR_FG_DIMMED).pack(pady=7)

root_window.mainloop()