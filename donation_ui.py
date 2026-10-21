import tkinter as tk
from tkinter import ttk, messagebox

from config.database import get_connection


class DonationManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Donation Management")
        self.root.geometry("1250x800")
        self.root.configure(bg="#F4F6F9")

        self.build_ui()
        self.load_donations()

    def build_ui(self):
        # Readable fonts
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 12), rowheight=32)
        style.configure("Treeview.Heading", font=("Arial", 12, "bold"))
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TButton", font=("Arial", 12))
        style.configure("TEntry", font=("Arial", 12))
        style.configure("TLabelframe.Label", font=("Arial", 12, "bold"))

        # Header
        header = tk.Frame(self.root, bg="#9F1D25", height=65)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="DONATION MANAGEMENT",
            font=("Arial", 22, "bold"),
            bg="#9F1D25",
            fg="white",
        ).pack(pady=14)

        # Donation form
        form = ttk.LabelFrame(
            self.root,
            text="Record New Donation",
            padding=14,
        )
        form.pack(fill="x", padx=15, pady=10)

        ttk.Label(form, text="Donor ID:").grid(
            row=0, column=0, padx=8, pady=8, sticky="w"
        )
        self.donor_id = ttk.Entry(form, width=16, font=("Arial", 12))
        self.donor_id.grid(
            row=0, column=1, padx=8, pady=8, sticky="ew", ipady=3
        )

        ttk.Label(form, text="Quantity (mL):").grid(
            row=0, column=2, padx=8, pady=8, sticky="w"
        )
        self.quantity = ttk.Entry(form, width=16, font=("Arial", 12))
        self.quantity.grid(
            row=0, column=3, padx=8, pady=8, sticky="ew", ipady=3
        )

        ttk.Label(form, text="Staff ID:").grid(
            row=0, column=4, padx=8, pady=8, sticky="w"
        )
        self.staff_id = ttk.Entry(form, width=16, font=("Arial", 12))
        self.staff_id.grid(
            row=0, column=5, padx=8, pady=8, sticky="ew", ipady=3
        )

        for column in (1, 3, 5):
            form.columnconfigure(column, weight=1)

        ttk.Button(
            form,
            text="Record Donation",
            command=self.record_donation,
        ).grid(row=1, column=1, columnspan=2, padx=8, pady=10, ipady=3)

        ttk.Button(
            form,
            text="Clear",
            command=self.clear_form,
        ).grid(row=1, column=3, padx=8, pady=10, ipady=3)

        ttk.Label(
            form,
            text="New donations remain PENDING until approved.",
        ).grid(row=1, column=4, columnspan=2, padx=8, pady=10, sticky="w")

        # Action buttons
        actions = ttk.Frame(self.root)
        actions.pack(fill="x", padx=15, pady=5)

        ttk.Button(
            actions,
            text="Approve Selected",
            command=self.approve_donation,
        ).pack(side="left", padx=5, ipady=3)

        ttk.Button(
            actions,
            text="Reject Selected",
            command=self.reject_donation,
        ).pack(side="left", padx=5, ipady=3)

        ttk.Button(
            actions,
            text="Refresh",
            command=self.load_donations,
        ).pack(side="left", padx=5, ipady=3)

        # Donation table
        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(8, 12),
        )

        columns = (
            "id",
            "donor",
            "date",
            "group",
            "quantity",
            "status",
            "staff",
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        headings = {
            "id": "Donation ID",
            "donor": "Donor Name",
            "date": "Donation Date",
            "group": "Blood Group",
            "quantity": "Quantity (mL)",
            "status": "Screening Status",
            "staff": "Staff ID",
        }

        widths = {
            "id": 110,
            "donor": 230,
            "date": 170,
            "group": 140,
            "quantity": 170,
            "status": 210,
            "staff": 130,
        }

        for column in columns:
            self.tree.heading(column, text=headings[column])
            self.tree.column(
                column,
                width=widths[column],
                minwidth=90,
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

    def record_donation(self):
        try:
            donor_text = self.donor_id.get().strip()
            quantity_text = self.quantity.get().strip()
            staff_text = self.staff_id.get().strip()

            if not donor_text or not quantity_text or not staff_text:
                raise ValueError(
                    "Enter Donor ID, Quantity, and Staff ID."
                )

            try:
                donor_id = int(donor_text)
                quantity = int(quantity_text)
                staff_id = int(staff_text)
            except ValueError:
                raise ValueError(
                    "Donor ID, Quantity, and Staff ID must be whole numbers."
                )

            if donor_id <= 0 or staff_id <= 0:
                raise ValueError(
                    "Donor ID and Staff ID must be positive numbers."
                )

            if quantity <= 0:
                raise ValueError("Quantity must be greater than zero.")

            with get_connection() as conn:
                with conn.cursor() as cur:
                    # Verify that the donor exists and is active.
                    cur.execute(
                        """
                        SELECT blood_group_code, is_active
                        FROM donor
                        WHERE donor_id = %s
                        """,
                        (donor_id,),
                    )
                    donor = cur.fetchone()

                    if donor is None:
                        raise ValueError("Donor does not exist.")

                    blood_group, is_active = donor

                    if not is_active:
                        raise ValueError("This donor is inactive.")

                    # Verify that the staff ID exists.
                    cur.execute(
                        """
                        SELECT 1
                        FROM staff
                        WHERE staff_id = %s
                        """,
                        (staff_id,),
                    )

                    if cur.fetchone() is None:
                        raise ValueError("Staff ID does not exist.")

                    # New donations remain pending until approved.
                    cur.execute(
                        """
                        INSERT INTO donation (
                            donor_id,
                            donation_date,
                            blood_group_code,
                            quantity_ml,
                            screening_status,
                            staff_id
                        )
                        VALUES (
                            %s, CURRENT_DATE, %s, %s, 'PENDING', %s
                        )
                        RETURNING donation_id
                        """,
                        (donor_id, blood_group, quantity, staff_id),
                    )

                    donation_id = cur.fetchone()[0]

            messagebox.showinfo(
                "Donation Recorded",
                f"Donation recorded as PENDING.\n"
                f"Donation ID: {donation_id}\n"
                "Blood stock has not been increased yet.",
                parent=self.root,
            )

            self.clear_form()
            self.load_donations()

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

    def get_selected_id(self):
        selection = self.tree.selection()

        if not selection:
            messagebox.showwarning(
                "Select Donation",
                "Select a donation from the table first.",
                parent=self.root,
            )
            return None

        values = self.tree.item(selection[0], "values")
        return int(values[0])

    def approve_donation(self):
        donation_id = self.get_selected_id()

        if donation_id is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm Approval",
            "Approve this pending donation and add its quantity "
            "to blood stock?",
            parent=self.root,
        )

        if not confirmed:
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            blood_group_code,
                            quantity_ml,
                            screening_status
                        FROM donation
                        WHERE donation_id = %s
                        FOR UPDATE
                        """,
                        (donation_id,),
                    )

                    donation = cur.fetchone()

                    if donation is None:
                        raise ValueError("Donation not found.")

                    group, quantity, status = donation

                    if status != "PENDING":
                        raise ValueError(
                            "Only pending donations can be approved."
                        )

                    # Increase stock within the same transaction.
                    cur.execute(
                        """
                        UPDATE blood_stock
                        SET available_quantity_ml =
                                available_quantity_ml + %s,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE blood_group_code = %s
                        """,
                        (quantity, group),
                    )

                    if cur.rowcount != 1:
                        raise ValueError(
                            "Blood stock record not found for this blood group."
                        )

                    cur.execute(
                        """
                        UPDATE donation
                        SET screening_status = 'APPROVED'
                        WHERE donation_id = %s
                          AND screening_status = 'PENDING'
                        """,
                        (donation_id,),
                    )

                    if cur.rowcount != 1:
                        raise ValueError(
                            "Donation status changed unexpectedly."
                        )

            messagebox.showinfo(
                "Success",
                "Donation approved and blood stock updated.",
                parent=self.root,
            )

            self.load_donations()

        except ValueError as error:
            messagebox.showwarning(
                "Approval Failed",
                str(error),
                parent=self.root,
            )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=self.root,
            )

    def reject_donation(self):
        donation_id = self.get_selected_id()

        if donation_id is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm Rejection",
            "Reject this pending donation? Blood stock will remain unchanged.",
            parent=self.root,
        )

        if not confirmed:
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE donation
                        SET screening_status = 'REJECTED'
                        WHERE donation_id = %s
                          AND screening_status = 'PENDING'
                        """,
                        (donation_id,),
                    )

                    if cur.rowcount != 1:
                        raise ValueError(
                            "Only pending donations can be rejected."
                        )

            messagebox.showinfo(
                "Success",
                "Donation rejected. Blood stock was not changed.",
                parent=self.root,
            )

            self.load_donations()

        except ValueError as error:
            messagebox.showwarning(
                "Rejection Failed",
                str(error),
                parent=self.root,
            )

        except Exception as error:
            messagebox.showerror(
                "Database Error",
                str(error),
                parent=self.root,
            )

    def load_donations(self):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            d.donation_id,
                            dr.full_name,
                            d.donation_date,
                            d.blood_group_code,
                            d.quantity_ml,
                            d.screening_status,
                            d.staff_id
                        FROM donation d
                        JOIN donor dr
                          ON dr.donor_id = d.donor_id
                        ORDER BY d.donation_id DESC
                        """
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

    def clear_form(self):
        self.donor_id.delete(0, tk.END)
        self.quantity.delete(0, tk.END)

        # Keep the Staff ID populated for the current staff member.


if __name__ == "__main__":
    root = tk.Tk()
    app = DonationManagement(root)
    root.mainloop()