import customtkinter as ctk
from login_ui import LoginWindow

def main():
    ctk.set_appearance_mode("Light")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Blood Bank Management System")
    root.geometry("1000x650")

    LoginWindow(root)

    root.mainloop()

if __name__ == "__main__":
    main()