
import tkinter as tk
from tkinter import ttk, messagebox

from config.database import get_connection


class BloodIssueManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Blood Issue Management")
        self.root.geometry("1150x650")
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
            text="BLOOD ISSUE MANAGEMENT",
            font=("Arial", 19, "bold"),
            bg="#9F1D25",
            fg="white"
        ).pack(pady=14)

        info = ttk.LabelFrame(
            self.root, text="Issue Blood", padding=12
        )
        info.pack(fill="x", padx=15, pady=10)

        ttk.Label(
            info, text="Selected Request ID:"
        ).grid(row=0, column=0, padx=8, pady=8, sticky="w")

        self.request_label = ttk.Label(
            info, text="No request selected"
        )
        self.request_label.grid(
            row=0, column=1, padx=8, pady=8, sticky="w"
        )

        ttk.Label(
            info, text="Quantity to Issue (mL):"
        ).grid(row=1, column=0, padx=8, pady=8, sticky="w")

        self.quantity_entry = ttk.Entry(info, width=22)
        self.quantity_entry.grid(
            row=1, column=1, padx=8, pady=8, sticky="w"
        )

        ttk.Label(
            info, text="Staff ID:"
        ).grid(row=1, column=2, padx=8, pady=8, sticky="w")

        self.staff_entry = ttk.Entry(info, width=15)
        self.staff_entry.grid(
            row=1, column=3, padx=8, pady=8, sticky="w"
        )

        ttk.Button(
            info,
            text="Issue Blood",
            command=self.issue_blood
        ).grid(row=2, column=0, padx=8, pady=10)

        ttk.Button(
            info,
            text="Clear Selection",
            command=self.clear_selection
        ).grid(row=2, column=1, padx=8, pady=10, sticky="w")

        ttk.Button(
            info,
            text="Refresh Requests",
            command=self.load_requests
        ).grid(row=2, column=2, padx=8, pady=10)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both", expand=True, padx=15, pady=10
        )

        columns = (
            "id", "hospital", "group", "requested",
            "issued", "remaining", "stock", "status"
        )

        self.tree = ttk.Treeview(
            table_frame, columns=columns, show="headings"
        )

        headings = {
            "id": "Request ID",
            "hospital": "Hospital",
            "group": "Blood Group",
            "requested": "Requested (mL)",
            "issued": "Issued (mL)",
            "remaining": "Remaining (mL)",
            "stock": "Stock (mL)",
            "status": "Status"
        }

        widths = {
            "id": 80,
            "hospital": 190,
            "group": 90,
            "requested": 120,
            "issued": 105,
            "remaining": 120,
            "stock": 100,
            "status": 180
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

    def load_requests(self):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            br.request_id,
                            h.hospital_name,
                            br.blood_group_code,
                            br.quantity_requested_ml,
                            COALESCE(
                                (
                                    SELECT SUM(bi.quantity_issued_ml)
                                    FROM blood_issue bi
                                    WHERE bi.request_id = br.request_id
                                ), 0
                            ) AS total_issued,
                            br.quantity_requested_ml -
                            COALESCE(
                                (
                                    SELECT SUM(bi.quantity_issued_ml)
                                    FROM blood_issue bi
                                    WHERE bi.request_id = br.request_id
                                ), 0
                            ) AS remaining,
                            bs.available_quantity_ml,
                            br.request_status
                        FROM blood_request br
                        JOIN hospital h
                          ON h.hospital_id = br.hospital_id
                        JOIN blood_stock bs
                          ON bs.blood_group_code = br.blood_group_code
                        WHERE br.request_status IN (
                            'APPROVED', 'PARTIALLY_FULFILLED'
                        )
                        ORDER BY br.request_date, br.request_id
                        """
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
                "Database Error",
                f"Could not load requests:\n{error}"
            )

    def select_request(self, event=None):
        selection = self.tree.selection()

        if not selection:
            return

        values = self.tree.item(selection[0], "values")
        self.selected_request_id = int(values[0])

        self.request_label.config(
            text=f"Request #{self.selected_request_id} — "
                 f"{values[1]}, {values[2]}, "
                 f"{values[5]} mL remaining"
        )

    def issue_blood(self):
        if self.selected_request_id is None:
            messagebox.showwarning(
                "Select Request",
                "Select an approved request from the table."
            )
            return

        quantity_text = self.quantity_entry.get().strip()
        staff_text = self.staff_entry.get().strip()

        try:
            quantity = int(quantity_text)
            staff_id = int(staff_text)

            if quantity <= 0:
                raise ValueError(
                    "Issue quantity must be greater than zero."
                )

            if staff_id <= 0:
                raise ValueError("Staff ID must be positive.")

        except ValueError as error:
            messagebox.showwarning(
                "Invalid Input",
                f"Enter a valid quantity and staff ID.\n{error}"
            )
            return

        request_id = self.selected_request_id

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:

                    # Lock the request so two transactions cannot
                    # issue against its remaining quantity at once.
                    cur.execute(
                        """
                        SELECT blood_group_code,
                               quantity_requested_ml,
                               request_status
                        FROM blood_request
                        WHERE request_id = %s
                        FOR UPDATE
                        """,
                        (request_id,)
                    )
                    request = cur.fetchone()

                    if request is None:
                        raise ValueError("Request does not exist.")

                    group, requested, status = request

                    if status not in (
                        "APPROVED", "PARTIALLY_FULFILLED"
                    ):
                        raise ValueError(
                            "Only approved or partially fulfilled "
                            "requests can receive blood."
                        )

                    cur.execute(
                        """
                        SELECT COALESCE(
                            SUM(quantity_issued_ml), 0
                        )
                        FROM blood_issue
                        WHERE request_id = %s
                        """,
                        (request_id,)
                    )
                    already_issued = cur.fetchone()[0]
                    remaining = requested - already_issued

                    if quantity > remaining:
                        raise ValueError(
                            f"Only {remaining} mL remains "
                            "for this request."
                        )

                    # Lock the relevant stock row to prevent
                    # concurrent issues from overspending stock.
                    cur.execute(
                        """
                        SELECT available_quantity_ml
                        FROM blood_stock
                        WHERE blood_group_code = %s
                        FOR UPDATE
                        """,
                        (group,)
                    )
                    stock_row = cur.fetchone()

                    if stock_row is None:
                        raise ValueError(
                            "No stock record exists for this group."
                        )

                    available = stock_row[0]

                    if quantity > available:
                        raise ValueError(
                            f"Insufficient stock. Only "
                            f"{available} mL is available."
                        )

                    # Confirm that the issuing staff member exists.
                    cur.execute(
                        "SELECT 1 FROM staff WHERE staff_id = %s",
                        (staff_id,)
                    )
                    if cur.fetchone() is None:
                        raise ValueError("Staff ID does not exist.")

                    # Both operations commit together or roll back.
                    cur.execute(
                        """
                        INSERT INTO blood_issue (
                            request_id,
                            quantity_issued_ml,
                            staff_id
                        )
                        VALUES (%s, %s, %s)
                        RETURNING issue_id
                        """,
                        (request_id, quantity, staff_id)
                    )
                    issue_id = cur.fetchone()[0]

                    cur.execute(
                        """
                        UPDATE blood_stock
                        SET available_quantity_ml =
                                available_quantity_ml - %s,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE blood_group_code = %s
                        """,
                        (quantity, group)
                    )

                    new_status = (
                        "FULFILLED"
                        if quantity == remaining
                        else "PARTIALLY_FULFILLED"
                    )

                    cur.execute(
                        """
                        UPDATE blood_request
                        SET request_status = %s
                        WHERE request_id = %s
                        """,
                        (new_status, request_id)
                    )

            messagebox.showinfo(
                "Issue Successful",
                f"Issue ID: {issue_id}\n"
                f"Quantity issued: {quantity} mL\n"
                f"Request status: {new_status}"
            )

            self.clear_selection()
            self.load_requests()

        except ValueError as error:
            messagebox.showwarning(
                "Cannot Issue Blood", str(error)
            )
        except Exception as error:
            messagebox.showerror(
                "Database Error",
                f"The issue transaction failed:\n{error}"
            )

    def clear_selection(self):
        self.selected_request_id = None
        self.request_label.config(text="No request selected")
        self.quantity_entry.delete(0, tk.END)

        for item in self.tree.selection():
            self.tree.selection_remove(item)


if __name__ == "__main__":
    root = tk.Tk()
    app = BloodIssueManagement(root)
    root.mainloop()

