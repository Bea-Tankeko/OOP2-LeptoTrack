import sys
import sqlite3
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QLineEdit, QFrame, QHeaderView, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QAbstractItemView, QDateEdit, QScrollArea, QLayout
)
from PyQt6.QtCore import Qt, QRectF, QDate
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QIcon, QPixmap, QPainterPath


def load_stylesheet():
    stylesheet_path = Path(__file__).resolve().parent / "LeptoTrack.qss"
    try:
        return stylesheet_path.read_text(encoding="utf-8")
    except OSError:
        return ""




def draw_leptotrack_icon(painter, rect):
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    size = min(rect.width(), rect.height())
    scale = size / 512
    painter.translate(rect.x() + (rect.width() - size) / 2,
                      rect.y() + (rect.height() - size) / 2)
    painter.scale(scale, scale)

    painter.setPen(QPen(QColor("#18BEB4"), 14))
    painter.setBrush(QColor("#0F1F31"))
    painter.drawRoundedRect(QRectF(8, 8, 496, 496), 100, 100)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("#EBF6FA"))
    painter.drawRoundedRect(QRectF(120, 175, 270, 235), 32, 32)
    painter.drawRect(QRectF(190, 120, 130, 70))

    painter.setBrush(QColor("#1CCABE"))
    painter.drawRoundedRect(QRectF(218, 78, 76, 94), 16, 16)
    painter.drawRoundedRect(QRectF(192, 100, 128, 46), 14, 14)

    painter.setBrush(QColor("#0F1F31"))
    for x in (150, 224, 298):
        for y in (220, 292):
            painter.drawRoundedRect(QRectF(x, y, 28, 28), 6, 6)
    painter.drawRoundedRect(QRectF(236, 330, 56, 80), 12, 12)

    painter.setPen(QPen(QColor("#1CCABE"), 15, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(305, 370)
    path.lineTo(330, 370)
    path.lineTo(350, 330)
    path.lineTo(370, 395)
    path.lineTo(392, 285)
    path.lineTo(415, 345)
    path.lineTo(465, 250)
    painter.drawPath(path)

    painter.restore()


def create_app_icon():
    pixmap = QPixmap(512, 512)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    draw_leptotrack_icon(painter, QRectF(0, 0, 512, 512))
    painter.end()
    return QIcon(pixmap)


class LeptoLogo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcomeLogo")
        self.setFixedSize(112, 112)

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_leptotrack_icon(painter, QRectF(0, 0, self.width(), self.height()))
        painter.end()


DB_PATH = Path(__file__).resolve().parent / "leptotrack.db"
STYLE_PATH = Path(__file__).resolve().with_name("LeptoTrack.qss")


def init_db():
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS monitoring_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_date TEXT NOT NULL UNIQUE,
                general_capacity INTEGER NOT NULL DEFAULT 0,
                general_admitted INTEGER NOT NULL DEFAULT 0,
                general_released INTEGER NOT NULL DEFAULT 0,
                general_deaths INTEGER NOT NULL DEFAULT 0,
                icu_capacity INTEGER NOT NULL DEFAULT 0,
                icu_admitted INTEGER NOT NULL DEFAULT 0,
                icu_released INTEGER NOT NULL DEFAULT 0,
                icu_deaths INTEGER NOT NULL DEFAULT 0,
                new_cases_reported INTEGER NOT NULL DEFAULT 0,
                total_cases_recorded INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL
            )
        """)

        columns = {
            row[1] for row in
            conn.execute("PRAGMA table_info(monitoring_records)")
        }

        additions = {
            "general_capacity": "INTEGER NOT NULL DEFAULT 0",
            "general_admitted": "INTEGER NOT NULL DEFAULT 0",
            "general_released": "INTEGER NOT NULL DEFAULT 0",
            "general_deaths": "INTEGER NOT NULL DEFAULT 0",
            "icu_capacity": "INTEGER NOT NULL DEFAULT 0",
            "icu_admitted": "INTEGER NOT NULL DEFAULT 0",
            "icu_released": "INTEGER NOT NULL DEFAULT 0",
            "icu_deaths": "INTEGER NOT NULL DEFAULT 0",
            "new_cases_reported": "INTEGER NOT NULL DEFAULT 0",
            "total_cases_recorded": "INTEGER NOT NULL DEFAULT 0"
        }

        for name, definition in additions.items():
            if name not in columns:
                conn.execute(
                    f"ALTER TABLE monitoring_records ADD COLUMN {name} {definition}"
                )

        if "general_beds_available" in columns:
            conn.execute("""
                UPDATE monitoring_records
                SET general_capacity = general_beds_available + general_admitted
                WHERE general_capacity = 0
            """)

        if "icu_beds_available" in columns:
            conn.execute("""
                UPDATE monitoring_records
                SET icu_capacity = icu_beds_available + icu_admitted
                WHERE icu_capacity = 0
            """)

        if "deaths" in columns:
            conn.execute("""
                UPDATE monitoring_records
                SET general_deaths = deaths
                WHERE general_deaths = 0 AND icu_deaths = 0
            """)

        if "released_patients" in columns:
            conn.execute("""
                UPDATE monitoring_records
                SET general_released = released_patients
                WHERE general_released = 0 AND icu_released = 0
            """)

        if (
            "new_cases_reported" not in columns
            and "total_cases_recorded" in columns
        ):
            rows = conn.execute("""
                SELECT id, total_cases_recorded
                FROM monitoring_records
                ORDER BY report_date ASC, id ASC
            """).fetchall()

            previous_total = 0

            for record_id, old_total in rows:
                current_total = max(0, old_total or 0)
                daily_cases = max(0, current_total - previous_total)

                conn.execute("""
                    UPDATE monitoring_records
                    SET new_cases_reported = ?
                    WHERE id = ?
                """, (daily_cases, record_id))

                previous_total = current_total


def get_setting(key, default=""):
    with sqlite3.connect(str(DB_PATH)) as conn:
        row = conn.execute(
            "SELECT setting_value FROM app_settings WHERE setting_key=?",
            (key,)
        ).fetchone()
    return row[0] if row else default


def save_setting(key, value):
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("""
            INSERT INTO app_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key)
            DO UPDATE SET setting_value=excluded.setting_value
        """, (key, value))


def reset_all_data():
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute("DELETE FROM monitoring_records")
        conn.execute("DELETE FROM app_settings")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='monitoring_records'")


def load_records():
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM monitoring_records ORDER BY report_date ASC, id ASC"
        ).fetchall()

    records = []
    cumulative_cases = 0

    for row in rows:
        record = dict(row)

        cumulative_cases += record["new_cases_reported"]
        record["total_cases_recorded"] = cumulative_cases

        record["general_occupied"] = max(
            0,
            record["general_admitted"]
            - record["general_released"]
            - record["general_deaths"]
        )

        record["icu_occupied"] = max(
            0,
            record["icu_admitted"]
            - record["icu_released"]
            - record["icu_deaths"]
        )

        record["general_beds_available"] = max(
            0, record["general_capacity"] - record["general_occupied"]
        )

        record["icu_beds_available"] = max(
            0, record["icu_capacity"] - record["icu_occupied"]
        )

        record["deaths"] = (
            record["general_deaths"] + record["icu_deaths"]
        )

        record["released_patients"] = (
            record["general_released"] + record["icu_released"]
        )

        record["total_admitted"] = (
            record["general_admitted"] + record["icu_admitted"]
        )

        records.append(record)

    return sorted(
        records,
        key=lambda item: (item["report_date"], item["id"]),
        reverse=True
    )


def capacity_warning(record):
    warnings = []

    if record["general_beds_available"] == 0:
        warnings.append("GENERAL BEDS FULL")

    if record["icu_beds_available"] == 0:
        warnings.append("ICU CAPACITY FULL")

    return " | ".join(warnings) if warnings else "NORMAL"


def save_record(data, record_id=None):
    values = (
        data["report_date"],
        data["general_capacity"],
        data["general_admitted"],
        data["general_released"],
        data["general_deaths"],
        data["icu_capacity"],
        data["icu_admitted"],
        data["icu_released"],
        data["icu_deaths"],
        data["new_cases_reported"],
        datetime.now().strftime("%Y-%m-%d %H:%M")
    )

    with sqlite3.connect(str(DB_PATH)) as conn:
        if record_id is None:
            conn.execute("""
                INSERT INTO monitoring_records (
                    report_date, general_capacity, general_admitted,
                    general_released, general_deaths, icu_capacity,
                    icu_admitted, icu_released, icu_deaths,
                    new_cases_reported, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)

        else:
            conn.execute("""
                UPDATE monitoring_records SET
                    report_date=?,
                    general_capacity=?,
                    general_admitted=?,
                    general_released=?,
                    general_deaths=?,
                    icu_capacity=?,
                    icu_admitted=?,
                    icu_released=?,
                    icu_deaths=?,
                    new_cases_reported=?,
                    last_updated=?
                WHERE id=?
            """, values + (record_id,))


