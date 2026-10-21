
import importlib
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from config.database import get_connection
from permissions import can_access_module


# --------------------------------------------------
# APPEARANCE
# --------------------------------------------------

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

BG = ("#F4F6FA", "#15171C")
CARD = ("#FFFFFF", "#20232A")
TEXT = ("#202637", "#F4F5F7")
MUTED = ("#70798B", "#A6ADBB")
BORDER = ("#E3E7EF", "#343944")

RED = "#B91C1C"
RED_HOVER = "#991B1B"


# --------------------------------------------------
# MODULES
# --------------------------------------------------

MODULES = [
    ("Donor Management", "donor_ui"),
    ("Donation Management", "donation_ui"),
    ("Blood Stock", "stock_ui"),
    ("Hospital Management", "hospital_ui"),
    ("Blood Requests", "blood_request_ui"),
    ("Blood Issues", "blood_issue_ui"),
    ("Reports & Analytics", "reports_ui"),
]


# --------------------------------------------------
# COMPATIBILITY FRAME FOR EXISTING MODULES
# --------------------------------------------------

class EmbeddedModuleFrame(tk.Frame):
    """
    Allows existing modules to run inside the dashboard.

    Older modules call root.title() and root.geometry()
    because they were originally designed for separate
    windows. These methods become harmless no-ops here.
    """

    def title(self, *_args, **_kwargs):
        pass

    def geometry(self, *_args, **_kwargs):
        pass


# --------------------------------------------------
# MAIN DASHBOARD
# --------------------------------------------------

