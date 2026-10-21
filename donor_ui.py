import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config.database import get_connection


class DonorManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Donor Management")
        self.root.geometry("1250x800")
        self.root.configure(bg="#F4F6F9")

        self.selected_donor_id = None
        self.fields = {}

        self.build_ui()
        self.load_donors()

    def build_ui(self):
        # Larger, more readable fonts
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 12), rowheight=32)
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12))
        style.configure("TEntry", font=("Arial", 12))
        style.configure("TCombobox", font=("Arial", 12))
        style.configure("TLabelframe.Label", font=("Arial", 12, "bold"))

        # Header
        header = tk.Frame(self.root, bg="#9F1D25", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="DONOR MANAGEMENT",
            font=("Arial", 22, "bold"),
            bg="#9F1D25",
            fg="white",
        ).pack(pady=14)

        # Donor form
        form = ttk.LabelFrame(
            self.root,
            text="Donor Details",
            padding=12,
        )
        form.pack(fill="x", padx=15, pady=(10, 6))

        labels = [
            ("Full Name", "full_name"),
            ("Date of Birth (YYYY-MM-DD)", "date_of_birth"),
            ("Gender", "gender"),
            ("Blood Group", "blood_group_code"),
            ("Phone", "phone"),
            ("Email", "email"),
            ("Address", "address"),
        ]

        for index, (label, key) in enumerate(labels):
            row = index // 2
            col = (index % 2) * 2

            ttk.Label(form, text=label).grid(
                row=row,
                column=col,
                padx=8,
                pady=7,
                sticky="w",
            )

            if key == "blood_group_code":
                widget = ttk.Combobox(
                    form,
                    values=[
                        "A+", "A-", "B+", "B-",
                        "AB+", "AB-", "O+", "O-",
                    ],
                    state="readonly",
                    width=25,
                    font=("Arial", 12),
                )
            elif key == "gender":
                widget = ttk.Combobox(
                    form,
                    values=[
                        "Male", "Female", "Other",
                        "Prefer not to say",
                    ],
                    state="readonly",
                    width=25,
                    font=("Arial", 12),
                )
            else:
                widget = ttk.Entry(
                    form,
                    width=28,
                    font=("Arial", 12),
                )

            widget.grid(
                row=row,
                column=col + 1,
                padx=8,
                pady=7,
                sticky="ew",
                ipady=3,
            )

            self.fields[key] = widget

        for col in range(4):
            form.columnconfigure(col, weight=1)

        # Action buttons
        buttons = ttk.Frame(self.root)
        buttons.pack(fill="x", padx=15, pady=5)

        ttk.Button(
            buttons,
            text="Add Donor",
            command=self.add_donor,
        ).pack(side="left", padx=5, ipady=3)

        ttk.Button(
            buttons,
            text="Update Selected",
            command=self.update_donor,
        ).pack(side="left", padx=5, ipady=3)

        ttk.Button(
            buttons,
            text="Deactivate Selected",
            command=self.deactivate_donor,
        ).pack(side="left", padx=5, ipady=3)

        ttk.Button(
            buttons,
            text="Clear Form",
            command=self.clear_form,
        ).pack(side="left", padx=5, ipady=3)

        # Search section
        search_frame = ttk.LabelFrame(
            self.root,
            text="Search Donors",
            padding=10,
        )
        search_frame.pack(fill="x", padx=15, pady=8)

        ttk.Label(
            search_frame,
            text="Name:",
        ).grid(row=0, column=0, padx=8, pady=5, sticky="w")

        self.search_name = ttk.Entry(
            search_frame,
            width=28,
            font=("Arial", 12),
        )
        self.search_name.grid(
            row=0,
            column=1,
            padx=8,
            pady=5,
            sticky="ew",
        )
        self.search_name.bind("<Return>", self._search_on_enter)

        ttk.Label(
            search_frame,
            text="Blood Group:",
        ).grid(row=0, column=2, padx=8, pady=5, sticky="w")

        self.search_group = ttk.Combobox(
            search_frame,
            values=[
                "", "A+", "A-", "B+", "B-",
                "AB+", "AB-", "O+", "O-",
            ],
            state="readonly",
            width=12,
            font=("Arial", 12),
            height=9,
        )
        self.search_group.set("")
        self.search_group.grid(
            row=0,
            column=3,
            padx=8,
            pady=5,
            sticky="w",
        )
        self.search_group.bind(
            "<<ComboboxSelected>>",
            self._search_group_selected,
        )

        ttk.Button(
            search_frame,
            text="Search",
            command=self.load_donors,
        ).grid(row=0, column=4, padx=8, pady=5, ipady=3)

        ttk.Button(
            search_frame,
            text="Show All Active",
            command=self.reset_search,
        ).grid(row=0, column=5, padx=8, pady=5, ipady=3)

        search_frame.columnconfigure(1, weight=1)

        # Donor table
        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 12),
        )

        columns = (
            "id", "name", "dob", "gender",
            "group", "phone", "email", "address",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "id": "ID",
            "name": "Full Name",
            "dob": "Date of Birth",
            "gender": "Gender",
            "group": "Blood Group",
            "phone": "Phone",
            "email": "Email",
            "address": "Address",
        }

        widths = {
            "id": 65,
            "name": 190,
            "dob": 145,
            "gender": 125,
            "group": 125,
            "phone": 155,
            "email": 240,
            "address": 220,
        }

        for column in columns:
            self.tree.heading(
                column,
                text=headings[column],
            )
            self.tree.column(
                column,
                width=widths[column],
                minwidth=55 if column == "id" else 75,
                anchor="w",
                stretch=True,
            )

        vertical_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview,
        )

        horizontal_scrollbar = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview,
        )

        self.tree.configure(
            yscrollcommand=vertical_scrollbar.set,
            xscrollcommand=horizontal_scrollbar.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scrollbar.grid(row=0, column=1, sticky="ns")
        horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_donor,
        )

    def _search_on_enter(self, event=None):
        self.load_donors()
        return "break"

    def _search_group_selected(self, event=None):
        self.load_donors()

    def get_form_data(self):
        data = {
            key: widget.get().strip()
            for key, widget in self.fields.items()
        }

        if not data["full_name"]:
            raise ValueError("Full name is required.")

        if not data["date_of_birth"]:
            raise ValueError("Date of birth is required.")

        try:
            datetime.strptime(
                data["date_of_birth"],
                "%Y-%m-%d",
            )
        except ValueError:
            raise ValueError(
                "Enter date of birth in YYYY-MM-DD format."
            )

        if data["date_of_birth"] > datetime.today().strftime("%Y-%m-%d"):
            raise ValueError("Date of birth cannot be in the future.")

        if not data["blood_group_code"]:
            raise ValueError("Select a blood group.")

        for key in ("gender", "phone", "email", "address"):
            if not data[key]:
                data[key] = None

        return data

    def add_donor(self):
        try:
            data = self.get_form_data()

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO donor (
                            full_name, date_of_birth, gender,
                            blood_group_code, phone, email, address
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING donor_id
                        """,
                        (
                            data["full_name"],
                            data["date_of_birth"],
                            data["gender"],
                            data["blood_group_code"],
                            data["phone"],
                            data["email"],
                            data["address"],
                        ),
                    )
                    donor_id = cur.fetchone()[0]

            messagebox.showinfo(
                "Success",
                f"Donor added successfully. ID: {donor_id}",
                parent=self.root,
            )
            self.clear_form()
            self.load_donors()

        except ValueError as error:
            messagebox.showwarning(
                "Invalid Input",
                str(error),
                parent=self.root,
            )
        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=self.root,
            )

    def load_donors(self):
        name = self.search_name.get().strip()
        group = self.search_group.get().strip()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            donor_id,
                            full_name,
                            date_of_birth,
                            gender,
                            blood_group_code,
                            phone,
                            email,
                            address
                        FROM donor
                        WHERE is_active = TRUE
                          AND (%s = '' OR full_name ILIKE %s)
                          AND (%s = '' OR blood_group_code = %s)
                        ORDER BY donor_id
                        """,
                        (name, f"%{name}%", group, group),
                    )
                    rows = cur.fetchall()

            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in rows:
                self.tree.insert(
                    "",
                    "end",
                    values=[
                        value if value is not None else ""
                        for value in row
                    ],
                )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=self.root,
            )

    def select_donor(self, event=None):
        selection = self.tree.selection()

        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        self.selected_donor_id = int(values[0])

        keys = [
            "full_name",
            "date_of_birth",
            "gender",
            "blood_group_code",
            "phone",
            "email",
            "address",
        ]

        for key, value in zip(keys, values[1:]):
            widget = self.fields[key]
            widget.delete(0, tk.END)

            if value:
                widget.insert(0, value)

    def update_donor(self):
        if self.selected_donor_id is None:
            messagebox.showwarning(
                "Select Donor",
                "Select a donor from the table first.",
                parent=self.root,
            )
            return

        try:
            data = self.get_form_data()

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE donor
                        SET full_name = %s,
                            date_of_birth = %s,
                            gender = %s,
                            blood_group_code = %s,
                            phone = %s,
                            email = %s,
                            address = %s
                        WHERE donor_id = %s
                          AND is_active = TRUE
                        """,
                        (
                            data["full_name"],
                            data["date_of_birth"],
                            data["gender"],
                            data["blood_group_code"],
                            data["phone"],
                            data["email"],
                            data["address"],
                            self.selected_donor_id,
                        ),
                    )

                    if cur.rowcount == 0:
                        raise ValueError(
                            "Donor not found or inactive."
                        )

            messagebox.showinfo(
                "Success",
                "Donor updated successfully.",
                parent=self.root,
            )
            self.clear_form()
            self.load_donors()

        except ValueError as error:
            messagebox.showwarning(
                "Update Failed",
                str(error),
                parent=self.root,
            )
        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=self.root,
            )

    def deactivate_donor(self):
        if self.selected_donor_id is None:
            messagebox.showwarning(
                "Select Donor",
                "Select a donor from the table first.",
                parent=self.root,
            )
            return

        confirmed = messagebox.askyesno(
            "Confirm Deactivation",
            "Deactivate this donor? Historical records will remain.",
            parent=self.root,
        )

        if not confirmed:
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE donor
                        SET is_active = FALSE
                        WHERE donor_id = %s
                          AND is_active = TRUE
                        """,
                        (self.selected_donor_id,),
                    )

                    if cur.rowcount == 0:
                        raise ValueError(
                            "Donor not found or already inactive."
                        )

            messagebox.showinfo(
                "Success",
                "Donor deactivated.",
                parent=self.root,
            )
            self.clear_form()
            self.load_donors()

        except ValueError as error:
            messagebox.showwarning(
                "Deactivation Failed",
                str(error),
                parent=self.root,
            )
        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=self.root,
            )

    def clear_form(self):
        for widget in self.fields.values():
            widget.delete(0, tk.END)

        self.selected_donor_id = None

        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def reset_search(self):
        self.search_name.delete(0, tk.END)
        self.search_group.set("")
        self.load_donors()


if __name__ == "__main__":
    root = tk.Tk()
    app = DonorManagement(root)
    root.mainloop()