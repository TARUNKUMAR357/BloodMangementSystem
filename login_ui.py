import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from config.database import get_connection
from auth import verify_password

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

BG = ("#F4F6FA", "#15171C")
CARD = ("#FFFFFF", "#20232A")
TEXT = ("#202637", "#F4F5F7")
MUTED = ("#70798B", "#A6ADBB")
RED = "#B91C1C"


class LoginWindow:
    """Premium staff sign-in screen. Uses the existing staff table/auth module."""
    def __init__(self, root):
        self.root = root
        self.root.title("LIFEPOINT | Staff Login")
        self.root.geometry("980x620")
        self.root.minsize(780, 520)
        self.root.configure(bg="#F4F6FA")
        self.build_ui()

    def build_ui(self):
        self.login_frame = ctk.CTkFrame(self.root, fg_color=BG, corner_radius=0)
        self.login_frame.pack(fill="both", expand=True)
        self.login_frame.grid_columnconfigure((0, 1), weight=1)
        self.login_frame.grid_rowconfigure(0, weight=1)

        brand = ctk.CTkFrame(self.login_frame, fg_color=RED, corner_radius=0)
        brand.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(brand, text="✚", font=("Arial", 68, "bold"), text_color="white").pack(anchor="w", padx=45, pady=(75, 5))
        ctk.CTkLabel(brand, text="LIFEPOINT", font=("Arial", 30, "bold"), text_color="white").pack(anchor="w", padx=45)
        ctk.CTkLabel(brand, text="BLOOD BANK MANAGEMENT", font=("Arial", 13, "bold"), text_color="#FEE2E2").pack(anchor="w", padx=45, pady=(5, 22))
        ctk.CTkLabel(brand, text="Every donation can help save a life.", font=("Arial", 15), text_color="white").pack(anchor="w", padx=45)
        ctk.CTkLabel(brand, text="STAFF ACCESS  •  POSTGRESQL", font=("Arial", 10, "bold"), text_color="#FEE2E2").pack(anchor="w", padx=45, pady=(115, 0))

        panel = ctk.CTkFrame(self.login_frame, fg_color=CARD, corner_radius=0)
        panel.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(panel, text="Welcome back", font=("Arial", 28, "bold"), text_color=TEXT).pack(anchor="w", padx=42, pady=(85, 5))
        ctk.CTkLabel(panel, text="Sign in with your staff account.", font=("Arial", 13), text_color=MUTED).pack(anchor="w", padx=42, pady=(0, 25))

        ctk.CTkLabel(panel, text="Username", text_color=TEXT).pack(anchor="w", padx=42)
        self.username_entry = ctk.CTkEntry(panel, width=310, height=42, placeholder_text="Enter username")
        self.username_entry.pack(padx=42, pady=(6, 18))

        ctk.CTkLabel(panel, text="Password", text_color=TEXT).pack(anchor="w", padx=42)
        self.password_entry = ctk.CTkEntry(panel, width=310, height=42, placeholder_text="Enter password", show="•")
        self.password_entry.pack(padx=42, pady=(6, 20))

        self.login_button = ctk.CTkButton(panel, text="Sign in", width=310, height=44, fg_color=RED, hover_color="#991B1B", command=self.login)
        self.login_button.pack(padx=42, pady=(0, 12))
        ctk.CTkLabel(panel, text="Authorized staff only", text_color=MUTED, font=("Arial", 10)).pack(anchor="w", padx=42, pady=(4, 0))
        self.root.bind("<Return>", self.handle_enter)
        self.username_entry.focus_set()

    def handle_enter(self, _event=None):
        self.login()

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            messagebox.showwarning("Missing details", "Enter both username and password.", parent=self.root)
            return

        self.login_button.configure(state="disabled", text="Signing in…")
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT staff_id, full_name, role, password_hash FROM staff WHERE username = %s",
                        (username,),
                    )
                    staff = cur.fetchone()
        except Exception:
            messagebox.showerror(
                "Database connection error",
                "Could not connect to PostgreSQL. Check that the server is running and DB_* settings are correct.",
                parent=self.root,
            )
            self.login_button.configure(state="normal", text="Sign in")
            return

        if staff is None or not verify_password(password, staff[3]):
            messagebox.showerror("Sign-in failed", "Invalid username or password.", parent=self.root)
            self.password_entry.delete(0, tk.END)
            self.login_button.configure(state="normal", text="Sign in")
            return

        staff_id, full_name, role, _stored_hash = staff
        if role not in ("ADMIN", "STAFF"):
            messagebox.showerror("Access denied", "This account has an invalid role.", parent=self.root)
            self.login_button.configure(state="normal", text="Sign in")
            return

        
            # Close only the login screen
        self.root.unbind("<Return>")
        self.login_frame.destroy()

# Open the dashboard
        from dashboard import BloodBankDashboard

        dashboard = BloodBankDashboard(self.root)

        self.root.title(
        f"Blood Bank Management System — {full_name}"
        )

        dashboard.set_user(
        staff_id,
        full_name,
        role
        )

        self.dashboard = dashboard

        

if __name__ == "__main__":
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()
