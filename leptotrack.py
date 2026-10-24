import os
import sys

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QFrame,
    QHeaderView, QProgressBar
)


class StatCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("statTitle")
        value_label = QLabel("—")
        value_label.setObjectName("statValue")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()


class CapacityDonut(QWidget):
    """Placeholder donut chart; connect real capacity data when available."""
    def __init__(self):
        super().__init__()
        self.setMinimumSize(180, 180)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 28
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2,
                      side, side)
        pen = QPen(QColor("#E2E8F0"), 16)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(QColor("#172B4D"))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                         "— / —\nAvailable Beds")
        painter.end()


class CapacityBar(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("capacityCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("capacityTitle")
        value_label = QLabel("— / — beds")
        value_label.setObjectName("capacityValue")
        progress = QProgressBar()
        progress.setObjectName("capacityProgress")
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(False)
        note = QLabel("No data available")
        note.setObjectName("mutedText")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(progress)
        layout.addWidget(note)


class LeptoTrack(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LeptoTrack | Pasig City")
        self.resize(1280, 850)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        # Header
        header = QHBoxLayout()
        title_group = QVBoxLayout()
        title_group.setSpacing(5)

        title = QLabel("LeptoTrack")
        title.setObjectName("pageTitle")
        subtitle = QLabel(
            "Leptospirosis case monitoring and healthcare bed-capacity dashboard"
        )
        subtitle.setObjectName("pageSubtitle")
        scope = QLabel("PROJECT SCOPE: PASIG CITY")
        scope.setObjectName("scopeLabel")
        title_group.addWidget(title)
        title_group.addWidget(subtitle)
        title_group.addWidget(scope)

        badge = QLabel("HEALTHCARE MONITORING")
        badge.setObjectName("statusBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addLayout(title_group)
        header.addStretch()
        header.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        # Statistic cards
        stats = QGridLayout()
        stats.setHorizontalSpacing(14)
        stats.setVerticalSpacing(14)
        for column, name in enumerate([
            "Total Reported Cases", "Active Cases",
            "Recovered Cases", "Reported Deaths"
        ]):
            stats.addWidget(StatCard(name), 0, column)
        root.addLayout(stats)

        # Weekly trend and bed capacity
        dashboard_row = QHBoxLayout()
        dashboard_row.setSpacing(16)

        trend_panel = QFrame()
        trend_panel.setObjectName("panel")
        trend_layout = QVBoxLayout(trend_panel)
        trend_layout.setContentsMargins(18, 16, 18, 18)
        trend_layout.setSpacing(10)
        trend_title = QLabel("Weekly Case Trend")
        trend_title.setObjectName("sectionTitle")
        placeholder = QLabel(
            "Case trend visualization will appear here\n"
            "when reporting data is available."
        )
        placeholder.setObjectName("chartPlaceholder")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setMinimumHeight(250)
        trend_layout.addWidget(trend_title)
        trend_layout.addWidget(placeholder, 1)

        capacity_panel = QFrame()
        capacity_panel.setObjectName("panel")
        capacity_layout = QVBoxLayout(capacity_panel)
        capacity_layout.setContentsMargins(18, 16, 18, 18)
        capacity_layout.setSpacing(12)
        capacity_title = QLabel("Healthcare Bed Capacity")
        capacity_title.setObjectName("sectionTitle")
        capacity_layout.addWidget(capacity_title)
        capacity_layout.addWidget(CapacityDonut(), alignment=Qt.AlignmentFlag.AlignCenter)
        capacity_layout.addWidget(CapacityBar("Hospital Beds"))
        capacity_layout.addWidget(CapacityBar("ICU Beds"))

        dashboard_row.addWidget(trend_panel, 3)
        dashboard_row.addWidget(capacity_panel, 2)
        root.addLayout(dashboard_row)

        # Facility reporting status
        reporting_panel = QFrame()
        reporting_panel.setObjectName("panel")
        reporting_layout = QVBoxLayout(reporting_panel)
        reporting_layout.setContentsMargins(18, 14, 18, 14)
        reporting_layout.setSpacing(6)
        reporting_title = QLabel("Facility Reporting Status")
        reporting_title.setObjectName("sectionTitle")
        reporting_note = QLabel(
            "No facility reporting data available. Add healthcare facilities below to begin tracking."
        )
        reporting_note.setObjectName("mutedText")
        reporting_layout.addWidget(reporting_title)
        reporting_layout.addWidget(reporting_note)
        root.addWidget(reporting_panel)

        # Facility records and actions
        records_header = QHBoxLayout()
        records_title = QLabel("Healthcare Facility Records")
        records_title.setObjectName("sectionTitle")
        records_header.addWidget(records_title)
        records_header.addStretch()

        for text, role in [
            ("+ Add Facility", "add"),
            ("Edit Record", "edit"),
            ("Delete Record", "delete"),
            ("Refresh", "refresh"),
        ]:
            button = QPushButton(text)
            button.setProperty("role", role)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            records_header.addWidget(button)
        root.addLayout(records_header)

        self.facility_table = QTableWidget(0, 7)
        self.facility_table.setObjectName("facilityTable")
        self.facility_table.setHorizontalHeaderLabels([
            "Facility Name", "Facility Type", "Total Beds",
            "Available Beds", "ICU Beds", "Cases Reported", "Last Updated"
        ])
        self.facility_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.facility_table.verticalHeader().setVisible(False)
        self.facility_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.facility_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.facility_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.facility_table.setAlternatingRowColors(True)
        self.facility_table.setMinimumHeight(180)
        root.addWidget(self.facility_table, 1)

        # All widget styling is loaded from style.qss.
        style_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
        try:
            with open(style_path, "r", encoding="utf-8") as stylesheet:
                self.setStyleSheet(stylesheet.read())
        except OSError as error:
            print(f"Could not load style.qss: {error}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LeptoTrack()
    window.show()
    sys.exit(app.exec())