class BloodBankDashboard:

    def __init__(self, root):
        self.root = root

        self.staff_id = None
        self.staff_name = "Staff"
        self.staff_role = "STAFF"

        self.active_module = None
        self.active_module_frame = None

        self.root.title("LIFEPOINT | Blood Bank Management")
        self.root.geometry("1440x900")
        self.root.minsize(1050, 680)

        self.metric_labels = {}

        self.build_ui()
        self.refresh_dashboard()

    # --------------------------------------------------
    # USER SESSION
    # --------------------------------------------------

    def set_user(self, staff_id, staff_name, staff_role):
        self.staff_id = staff_id
        self.staff_name = staff_name
        self.staff_role = (staff_role or "STAFF").upper()

        self.user_label.configure(
            text=f"{self.staff_name}  |  {self.staff_role}"
        )

        self.update_menu_permissions()

    # --------------------------------------------------
    # BUILD MAIN WINDOW
    # --------------------------------------------------

    def build_ui(self):

        self.main = ctk.CTkFrame(
            self.root,
            fg_color=BG,
            corner_radius=0
        )
        self.main.pack(fill="both", expand=True)

        self.main.grid_columnconfigure(1, weight=1)
        self.main.grid_rowconfigure(0, weight=1)

        # ==============================================
        # SIDEBAR
        # ==============================================

        self.sidebar = ctk.CTkFrame(
            self.main,
            width=245,
            fg_color=CARD,
            corner_radius=0,
            border_width=1,
            border_color=BORDER
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(False)

        brand = ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        )
        brand.pack(
            fill="x",
            padx=20,
            pady=(25, 28)
        )

        ctk.CTkLabel(
            brand,
            text="✚",
            font=("Arial", 34, "bold"),
            text_color=RED
        ).pack(side="left", padx=(0, 10))

        brand_text = ctk.CTkFrame(
            brand,
            fg_color="transparent"
        )
        brand_text.pack(side="left")

        ctk.CTkLabel(
            brand_text,
            text="LIFEPOINT",
            font=("Arial", 19, "bold"),
            text_color=TEXT
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text="BLOOD BANK",
            font=("Arial", 10, "bold"),
            text_color=MUTED
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.sidebar,
            text="MAIN MENU",
            text_color=MUTED,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=23, pady=(0, 12))

        # Dashboard button
        self.dashboard_button = ctk.CTkButton(
            self.sidebar,
            text="▦    Dashboard",
            anchor="w",
            height=42,
            corner_radius=9,
            font=("Arial", 13),
            fg_color=RED,
            hover_color=RED_HOVER,
            text_color="#FFFFFF",
            command=self.show_dashboard
        )
        self.dashboard_button.pack(
            fill="x",
            padx=13,
            pady=3
        )

        # Module navigation buttons
        self.module_buttons = {}

        for label, module_name in MODULES:
            button = ctk.CTkButton(
                self.sidebar,
                text="›    " + label,
                anchor="w",
                height=42,
                corner_radius=9,
                font=("Arial", 13),
                fg_color="transparent",
                hover_color=BG,
                text_color=TEXT,
                command=lambda name=module_name: self.open_module(name)
            )

            button.pack(
                fill="x",
                padx=13,
                pady=3
            )

            self.module_buttons[module_name] = button

        ctk.CTkFrame(
            self.sidebar,
            fg_color="transparent"
        ).pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.sidebar,
            text="Blood Bank Management\nPython • PostgreSQL",
            text_color=MUTED,
            font=("Arial", 10),
            justify="left"
        ).pack(anchor="w", padx=20, pady=20)

        # ==============================================
        # MAIN CONTENT AREA
        # ==============================================

        self.content = ctk.CTkFrame(
            self.main,
            fg_color=BG,
            corner_radius=0
        )

        self.content.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Top navigation bar
        self.topbar = ctk.CTkFrame(
            self.content,
            fg_color=CARD,
            corner_radius=0,
            height=76,
            border_width=1,
            border_color=BORDER
        )

        self.topbar.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.topbar.grid_columnconfigure(0, weight=1)

        self.page_title = ctk.CTkLabel(
            self.topbar,
            text="Dashboard Overview",
            font=("Arial", 23, "bold"),
            text_color=TEXT
        )

        self.page_title.grid(
            row=0,
            column=0,
            sticky="w",
            padx=25,
            pady=20
        )

        right = ctk.CTkFrame(
            self.topbar,
            fg_color="transparent"
        )

        right.grid(
            row=0,
            column=1,
            padx=18,
            pady=12
        )

        self.user_label = ctk.CTkLabel(
            right,
            text="Staff",
            text_color=TEXT,
            font=("Arial", 12, "bold")
        )

        self.user_label.pack(side="left", padx=10)

        self.theme_switch = ctk.CTkSwitch(
            right,
            text="Dark mode",
            command=self.toggle_theme,
            progress_color=RED
        )

        self.theme_switch.pack(side="left", padx=10)

        # ==============================================
        # DASHBOARD HOME PAGE
        # ==============================================

        self.body = ctk.CTkScrollableFrame(
            self.content,
            fg_color=BG,
            corner_radius=0
        )

        self.body.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=18
        )

        self.body.grid_columnconfigure(
            (0, 1, 2, 3),
            weight=1
        )

        self.build_dashboard_content()

        # ==============================================
        # EMBEDDED MODULE PAGE
        # ==============================================
        # Module screens will appear here instead of
        # opening a separate Toplevel window.

        self.page_host = ctk.CTkFrame(
            self.content,
            fg_color=BG,
            corner_radius=0
        )

        self.page_host.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=18
        )

        self.page_host.grid_remove()

    # --------------------------------------------------
    # DASHBOARD HOME CONTENT
    # --------------------------------------------------

    def build_dashboard_content(self):

        ctk.CTkLabel(
            self.body,
            text="Welcome back 👋",
            font=("Arial", 25, "bold"),
            text_color=TEXT
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(3, 3)
        )

        ctk.CTkLabel(
            self.body,
            text="Here is the current overview of your blood bank.",
            font=("Arial", 13),
            text_color=MUTED
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 20)
        )

        ctk.CTkButton(
            self.body,
            text="↻  Refresh",
            width=110,
            height=34,
            fg_color=RED,
            hover_color=RED_HOVER,
            command=self.refresh_dashboard
        ).grid(
            row=0,
            column=3,
            sticky="e",
            pady=4
        )

        cards = [
            ("Active Donors", "donors", "Registered active donors"),
            ("Total Donations", "donations", "Donation records"),
            ("Available Blood", "stock", "Millilitres in stock"),
            ("Pending Requests", "pending", "Awaiting action"),
        ]

        for column, (title, key, subtitle) in enumerate(cards):

            card = ctk.CTkFrame(
                self.body,
                fg_color=CARD,
                corner_radius=14,
                border_width=1,
                border_color=BORDER
            )

            card.grid(
                row=2,
                column=column,
                sticky="ew",
                padx=5,
                pady=(0, 18)
            )

            ctk.CTkLabel(
                card,
                text=title,
                text_color=MUTED,
                font=("Arial", 12, "bold")
            ).pack(
                anchor="w",
                padx=16,
                pady=(17, 5)
            )

            value_label = ctk.CTkLabel(
                card,
                text="—",
                text_color=TEXT,
                font=("Arial", 27, "bold")
            )

            value_label.pack(anchor="w", padx=16)

            ctk.CTkLabel(
                card,
                text=subtitle,
                text_color=MUTED,
                font=("Arial", 10)
            ).pack(
                anchor="w",
                padx=16,
                pady=(4, 17)
            )

            self.metric_labels[key] = value_label

        # Blood stock panel
        self.stock_panel = ctk.CTkFrame(
            self.body,
            fg_color=CARD,
            corner_radius=14,
            border_width=1,
            border_color=BORDER
        )

        self.stock_panel.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="nsew",
            padx=5,
            pady=5
        )

        ctk.CTkLabel(
            self.stock_panel,
            text="Blood Group Stock",
            font=("Arial", 17, "bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(18, 12))

        self.stock_frame = ctk.CTkFrame(
            self.stock_panel,
            fg_color="transparent"
        )

        self.stock_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )

        # Recent requests panel
        self.requests_panel = ctk.CTkFrame(
            self.body,
            fg_color=CARD,
            corner_radius=14,
            border_width=1,
            border_color=BORDER
        )

        self.requests_panel.grid(
            row=3,
            column=2,
            columnspan=2,
            sticky="nsew",
            padx=5,
            pady=5
        )

        ctk.CTkLabel(
            self.requests_panel,
            text="Recent Blood Requests",
            font=("Arial", 17, "bold"),
            text_color=TEXT
        ).pack(anchor="w", padx=18, pady=(18, 12))

        self.requests_frame = ctk.CTkFrame(
            self.requests_panel,
            fg_color="transparent"
        )

        self.requests_frame.pack(
            fill="both",
            expand=True,
            padx=18,
            pady=(0, 18)
        )

        self.status_label = ctk.CTkLabel(
            self.body,
            text="Ready",
            text_color=MUTED,
            font=("Arial", 11)
        )

        self.status_label.grid(
            row=4,
            column=0,
            columnspan=4,
            sticky="w",
            padx=7,
            pady=12
        )

    # --------------------------------------------------
    # THEME SWITCH
    # --------------------------------------------------

    def toggle_theme(self):
        mode = "Dark" if self.theme_switch.get() else "Light"
        ctk.set_appearance_mode(mode)

    # --------------------------------------------------
    # NAVIGATE TO DASHBOARD HOME
    # --------------------------------------------------

    def show_dashboard(self):

        # Remove the currently displayed module.
        for widget in self.page_host.winfo_children():
            widget.destroy()

        self.active_module = None
        self.active_module_frame = None

        # Show the home dashboard.
        self.page_host.grid_remove()
        self.body.grid()

        self.page_title.configure(
            text="Dashboard Overview"
        )

        self.dashboard_button.configure(
            fg_color=RED,
            hover_color=RED_HOVER,
            text_color="#FFFFFF"
        )

        for button in self.module_buttons.values():
            button.configure(
                fg_color="transparent",
                text_color=TEXT
            )

        self.refresh_dashboard()

    # --------------------------------------------------
    # OPEN A MODULE INSIDE THE MAIN WINDOW
    # --------------------------------------------------

    def open_module(self, module_name):

        # Enforce the existing role permissions.
        if not can_access_module(self.staff_role, module_name):
            messagebox.showwarning(
                "Access denied",
                "Your staff role does not have permission "
                "to open this module.",
                parent=self.root
            )
            return

        # Identify the selected module's title.
        module_title = next(
            (
                label
                for label, name in MODULES
                if name == module_name
            ),
            module_name
        )

        try:
            module = importlib.import_module(module_name)

            # Find the UI class defined in the module.
            ui_classes = [
                obj
                for obj in vars(module).values()
                if isinstance(obj, type)
                and obj.__module__ == module.__name__
            ]

            if len(ui_classes) != 1:
                raise RuntimeError(
                    f"Expected one UI class in {module_name}; "
                    f"found {len(ui_classes)}."
                )

            ui_class = ui_classes[0]

            # Clear the previous embedded page.
            for widget in self.page_host.winfo_children():
                widget.destroy()

            self.active_module = module_name

            # Hide the dashboard home page.
            self.body.grid_remove()

            # Display the module area in the same window.
            self.page_host.grid()

            self.page_title.configure(text=module_title)

            self.dashboard_button.configure(
                fg_color="transparent",
                text_color=TEXT
            )

            for name, button in self.module_buttons.items():
                if name == module_name:
                    button.configure(
                        fg_color=RED,
                        hover_color=RED_HOVER,
                        text_color="#FFFFFF"
                    )
                else:
                    button.configure(
                        fg_color="transparent",
                        text_color=TEXT
                    )

            # Create a frame that behaves like the old
            # module window, but is embedded in the dashboard.
            module_frame = EmbeddedModuleFrame(
                self.page_host,
                bg="#F4F6F9",
                bd=0,
                highlightthickness=0
            )

            module_frame.pack(
                fill="both",
                expand=True
            )

            self.active_module_frame = module_frame

            # Initialize the existing module inside this frame.
            ui = ui_class(module_frame)

            # Pass the logged-in staff ID without overwriting
            # any existing Entry widgets named staff_id.
            ui.current_staff_id = self.staff_id

            # Fill staff ID fields used by older module forms.
            for attr_name in (
                "staff_entry",
                "staff_id",
                "staff_id_entry"
            ):
                entry = getattr(ui, attr_name, None)

                if (
                    entry is not None
                    and hasattr(entry, "delete")
                    and hasattr(entry, "insert")
                ):
                    try:
                        entry.configure(state="normal")
                        entry.delete(0, tk.END)

                        if self.staff_id is not None:
                            entry.insert(0, str(self.staff_id))

                        # Make staff identity read-only when possible.
                        try:
                            entry.configure(state="readonly")
                        except tk.TclError:
                            pass

                    except (tk.TclError, AttributeError):
                        pass

            # Keep a reference to prevent accidental collection.
            self.active_module_ui = ui

        except Exception as exc:
            # Do not leave a partially constructed page behind.
            for widget in self.page_host.winfo_children():
                widget.destroy()

            self.active_module = None
            self.active_module_frame = None

            messagebox.showerror(
                "Could not open module",
                f"Module: {module_name}\n\n{exc}",
                parent=self.root
            )

            self.show_dashboard()

    # --------------------------------------------------
    # DASHBOARD DATA
    # --------------------------------------------------

    def refresh_dashboard(self):

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:

                    cur.execute(
                        "SELECT COUNT(*) FROM donor "
                        "WHERE is_active = TRUE"
                    )
                    donors = cur.fetchone()[0]

                    cur.execute(
                        "SELECT COUNT(*) FROM donation"
                    )
                    donations = cur.fetchone()[0]

                    cur.execute(
                        "SELECT COALESCE("
                        "SUM(available_quantity_ml), 0) "
                        "FROM blood_stock"
                    )
                    stock = cur.fetchone()[0]

                    cur.execute(
                        "SELECT COUNT(*) FROM blood_request "
                        "WHERE request_status = 'PENDING'"
                    )
                    pending = cur.fetchone()[0]

                    cur.execute("""
                        SELECT bg.blood_group_code,
                               bs.available_quantity_ml
                        FROM blood_stock bs
                        JOIN blood_group bg
                          ON bg.blood_group_code = bs.blood_group_code
                        ORDER BY bg.blood_group_code
                    """)
                    stock_rows = cur.fetchall()

                    cur.execute("""
                        SELECT br.request_id,
                               h.hospital_name,
                               br.blood_group_code,
                               br.quantity_requested_ml,
                               br.request_status
                        FROM blood_request br
                        JOIN hospital h
                          ON h.hospital_id = br.hospital_id
                        ORDER BY br.request_date DESC
                        LIMIT 5
                    """)
                    request_rows = cur.fetchall()

            metrics = {
                "donors": f"{donors:,}",
                "donations": f"{donations:,}",
                "stock": f"{stock:,} ml",
                "pending": f"{pending:,}"
            }

            for key, value in metrics.items():
                self.metric_labels[key].configure(
                    text=value
                )

            self.render_stock(stock_rows)
            self.render_requests(request_rows)

            self.status_label.configure(
                text="Dashboard updated successfully."
            )

        except Exception as exc:
            self.status_label.configure(
                text=f"Could not load dashboard data: {exc}"
            )

    # --------------------------------------------------
    # STOCK VISUALIZATION
    # --------------------------------------------------

    def render_stock(self, rows):

        for widget in self.stock_frame.winfo_children():
            widget.destroy()

        if not rows:
            ctk.CTkLabel(
                self.stock_frame,
                text="No stock records found.",
                text_color=MUTED
            ).pack(anchor="w")
            return

        max_quantity = max(
            [int(row[1]) for row in rows] + [1]
        )

        for group, quantity in rows:

            line = ctk.CTkFrame(
                self.stock_frame,
                fg_color="transparent"
            )

            line.pack(fill="x", pady=6)

            ctk.CTkLabel(
                line,
                text=group,
                width=48,
                font=("Arial", 12, "bold"),
                text_color=TEXT
            ).pack(side="left")

            bar = ctk.CTkProgressBar(
                line,
                progress_color=RED,
                height=9
            )

            bar.pack(
                side="left",
                fill="x",
                expand=True,
                padx=12
            )

            bar.set(
                max(0, min(1, int(quantity) / max_quantity))
            )

            ctk.CTkLabel(
                line,
                text=f"{quantity:,} ml",
                width=95,
                anchor="e",
                font=("Arial", 11),
                text_color=MUTED
            ).pack(side="right")

    # --------------------------------------------------
    # RECENT REQUESTS
    # --------------------------------------------------

    def render_requests(self, rows):

        for widget in self.requests_frame.winfo_children():
            widget.destroy()

        if not rows:
            ctk.CTkLabel(
                self.requests_frame,
                text="No requests found.",
                text_color=MUTED
            ).pack(anchor="w")
            return

        for request_id, hospital, group, quantity, status in rows:

            item = ctk.CTkFrame(
                self.requests_frame,
                fg_color=BG,
                corner_radius=9
            )

            item.pack(fill="x", pady=5)

            left = ctk.CTkFrame(
                item,
                fg_color="transparent"
            )

            left.pack(
                side="left",
                fill="x",
                expand=True,
                padx=10,
                pady=9
            )

            ctk.CTkLabel(
                left,
                text=f"Request #{request_id} • {group}",
                font=("Arial", 12, "bold"),
                text_color=TEXT
            ).pack(anchor="w")

            ctk.CTkLabel(
                left,
                text=f"{hospital} • {quantity:,} ml",
                font=("Arial", 10),
                text_color=MUTED
            ).pack(anchor="w", pady=(3, 0))

            ctk.CTkLabel(
                item,
                text=status.replace("_", " "),
                font=("Arial", 10, "bold"),
                text_color=RED if status == "PENDING" else MUTED
            ).pack(side="right", padx=10)

    # --------------------------------------------------
    # UPDATE ROLE-BASED MENU ACCESS
    # --------------------------------------------------

    def update_menu_permissions(self):

        for label, module_name in MODULES:
            button = self.module_buttons[module_name]

            allowed = can_access_module(
                self.staff_role,
                module_name
            )

            button.configure(
                state="normal" if allowed else "disabled"
            )
