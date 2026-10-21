
import tkinter as tk
from tkinter import ttk, messagebox

from config.database import get_connection


REQUEST_STATUSES = (
    "PENDING",
    "APPROVED",
    "PARTIALLY_FULFILLED",
    "FULFILLED",
    "REJECTED"
)


class BloodRequestManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Blood Request Management")
        self.root.geometry("1150x680")
        self.root.configure(bg="#F4F6F9")

        self.selected_request_id = None
        self.build_ui()
        self.load_requests()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#9F1D25", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="BLOOD REQUEST MANAGEMENT",
            font=("Arial", 19, "bold"),
            bg="#9F1D25",
            fg="white"
        ).pack(pady=14)

        form = ttk.LabelFrame(
            self.root, text="Create Blood Request", padding=12
        )
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Hospital").grid(
            row=0, column=0, padx=6, pady=7, sticky="w"
        )
        self.hospital_combo = ttk.Combobox(
            form, state="readonly", width=32
        )
        self.hospital_combo.grid(
            row=0, column=1, padx=6, pady=7, sticky="ew"
        )

        ttk.Label(form, text="Blood Group").grid(
            row=0, column=2, padx=6, pady=7, sticky="w"
        )
        self.group_combo = ttk.Combobox(
            form,
            state="readonly",
            values=("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"),
            width=12
        )
        self.group_combo.grid(
            row=0, column=3, padx=6, pady=7, sticky="ew"
        )

        ttk.Label(form, text="Quantity (mL)").grid(
            row=1, column=0, padx=6, pady=7, sticky="w"
        )
        self.quantity_entry = ttk.Entry(form, width=20)
        self.quantity_entry.grid(
            row=1, column=1, padx=6, pady=7, sticky="ew"
        )

        ttk.Label(form, text="Staff ID").grid(
            row=1, column=2, padx=6, pady=7, sticky="w"
        )
        self.staff_entry = ttk.Entry(form, width=15)
        self.staff_entry.grid(
            row=1, column=3, padx=6, pady=7, sticky="ew"
        )

        for column in (1, 3):
            form.columnconfigure(column, weight=1)

        ttk.Button(
            form,
            text="Create Request",
            command=self.create_request
        ).grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(
            form,
            text="Clear Form",
            command=self.clear_form
        ).grid(row=2, column=2, columnspan=2, pady=10)

        self.load_form_options()

        search_frame = ttk.LabelFrame(
            self.root, text="Search Requests", padding=10
        )
        search_frame.pack(fill="x", padx=15, pady=5)

        ttk.Label(
            search_frame, text="Hospital Name:"
        ).pack(side="left", padx=5)

        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="Search",
            command=self.load_requests
        ).pack(side="left", padx=5)

        ttk.Button(
            search_frame,
            text="Show All",
            command=self.reset_search
        ).pack(side="left", padx=5)

        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", padx=15, pady=5)

        ttk.Button(
            action_frame,
            text="Approve Selected",
            command=self.approve_request
        ).pack(side="left", padx=5)

        ttk.Button(
            action_frame,
            text="Reject Selected",
            command=self.reject_request
        ).pack(side="left", padx=5)

        ttk.Button(
            action_frame,
            text="Refresh",
            command=self.load_requests
        ).pack(side="left", padx=5)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both", expand=True, padx=15, pady=10
        )

        columns = (
            "id", "hospital", "group", "quantity",
            "date", "status", "staff"
        )

        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings"
        )

        headings = {
            "id": "Request ID",
            "hospital": "Hospital",
            "group": "Blood Group",
            "quantity": "Quantity (mL)",
            "date": "Request Date",
            "status": "Status",
            "staff": "Staff ID"
        }

        widths = {
            "id": 85, "hospital": 210, "group": 100,
            "quantity": 120, "date": 170,
            "status": 190, "staff": 85
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column, width=widths[column], anchor="center"
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
            "<<TreeviewSelect>>", self.select_request
        )

    def load_form_options(self):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT hospital_id, hospital_name
                        FROM hospital
                        ORDER BY hospital_name
                        """
                    )
                    hospitals = cur.fetchall()

                    cur.execute(
                        """
                        SELECT blood_group_code
                        FROM blood_group
                        ORDER BY blood_group_code
                        """
                    )
                    groups = [row[0] for row in cur.fetchall()]

            self.hospital_options = {
                f"{name} (ID: {hospital_id})": hospital_id
                for hospital_id, name in hospitals
            }
            self.hospital_combo["values"] = list(
                self.hospital_options.keys()
            )
            self.group_combo["values"] = groups

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"Could not load form options:\n{error}"
            )

    def create_request(self):
        hospital_label = self.hospital_combo.get()
        group = self.group_combo.get()
        quantity_text = self.quantity_entry.get().strip()
        staff_text = self.staff_entry.get().strip()

        if not hospital_label or not group:
            messagebox.showwarning(
                "Missing Information",
                "Select a hospital and blood group."
            )
            return

        try:
            quantity = int(quantity_text)
            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")

            staff_id = int(staff_text)
            if staff_id <= 0:
                raise ValueError("Staff ID must be positive.")

        except ValueError as error:
            messagebox.showwarning(
                "Invalid Input",
                f"Enter a valid quantity and staff ID.\n{error}"
            )
            return

        hospital_id = self.hospital_options[hospital_label]

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Confirm the staff ID exists.
                    cur.execute(
                        "SELECT 1 FROM staff WHERE staff_id = %s",
                        (staff_id,)
                    )
                    if cur.fetchone() is None:
                        raise ValueError("Staff ID does not exist.")

                    cur.execute(
                        """
                        INSERT INTO blood_request (
                            hospital_id,
                            blood_group_code,
                            quantity_requested_ml,
                            request_status,
                            staff_id
                        )
                        VALUES (%s, %s, %s, 'PENDING', %s)
                        RETURNING request_id
                        """,
                        (hospital_id, group, quantity, staff_id)
                    )
                    request_id = cur.fetchone()[0]

            messagebox.showinfo(
                "Success",
                f"Blood request created. Request ID: {request_id}"
            )
            self.clear_form()
            self.load_requests()

        except ValueError as error:
            messagebox.showwarning("Invalid Request", str(error))
        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    def load_requests(self):
        search = self.search_entry.get().strip()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT br.request_id,
                               h.hospital_name,
                               br.blood_group_code,
                               br.quantity_requested_ml,
                               br.request_date,
                               br.request_status,
                               br.staff_id
                        FROM blood_request br
                        JOIN hospital h
                          ON h.hospital_id = br.hospital_id
                        WHERE (%s = ''
                               OR h.hospital_name ILIKE %s)
                        ORDER BY br.request_date DESC,
                                 br.request_id DESC
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

    def select_request(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        self.selected_request_id = int(values[0])

    def change_status(self, new_status):
        if self.selected_request_id is None:
            messagebox.showwarning(
                "Select Request",
                "Select a request from the table first."
            )
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE blood_request
                        SET request_status = %s
                        WHERE request_id = %s
                          AND request_status = 'PENDING'
                        """,
                        (new_status, self.selected_request_id)
                    )

                    if cur.rowcount == 0:
                        raise ValueError(
                            "Only pending requests can be approved "
                            "or rejected."
                        )

            messagebox.showinfo(
                "Success",
                f"Request {self.selected_request_id} "
                f"marked as {new_status}."
            )
            self.selected_request_id = None
            self.load_requests()

        except ValueError as error:
            messagebox.showwarning("Status Not Changed", str(error))
        except Exception as error:
            messagebox.showerror("Database Error", str(error))

    def approve_request(self):
        self.change_status("APPROVED")

    def reject_request(self):
        self.change_status("REJECTED")

    def clear_form(self):
        self.hospital_combo.set("")
        self.group_combo.set("")
        self.quantity_entry.delete(0, tk.END)
        self.staff_entry.delete(0, tk.END)

    def reset_search(self):
        self.search_entry.delete(0, tk.END)
        self.load_requests()


if __name__ == "__main__":
    root = tk.Tk()
    app = BloodRequestManagement(root)
    root.mainloop()