def delete_record(record_id):
    with sqlite3.connect(str(DB_PATH)) as conn:
        conn.execute(
            "DELETE FROM monitoring_records WHERE id=?",
            (record_id,)
        )


class StatCard(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setObjectName("statCard")

        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        layout.addWidget(title_label)

        self.value = QLabel("—")
        self.value.setObjectName("statValue")
        layout.addWidget(self.value)


class CapacityDonut(QWidget):
    def __init__(self, center_label):
        super().__init__()

        self.setMinimumSize(170, 170)

        self.value = 0
        self.total = 0
        self.center_label = center_label
        self.show_count_only = False
        self.alert = False

    def set_alert(self, alert):
        self.alert = alert
        self.update()

    def set_count(self, value):
        self.value = max(0, value)
        self.total = self.value
        self.show_count_only = True
        self.update()

    def set_ratio(self, value, total):
        self.value = max(0, value)
        self.total = max(0, total)
        self.show_count_only = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height()) - 30

        rect = QRectF(
            (self.width() - side) / 2,
            (self.height() - side) / 2,
            side,
            side
        )

        painter.setPen(QPen(QColor("#2B3746"), 17))
        painter.drawArc(rect, 0, 360 * 16)

        ring_color = (
            QColor("#EF4444")
            if self.alert
            else QColor("#2DD4BF")
        )

        if self.show_count_only:
            if self.value > 0:
                painter.setPen(QPen(ring_color, 17))
                painter.drawArc(rect, 90 * 16, -360 * 16)

            center = str(self.value)

        else:
            if self.total > 0:
                ratio = min(1, self.value / self.total)

                painter.setPen(QPen(ring_color, 17))
                painter.drawArc(
                    rect,
                    90 * 16,
                    -int(ratio * 360 * 16)
                )

            center = (
                f"{self.value}\n/ {self.total}"
                if self.total
                else "0\n/ 0"
            )

        painter.setPen(QColor("#17324D"))
        painter.setFont(
            QFont("Segoe UI", 15, QFont.Weight.Bold)
        )

        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            center
        )


