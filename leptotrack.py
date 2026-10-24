import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget,
    QLineEdit, QComboBox, QFrame, QHeaderView, QProgressBar
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor


class StatCard(QFrame):
    def __init__(self, title, color):
        super().__init__()
        self.setObjectName("statCard")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(title))

        self.value = QLabel("—")
        self.value.setStyleSheet(
            f"font-size:25px;font-weight:bold;color:{color};"
        )
        layout.addWidget(self.value)


class CapacityDonut(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(210, 210)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height()) - 28
        rect = QRectF(
            (self.width() - side) / 2,
            (self.height() - side) / 2,
            side, side
        )

        pen = QPen(QColor("#E1E7ED"), 18)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        painter.setPen(QColor("#173B56"))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            "— / —\nAvailable Beds"
        )


class CapacityBar(QFrame):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)

        heading = QHBoxLayout()
        heading.addWidget(QLabel(title))
        heading.addStretch()
        heading.addWidget(QLabel("— / —"))
        layout.addLayout(heading)

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        bar.setTextVisible(False)
        bar.setFixedHeight(16)
        layout.addWidget(bar)

        layout.addWidget(QLabel("Availability not entered"))


class LeptoTrack(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LeptoTrack | Healthcare Monitoring System")
        self.resize(1350, 900)

        central = QWidget()
        self.setCentralWidget(central)

        main = QVBoxLayout(central)
        main.setSpacing(12)

        header = QHBoxLayout()
        branding = QVBoxLayout()

        title = QLabel("LeptoTrack")
        title.setObjectName("mainTitle")
        branding.addWidget(title)
        branding.addWidget(QLabel(
            "Leptospirosis Patient Volume and Healthcare Facility Capacity Monitoring System"
        ))

        header.addLayout(branding)
        header.addStretch()

        badge = QLabel("FACILITY CAPACITY MONITORING")
        badge.setObjectName("badge")
        header.addWidget(badge)
        main.addLayout(header)

        stats = QGridLayout()

        self.facility_card = StatCard("Healthcare Facilities", "#147D76")
        self.patient_card = StatCard("Reported Patients", "#D97706")
        self.total_card = StatCard("Total Beds", "#3478C5")
        self.available_card = StatCard("Available Beds", "#159B83")
        self.icu_card = StatCard("Available ICU Beds", "#8E63B5")

        for col, card in enumerate([
            self.facility_card,
            self.patient_card,
            self.total_card,
            self.available_card,
            self.icu_card
        ]):
            stats.addWidget(card, 0, col)

        main.addLayout(stats)

        visual_row = QHBoxLayout()

        donut_frame = QFrame()
        donut_frame.setObjectName("panel")
        donut_layout = QVBoxLayout(donut_frame)
        donut_layout.addWidget(QLabel("Overall Bed Availability"))

        donut_layout.addWidget(
            CapacityDonut(),
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        occupied = QLabel("Occupied beds: —")
        occupied.setAlignment(Qt.AlignmentFlag.AlignCenter)
        donut_layout.addWidget(occupied)

        visual_row.addWidget(donut_frame, 1)

        bars_frame = QFrame()
        bars_frame.setObjectName("panel")
        bars_layout = QVBoxLayout(bars_frame)
        bars_layout.addWidget(QLabel("Capacity by Bed Type"))
        bars_layout.addWidget(CapacityBar("General Beds"))
        bars_layout.addWidget(CapacityBar("ICU Beds"))

        warning = QLabel("Capacity status will appear when data is available.")
        warning.setWordWrap(True)
        warning.setStyleSheet(
            "color:#64748B;font-weight:bold;padding:8px;"
        )
        bars_layout.addWidget(warning)
        bars_layout.addStretch()

        visual_row.addWidget(bars_frame, 2)
        main.addLayout(visual_row)

        section = QLabel("Healthcare Facility Records")
        section.setObjectName("sectionTitle")
        main.addWidget(section)

        toolbar = QHBoxLayout()

        search = QLineEdit()
        search.setPlaceholderText("Search facility name or location...")

        location = QComboBox()
        location.addItems([
            "All Locations",
            "Metro Manila",
            "Quezon City",
            "Pasig City",
            "Makati",
            "Manila",
            "Other Locations"
        ])

        toolbar.addWidget(search, 3)
        toolbar.addWidget(location, 1)
        main.addLayout(toolbar)

        buttons = QHBoxLayout()

        for text, color in [
            ("+ Add Facility", "#147D76"),
            ("Edit Record", "#64748B"),
            ("Delete Record", "#C03939"),
            ("Refresh", "#64748B")
        ]:
            button = QPushButton(text)
            button.setStyleSheet(
                f"background:{color};color:white;padding:9px;"
                "border:none;border-radius:5px;"
            )
            buttons.addWidget(button)

        main.addLayout(buttons)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            "Facility ID",
            "Facility Name",
            "Location",
            "Contact Number",
            "Patients",
            "Total Beds",
            "Bed Availability",
            "Last Updated"
        ])

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(220)
        main.addWidget(self.table, 1)

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background:#F3F7FA;
                color:#263B4D;
                font-family:Arial;
                font-size:12px;
            }
            #mainTitle {
                font-size:28px;
                font-weight:bold;
                color:#147D76;
            }
            #sectionTitle {
                font-size:18px;
                font-weight:bold;
            }
            #badge {
                background:#DDF2EE;
                color:#147D76;
                padding:10px;
                border-radius:6px;
                font-weight:bold;
            }
            #statCard, #panel {
                background:white;
                border:1px solid #DCE5ED;
                border-radius:9px;
            }
            #statCard {
                padding:7px;
            }
            #panel {
                padding:10px;
            }
            QLineEdit, QComboBox {
                background:white;
                border:1px solid #D5DEE8;
                border-radius:5px;
                padding:8px;
            }
            QProgressBar {
                background:#E6EDF3;
                border:none;
                border-radius:7px;
            }
            QProgressBar::chunk {
                background:#159B83;
                border-radius:7px;
            }
            QTableWidget {
                background:white;
                alternate-background-color:#F7FAFC;
                gridline-color:#E5EAF0;
                border:1px solid #DCE4ED;
            }
            QHeaderView::section {
                background:#E9F0F4;
                padding:8px;
                border:none;
                font-weight:bold;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LeptoTrack()
    window.show()
    sys.exit(app.exec())
