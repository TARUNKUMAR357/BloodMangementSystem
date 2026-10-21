
import tkinter as tk
from tkinter import ttk, messagebox

from config.database import get_connection


class HospitalManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Management")
        self.root.geometry("1000x650")
        self.root.configure(bg="#F4F6F9")

        self.selected_hospital_id = None
        self.build_ui()
        self.load_hospitals()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#9F1D25", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="HOSPITAL MANAGEMENT",
            font=("Arial", 20, "bold"),
            bg="#9F1D25",
            fg="white"
        ).pack(pady=15)

        form = ttk.LabelFrame(
            self.root, text="Hospital Details", padding=15
        )
        form.pack(fill="x", padx=15, pady=12)

        fields = [
            ("Hospital Name", "hospital_name"),
            ("Phone", "phone"),
            ("Email", "email"),
            ("Address", "address")
        ]

        self.fields = {}

        for index, (label, key) in enumerate(fields):
            row = index // 2
            col = (index % 2) * 2

            ttk.Label(form, text=label).grid(
                row=row, column=col,
                padx=8, pady=8, sticky="w"
            )

            entry = ttk.Entry(form, width=35)
            entry.grid(
                row=row, column=col + 1,
                padx=8, pady=8, sticky="ew"
            )

            self.fields[key] = entry

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        actions = ttk.Frame(self.root)
        actions.pack(fill="x", padx=15, pady=5)

        ttk.Button(
            actions, text="Add Hospital",
            command=self.add_hospital
        ).pack(side="left", padx=5)

        ttk.Button(
            actions, text="Update Selected",
            command=self.update_hospital
        ).pack(side="left", padx=5)

        ttk.Button(
            actions, text="Clear Form",
            command=self.clear_form
        ).pack(side="left", padx=5)

        search_frame = ttk.LabelFrame(
            self.root, text="Search Hospitals", padding=10
        )
        search_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(
            search_frame, text="Hospital Name:"
        ).pack(side="left", padx=5)

        self.search_entry = ttk.Entry(
            search_frame, width=30
        )
        self.search_entry.pack(side="left", padx=5)

        ttk.Button(
            search_frame, text="Search",
            command=self.load_hospitals
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame, text="Show All",
            command=self.reset_search
        ).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both", expand=True, padx=15, pady=10
        )

        columns = (
            "id", "name", "phone", "email", "address"
        )

        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings"
        )

        headings = {
            "id": "Hospital ID",
            "name": "Hospital Name",
            "phone": "Phone",
            "email": "Email",
            "address": "Address"
        }

        widths = {
            "id": 90, "name": 220, "phone": 140,
            "email": 200, "address": 220
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(
                col, width=widths[col], anchor="w"
            )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind(
            "<<TreeviewSelect>>", self.select_hospital
        )

    def get_form_data(self):
        data = {
            key: widget.get().strip()
            for key, widget in self.fields.items()
        }

        if not data["hospital_name"]:
            raise ValueError("Hospital name is required.")

        # Store empty optional fields as SQL NULL.
        for key in ("phone", "email", "address"):
            if not data[key]:
                data[key] = None

        if data["email"] and "@" not in data["email"]:
            raise ValueError("Enter a valid email address.")

        return data

    def add_hospital(self):
        try:
            data = self.get_form_data()

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO hospital (
                            hospital_name, phone, email, address
                        )
                        VALUES (%s, %s, %s, %s)
                        RETURNING hospital_id
                        """,
                        (
                            data["hospital_name"],
                            data["phone"],
                            data["email"],
                            data["address"]
                        )
                    )
                    hospital_id = cur.fetchone()[0]

            messagebox.showinfo(
                "Success",
                f"Hospital registered. ID: {hospital_id}"
            )
            self.clear_form()
            self.load_hospitals()

        except ValueError as error:
            messagebox.showwarning(
                "Invalid Input", str(error)
            )
        except Exception as error:
            messagebox.showerror(
                "Database Error", str(error)
            )

    def load_hospitals(self):
        search = self.search_entry.get().strip()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT hospital_id, hospital_name,
                               phone, email, address
                        FROM hospital
                        WHERE (%s = ''
                               OR hospital_name ILIKE %s)
                        ORDER BY hospital_id
                        """,
                        (search, f"%{search}%")
                    )
                    rows = cur.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert(
                    "", "end",
                    values=[
                        value if value is not None else ""
                        for value in row
                    ]
                )

        except Exception as error:
            messagebox.showerror(
                "Database Error", str(error)
            )

    def select_hospital(self, event=None):
        selection = self.tree.selection()

        if not selection:
            return

        values = self.tree.item(
            selection[0], "values"
        )

        self.selected_hospital_id = int(values[0])

        keys = ["hospital_name", "phone", "email", "address"]

        for key, value in zip(keys, values[1:]):
            self.fields[key].delete(0, tk.END)
            if value:
                self.fields[key].insert(0, value)

    def update_hospital(self):
        if self.selected_hospital_id is None:
            messagebox.showwarning(
                "Select Hospital",
                "Select a hospital from the table first."
            )
            return

        try:
            data = self.get_form_data()

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE hospital
                        SET hospital_name = %s,
                            phone = %s,
                            email = %s,
                            address = %s
                        WHERE hospital_id = %s
                        """,
                        (
                            data["hospital_name"],
                            data["phone"],
                            data["email"],
                            data["address"],
                            self.selected_hospital_id
                        )
                    )

                    if cur.rowcount == 0:
                        raise ValueError("Hospital not found.")

            messagebox.showinfo(
                "Success", "Hospital details updated."
            )
            self.clear_form()
            self.load_hospitals()

        except ValueError as error:
            messagebox.showwarning(
                "Update Failed", str(error)
            )
        except Exception as error:
            messagebox.showerror(
                "Database Error", str(error)
            )

    def clear_form(self):
        for widget in self.fields.values():
            widget.delete(0, tk.END)

        self.selected_hospital_id = None

        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.load_hospitals()


if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalManagement(root)
    root.mainloop()