class MonitoringRecordDialog(QDialog):
    def __init__(self, parent=None, record=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Add Monitoring Record"
            if record is None
            else "Edit Monitoring Record"
        )

        self.setMinimumWidth(490)

        layout = QFormLayout(self)

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        self.date_input.setDate(QDate.currentDate())

        self.general_capacity_input = QLineEdit("0")
        self.general_admitted_input = QLineEdit("0")
        self.general_released_input = QLineEdit("0")
        self.general_deaths_input = QLineEdit("0")

        self.icu_capacity_input = QLineEdit("0")
        self.icu_admitted_input = QLineEdit("0")
        self.icu_released_input = QLineEdit("0")
        self.icu_deaths_input = QLineEdit("0")

        self.new_cases_input = QLineEdit("0")

        layout.addRow("Reporting date:", self.date_input)

        layout.addRow(QLabel("GENERAL WARD"), QLabel(""))

        layout.addRow(
            "Total general bed capacity:",
            self.general_capacity_input
        )

        layout.addRow(
            "Cumulative general-ward admissions:",
            self.general_admitted_input
        )

        layout.addRow(
            "Cumulative general-ward releases:",
            self.general_released_input
        )

        layout.addRow(
            "Cumulative general-ward deaths:",
            self.general_deaths_input
        )

        layout.addRow(QLabel("INTENSIVE CARE UNIT"), QLabel(""))

        layout.addRow(
            "Total ICU bed capacity:",
            self.icu_capacity_input
        )

        layout.addRow(
            "Cumulative ICU admissions:",
            self.icu_admitted_input
        )

        layout.addRow(
            "Cumulative ICU releases:",
            self.icu_released_input
        )

        layout.addRow(
            "Cumulative ICU deaths:",
            self.icu_deaths_input
        )

        layout.addRow(
            "New cases reported today:",
            self.new_cases_input
        )

        note = QLabel(
            "Enter cumulative admissions, releases, and deaths as of "
            "the reporting date. Enter only the new leptospirosis cases "
            "reported on this date. Total cumulative cases are calculated "
            "automatically."
        )

        note.setWordWrap(True)
        note.setObjectName("mutedText")
        layout.addRow(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )

        buttons.button(
            QDialogButtonBox.StandardButton.Save
        ).setObjectName("primaryButton")

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

        if record:
            self.date_input.setDate(
                QDate.fromString(
                    record["report_date"],
                    "yyyy-MM-dd"
                )
            )

            self.general_capacity_input.setText(
                str(record["general_capacity"])
            )

            self.general_admitted_input.setText(
                str(record["general_admitted"])
            )

            self.general_released_input.setText(
                str(record["general_released"])
            )

            self.general_deaths_input.setText(
                str(record["general_deaths"])
            )

            self.icu_capacity_input.setText(
                str(record["icu_capacity"])
            )

            self.icu_admitted_input.setText(
                str(record["icu_admitted"])
            )

            self.icu_released_input.setText(
                str(record["icu_released"])
            )

            self.icu_deaths_input.setText(
                str(record["icu_deaths"])
            )

            self.new_cases_input.setText(
                str(record["new_cases_reported"])
            )

    def get_data(self):
        def number(field):
            value_text = field.text().strip()

            if not value_text:
                raise ValueError(
                    "All numeric fields are required."
                )

            try:
                value = int(value_text)
            except ValueError:
                raise ValueError(
                    "Enter whole numbers only."
                )

            if value < 0:
                raise ValueError(
                    "Values cannot be negative."
                )

            return value

        general_capacity = number(
            self.general_capacity_input
        )

        general_admitted = number(
            self.general_admitted_input
        )

        general_released = number(
            self.general_released_input
        )

        general_deaths = number(
            self.general_deaths_input
        )

        icu_capacity = number(
            self.icu_capacity_input
        )

        icu_admitted = number(
            self.icu_admitted_input
        )

        icu_released = number(
            self.icu_released_input
        )

        icu_deaths = number(
            self.icu_deaths_input
        )

        new_cases = number(
            self.new_cases_input
        )

        general_occupied = (
            general_admitted
            - general_released
            - general_deaths
        )

        icu_occupied = (
            icu_admitted
            - icu_released
            - icu_deaths
        )

        if general_released + general_deaths > general_admitted:
            raise ValueError(
                "General-ward releases and deaths cannot exceed "
                "cumulative general admissions."
            )

        if icu_released + icu_deaths > icu_admitted:
            raise ValueError(
                "ICU releases and deaths cannot exceed "
                "cumulative ICU admissions."
            )

        if general_occupied > general_capacity:
            raise ValueError(
                "Current general-ward occupancy cannot exceed "
                "general bed capacity."
            )

        if icu_occupied > icu_capacity:
            raise ValueError(
                "Current ICU occupancy cannot exceed ICU bed capacity."
            )

        return {
            "report_date": self.date_input.date().toString("yyyy-MM-dd"),
            "general_capacity": general_capacity,
            "general_admitted": general_admitted,
            "general_released": general_released,
            "general_deaths": general_deaths,
            "icu_capacity": icu_capacity,
            "icu_admitted": icu_admitted,
            "icu_released": icu_released,
            "icu_deaths": icu_deaths,
            "new_cases_reported": new_cases
        }


