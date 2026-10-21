
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config.database import get_connection


REPORTS = {
    "Donor Report": {
        "columns": [
            "Donor ID", "Donor Name", "Date of Birth",
            "Gender", "Blood Group", "Phone", "Email", "Active"
        ],
        "query": """
            SELECT donor_id, full_name, date_of_birth,
                   gender, blood_group_code, phone, email,
                   is_active
            FROM donor
            ORDER BY donor_id
        """
    },

    "Donation Report": {
        "columns": [
            "Donation ID", "Donor Name", "Blood Group",
            "Donation Date", "Quantity (mL)",
            "Screening Status", "Staff Name"
        ],
        "query": """
            SELECT d.donation_id, dn.full_name,
                   d.blood_group_code, d.donation_date,
                   d.quantity_ml, d.screening_status,
                   s.full_name
            FROM donation d
            JOIN donor dn ON dn.donor_id = d.donor_id
            JOIN staff s ON s.staff_id = d.staff_id
            ORDER BY d.donation_date DESC, d.donation_id DESC
        """
    },

    "Blood Stock Report": {
        "columns": [
            "Blood Group", "Description",
            "Available (mL)", "Stock Status", "Last Updated"
        ],
        "query": """
            SELECT bg.blood_group_code, bg.description,
                   bs.available_quantity_ml,
                   CASE
                       WHEN bs.available_quantity_ml = 0
                           THEN 'OUT OF STOCK'
                       ELSE 'AVAILABLE'
                   END,
                   bs.last_updated
            FROM blood_stock bs
            JOIN blood_group bg
              ON bg.blood_group_code = bs.blood_group_code
            ORDER BY bg.blood_group_code
        """
    },

    "Hospital Request Report": {
        "columns": [
            "Request ID", "Hospital", "Blood Group",
            "Requested (mL)", "Issued (mL)",
            "Remaining (mL)", "Status", "Request Date"
        ],
        "query": """
            SELECT br.request_id, h.hospital_name,
                   br.blood_group_code,
                   br.quantity_requested_ml,
                   COALESCE(SUM(bi.quantity_issued_ml), 0)
                       AS issued_ml,
                   br.quantity_requested_ml -
                       COALESCE(SUM(bi.quantity_issued_ml), 0)
                       AS remaining_ml,
                   br.request_status, br.request_date
            FROM blood_request br
            JOIN hospital h
              ON h.hospital_id = br.hospital_id
            LEFT JOIN blood_issue bi
              ON bi.request_id = br.request_id
            GROUP BY br.request_id, h.hospital_name,
                     br.blood_group_code,
                     br.quantity_requested_ml,
                     br.request_status, br.request_date
            ORDER BY br.request_date DESC, br.request_id DESC
        """
    },

    "Blood Issue Report": {
        "columns": [
            "Issue ID", "Request ID", "Hospital",
            "Blood Group", "Quantity (mL)",
            "Issue Date", "Staff Name"
        ],
        "query": """
            SELECT bi.issue_id, br.request_id,
                   h.hospital_name, br.blood_group_code,
                   bi.quantity_issued_ml, bi.issue_date,
                   s.full_name
            FROM blood_issue bi
            JOIN blood_request br
              ON br.request_id = bi.request_id
            JOIN hospital h
              ON h.hospital_id = br.hospital_id
            JOIN staff s
              ON s.staff_id = bi.staff_id
            ORDER BY bi.issue_date DESC, bi.issue_id DESC
        """
    },

    "Summary Report": {
        "columns": ["Metric", "Value"],
        "query": """
            SELECT 'Total Donors',
                   COUNT(*)::TEXT
            FROM donor

            UNION ALL

            SELECT 'Active Donors',
                   COUNT(*)::TEXT
            FROM donor
            WHERE is_active = TRUE

            UNION ALL

            SELECT 'Total Donation Records',
                   COUNT(*)::TEXT
            FROM donation

            UNION ALL

            SELECT 'Approved Donation Quantity (mL)',
                   COALESCE(SUM(quantity_ml), 0)::TEXT
            FROM donation
            WHERE screening_status = 'APPROVED'

            UNION ALL

            SELECT 'Total Available Stock (mL)',
                   COALESCE(SUM(available_quantity_ml), 0)::TEXT
            FROM blood_stock

            UNION ALL

            SELECT 'Pending Requests',
                   COUNT(*)::TEXT
            FROM blood_request
            WHERE request_status = 'PENDING'

            UNION ALL

            SELECT 'Total Blood Issues',
                   COUNT(*)::TEXT
            FROM blood_issue
        """
    }
}


class ReportsManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("Reports and Analytics")
        self.root.geometry("1200x680")
        self.root.configure(bg="#F4F6F9")

        self.current_columns = []
        self.current_rows = []

        self.build_ui()
        self.load_report()

    def build_ui(self):
        header = tk.Frame(self.root, bg="#9F1D25", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text="REPORTS AND ANALYTICS",
            font=("Arial", 20, "bold"),
            bg="#9F1D25",
            fg="white"
        ).pack(pady=14)

        controls = ttk.LabelFrame(
            self.root, text="Select Report", padding=12
        )
        controls.pack(fill="x", padx=15, pady=12)

        ttk.Label(
            controls, text="Report Type:"
        ).pack(side="left", padx=6)

        self.report_combo = ttk.Combobox(
            controls,
            state="readonly",
            values=list(REPORTS.keys()),
            width=28
        )
        self.report_combo.pack(side="left", padx=6)
        self.report_combo.set("Summary Report")

        ttk.Button(
            controls,
            text="Generate Report",
            command=self.load_report
        ).pack(side="left", padx=6)

        ttk.Button(
            controls,
            text="Export CSV",
            command=self.export_csv
        ).pack(side="left", padx=6)

        ttk.Button(
            controls,
            text="Refresh",
            command=self.load_report
        ).pack(side="left", padx=6)

        self.status_label = ttk.Label(
            self.root, text="Select a report to begin."
        )
        self.status_label.pack(anchor="w", padx=18, pady=4)

        table_frame = ttk.Frame(self.root)
        table_frame.pack(
            fill="both", expand=True, padx=15, pady=10
        )

        self.tree = ttk.Treeview(
            table_frame, show="headings"
        )

        vertical_scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        horizontal_scroll = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=vertical_scroll.set,
            xscrollcommand=horizontal_scroll.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

    def load_report(self):
        report_name = self.report_combo.get()

        if report_name not in REPORTS:
            messagebox.showwarning(
                "Select Report", "Choose a report type."
            )
            return

        report = REPORTS[report_name]

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(report["query"])
                    rows = cur.fetchall()

            self.current_columns = report["columns"]
            self.current_rows = rows

            # Rebuild table headings for the chosen report.
            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = [
                f"col_{i}"
                for i in range(len(self.current_columns))
            ]

            for i, heading in enumerate(self.current_columns):
                column_id = f"col_{i}"
                self.tree.heading(column_id, text=heading)
                self.tree.column(
                    column_id,
                    width=150,
                    minwidth=90,
                    stretch=True,
                    anchor="w"
                )

            for row in rows:
                formatted_row = [
                    "" if value is None else str(value)
                    for value in row
                ]
                self.tree.insert(
                    "", "end", values=formatted_row
                )

            self.status_label.config(
                text=f"{report_name}: {len(rows)} record(s) found."
            )

        except Exception as error:
            messagebox.showerror(
                "Report Error",
                f"Could not generate the report:\n{error}"
            )

    def export_csv(self):
        if not self.current_columns:
            messagebox.showwarning(
                "No Report", "Generate a report before exporting."
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )

        if not path:
            return

        try:
            with open(
                path, "w", newline="", encoding="utf-8-sig"
            ) as file:
                writer = csv.writer(file)
                writer.writerow(self.current_columns)
                writer.writerows(self.current_rows)

            messagebox.showinfo(
                "Export Successful",
                f"Report saved to:\n{path}"
            )

        except Exception as error:
            messagebox.showerror(
                "Export Error", str(error)
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = ReportsManagement(root)
    root.mainloop()