class LeptoTrack(QMainWindow):
    def __init__(self, hospital_name=""):
        super().__init__()

        self.hospital_name = hospital_name.strip() or "Hospital"
        self.setWindowTitle(
            f"LeptoTrack | {self.hospital_name}"
        )

        self.resize(1250, 850)
        self.setMinimumSize(800, 600)

        self.records = []

        scroll_area = QScrollArea()
        scroll_area.setObjectName("dashboardScrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        root = QWidget()
        scroll_area.setWidget(root)

        self.setCentralWidget(scroll_area)

        main = QVBoxLayout(root)
        main.setSpacing(12)
        main.setContentsMargins(16, 16, 16, 16)

        main.setSizeConstraint(
            QLayout.SizeConstraint.SetMinimumSize
        )

        header = QHBoxLayout()
        branding = QVBoxLayout()

        title = QLabel("LeptoTrack")
        title.setObjectName("mainTitle")
        branding.addWidget(title)

        subtitle = QLabel("Single-Hospital Leptospirosis Monitoring")

        subtitle.setObjectName("subtitle")
        branding.addWidget(subtitle)

        header.addLayout(branding)
        header.addStretch()

        badge = QLabel("HOSPITAL MONITORING RECORDS")
        badge.setObjectName("badge")
        header.addWidget(badge)

        main.addLayout(header)

        stats = QGridLayout()

        self.cases_card = StatCard("Total Cases Recorded")
        self.general_card = StatCard("General Beds Available")
        self.icu_card = StatCard("ICU Beds Available")
        self.admitted_card = StatCard("Currently Admitted Patients")

        for index, card in enumerate((
            self.cases_card,
            self.general_card,
            self.icu_card,
            self.admitted_card
        )):
            stats.addWidget(card, 0, index)

        main.addLayout(stats)

        self.warning_banner = QLabel()
        self.warning_banner.setObjectName("warningBanner")
        self.warning_banner.setWordWrap(True)

        self.warning_banner.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.warning_banner.hide()
        main.addWidget(self.warning_banner)

        charts = QGridLayout()

        self.general_donut = CapacityDonut("General Beds")
        self.icu_donut = CapacityDonut("ICU Beds")
        self.cases_donut = CapacityDonut("Recorded Cases")
        self.admitted_donut = CapacityDonut("Currently Admitted")
        self.deaths_donut = CapacityDonut("Deaths")
        self.released_donut = CapacityDonut("Released")

        donut_items = [
            (
                "General Bed Availability",
                self.general_donut,
                "Available general beds compared with total capacity"
            ),
            (
                "ICU Bed Availability",
                self.icu_donut,
                "Available ICU beds compared with total capacity"
            ),
            (
                "Total Cases Recorded",
                self.cases_donut,
                "Cumulative reported cases"
            ),
            (
                "Currently Admitted Patients",
                self.admitted_donut,
                "Current general-ward and ICU occupancy"
            ),
            (
                "Reported Deaths",
                self.deaths_donut,
                "Cumulative deaths compared with total cases"
            ),
            (
                "Released Patients",
                self.released_donut,
                "Cumulative releases compared with total cases"
            )
        ]

        for index, (heading, donut, description) in enumerate(donut_items):
            panel = QFrame()
            panel.setObjectName("panel")

            box = QVBoxLayout(panel)

            label = QLabel(heading)
            label.setObjectName("sectionTitle")
            box.addWidget(label)

            box.addWidget(
                donut,
                alignment=Qt.AlignmentFlag.AlignCenter
            )

            detail = QLabel(description)
            detail.setObjectName("mutedText")

            detail.setAlignment(
                Qt.AlignmentFlag.AlignCenter
            )

            detail.setWordWrap(True)
            box.addWidget(detail)

            charts.addWidget(
                panel,
                index // 3,
                index % 3
            )

        main.addLayout(charts)

        section = QLabel("Hospital Monitoring Records")
        section.setObjectName("sectionTitle")
        main.addWidget(section)

        toolbar = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search by reporting date..."
        )

        self.search_input.textChanged.connect(
            self.populate_table
        )

        toolbar.addWidget(self.search_input)
        main.addLayout(toolbar)

        buttons = QHBoxLayout()

        add_button = QPushButton("Add Monitoring Record")
        add_button.setObjectName("primaryButton")
        add_button.clicked.connect(self.add_record)
        buttons.addWidget(add_button)

        edit_button = QPushButton("Edit Selected")
        edit_button.clicked.connect(self.edit_record)
        buttons.addWidget(edit_button)

        delete_button = QPushButton("Delete Selected")
        delete_button.setProperty("role", "delete")
        delete_button.clicked.connect(self.remove_record)
        buttons.addWidget(delete_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.setProperty("role", "refresh")
        refresh_button.clicked.connect(self.refresh)
        buttons.addWidget(refresh_button)

        reset_button = QPushButton("RESET ALL")
        reset_button.setProperty("role", "delete")
        reset_button.clicked.connect(self.reset_all)
        buttons.addWidget(reset_button)

        buttons.addStretch()
        main.addLayout(buttons)

        self.table = QTableWidget(0, 19)

        self.table.setHorizontalHeaderLabels([
            "Record ID",
            "Reporting Date",
            "General Capacity",
            "General Admitted",
            "General Released",
            "General Deaths",
            "General Occupied",
            "General Available",
            "ICU Capacity",
            "ICU Admitted",
            "ICU Released",
            "ICU Deaths",
            "ICU Occupied",
            "ICU Available",
            "New Cases",
            "Total Cumulative Cases",
            "Total Deaths",
            "Total Released",
            "Capacity Warning"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )

        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        self.table.itemSelectionChanged.connect(
            self.update_dashboard
        )

        self.table.setMinimumHeight(280)
        self.table.setMaximumHeight(360)

        self.table.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        main.addWidget(self.table)

        # Load the external stylesheet.
        self.setStyleSheet(load_stylesheet())

        self.refresh()

    def reset_all(self):
        answer = QMessageBox.warning(
            self,
            "Reset All Data",
            "This will permanently delete ALL monitoring records and the saved hospital name. "
            "The application will return to the hospital setup screen.\n\n"
            "This action cannot be undone. Continue?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        reset_all_data()
        QMessageBox.information(
            self,
            "Reset Complete",
            "All saved monitoring records and the hospital name have been reset."
        )

        self.welcome_page = WelcomePage()
        self.welcome_page.show()
        self.close()

    def refresh(self):
        self.records = load_records()
        self.populate_table()
        self.update_dashboard()

    def populate_table(self):
        query = self.search_input.text().strip().lower()

        self.table.setRowCount(0)

        for record in self.records:
            if query and query not in record["report_date"].lower():
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [
                record["id"],
                record["report_date"],
                record["general_capacity"],
                record["general_admitted"],
                record["general_released"],
                record["general_deaths"],
                record["general_occupied"],
                record["general_beds_available"],
                record["icu_capacity"],
                record["icu_admitted"],
                record["icu_released"],
                record["icu_deaths"],
                record["icu_occupied"],
                record["icu_beds_available"],
                record["new_cases_reported"],
                record["total_cases_recorded"],
                record["deaths"],
                record["released_patients"],
                capacity_warning(record)
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))

                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )

                if column == 18 and value != "NORMAL":
                    item.setForeground(QColor("#FFFFFF"))
                    item.setBackground(QColor("#B91C1C"))

                    item.setFont(
                        QFont("Segoe UI", 9, QFont.Weight.Bold)
                    )

                self.table.setItem(row, column, item)

    def selected_record(self):
        row = self.table.currentRow()

        if row < 0:
            return None

        record_id = int(
            self.table.item(row, 0).text()
        )

        return next(
            (
                record for record in self.records
                if record["id"] == record_id
            ),
            None
        )

    def update_dashboard(self):
        record = self.selected_record()

        if record is None and self.records:
            record = self.records[0]

        if not record:
            for card in (
                self.cases_card,
                self.general_card,
                self.icu_card,
                self.admitted_card
            ):
                card.value.setText("0")

            for donut in (
                self.general_donut,
                self.icu_donut,
                self.cases_donut,
                self.admitted_donut,
                self.deaths_donut,
                self.released_donut
            ):
                donut.set_alert(False)
                donut.set_count(0)

            self.warning_banner.hide()
            return

        general_available = record["general_beds_available"]
        icu_available = record["icu_beds_available"]

        cases = record["total_cases_recorded"]

        occupied = (
            record["general_occupied"]
            + record["icu_occupied"]
        )

        deaths = record["deaths"]
        released = record["released_patients"]

        self.cases_card.value.setText(str(cases))
        self.general_card.value.setText(str(general_available))
        self.icu_card.value.setText(str(icu_available))
        self.admitted_card.value.setText(str(occupied))

        self.general_donut.set_ratio(
            general_available,
            record["general_capacity"]
        )

        self.general_donut.set_alert(
            general_available == 0
        )

        self.icu_donut.set_ratio(
            icu_available,
            record["icu_capacity"]
        )

        self.icu_donut.set_alert(
            icu_available == 0
        )

        self.cases_donut.set_count(cases)

        self.admitted_donut.set_ratio(
            occupied,
            cases
        )

        self.deaths_donut.set_ratio(
            deaths,
            cases
        )

        self.released_donut.set_ratio(
            released,
            cases
        )

        warning = capacity_warning(record)

        if warning == "NORMAL":
            self.warning_banner.hide()

        else:
            self.warning_banner.setText(
                "⚠ CAPACITY WARNING: "
                + warning.replace(" | ", " AND ")
                + " — No beds are currently available."
            )

            self.warning_banner.show()

    def add_record(self):
        self.open_record_dialog()

    def edit_record(self):
        record = self.selected_record()

        if not record:
            QMessageBox.information(
                self,
                "Edit Record",
                "Select a monitoring record first."
            )
            return

        self.open_record_dialog(record)

    def open_record_dialog(self, record=None):
        dialog = MonitoringRecordDialog(self, record)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            data = dialog.get_data()

            save_record(
                data,
                record["id"] if record else None
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Record",
                str(error) or "Enter valid whole numbers."
            )
            return

        except sqlite3.IntegrityError:
            QMessageBox.warning(
                self,
                "Duplicate Date",
                "A record for this reporting date already exists. "
                "Edit that record instead."
            )
            return

        self.refresh()

    def remove_record(self):
        record = self.selected_record()

        if not record:
            QMessageBox.information(
                self,
                "Delete Record",
                "Select a monitoring record first."
            )
            return

        answer = QMessageBox.question(
            self,
            "Delete Record",
            f"Delete the record for {record['report_date']}?",
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.No
        )

        if answer == QMessageBox.StandardButton.Yes:
            delete_record(record["id"])
            self.refresh()



class WelcomePage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LeptoTrack | Welcome")
        self.setMinimumSize(760, 520)
        self.resize(950, 620)

        page = QWidget()
        page.setObjectName("welcomePage")
        self.setCentralWidget(page)

        layout = QVBoxLayout(page)
        layout.setContentsMargins(50, 35, 50, 35)
        layout.setSpacing(18)
        layout.addStretch()

        logo = LeptoLogo()
        layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)

        hospital_label = QLabel("Enter Hospital Name:")
        hospital_label.setObjectName("hospitalName")
        hospital_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hospital_label)

        self.hospital_input = QLineEdit()
        self.hospital_input.setPlaceholderText("Type hospital name here...")
        self.hospital_input.setMinimumWidth(320)
        self.hospital_input.setMaximumWidth(500)
        self.hospital_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.hospital_input, alignment=Qt.AlignmentFlag.AlignCenter)

        app_title = QLabel("LeptoTrack")
        app_title.setObjectName("welcomeTitle")
        app_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(app_title)

        subtitle = QLabel("Single-Hospital Leptospirosis Monitoring System")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        description = QLabel(
            "Monitor hospital beds, patient records, and reported cases "
            "in one simple dashboard."
        )
        description.setObjectName("welcomeDescription")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addSpacing(12)

        open_button = QPushButton("Open Monitoring Dashboard")
        open_button.setObjectName("primaryButton")
        open_button.setMinimumHeight(44)
        open_button.clicked.connect(self.open_dashboard)
        layout.addWidget(open_button, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        footer = QLabel("Hospital Monitoring • LeptoTrack")
        footer.setObjectName("welcomeFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

        self.setStyleSheet(load_stylesheet())

    def open_dashboard(self):
        hospital_name = self.hospital_input.text().strip()
        if not hospital_name:
            QMessageBox.warning(
                self,
                "Hospital Name Required",
                "Please type your hospital name before opening the dashboard."
            )
            self.hospital_input.setFocus()
            return

        save_setting("hospital_name", hospital_name)
        self.dashboard = LeptoTrack(hospital_name)
        self.dashboard.show()
        self.close()


if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    app.setWindowIcon(create_app_icon())

    saved_hospital_name = get_setting("hospital_name")

    if saved_hospital_name:
        window = LeptoTrack(saved_hospital_name)
    else:
        window = WelcomePage()

    window.show()
    sys.exit(app.exec())