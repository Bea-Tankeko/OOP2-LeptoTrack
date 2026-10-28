import os, sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QLineEdit, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame,
    QProgressBar, QStackedWidget
)
#====================================================================================================== (BORDERS FOR EACH CLASS TO AVOID CONFUSION)
class StatCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("statCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        for text, name in ((title, "statTitle"), ("", "statValue")):
            label = QLabel(text)
            label.setObjectName(name)
            layout.addWidget(label)
        layout.addStretch()
#======================================================================================================#
class CapacityBar(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("capacityCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        for text, name in ((title, "capacityTitle"), ("", "capacityValue")):
            label = QLabel(text)
            label.setObjectName(name)
            layout.addWidget(label)

        progress = QProgressBar()
        progress.setObjectName("capacityProgress")
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setTextVisible(False)
        layout.addWidget(progress)

        note = QLabel("")
        note.setObjectName("mutedText")
        layout.addWidget(note)
#======================================================================================================#
class FacilityFrontPage(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setObjectName("frontPage")
        root = QVBoxLayout(self)
        root.setContentsMargins(36, 36, 36, 36)
        root.addStretch()
        card = QFrame()
        card.setObjectName("welcomeCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(34, 34, 34, 34)
        layout.setSpacing(16)

        for text, name in (
            ("LeptoTrack", "pageTitle"),
            ("Hospital Setup", "sectionTitle"),
            ("", "pageSubtitle")
        ):
            label = QLabel(text)
            label.setObjectName(name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if name == "pageSubtitle":
                label.setWordWrap(True)
            layout.addWidget(label)

        layout.addSpacing(8)
        self.facility_input = QLineEdit()
        self.facility_input.setObjectName("facilityInput")
        self.facility_input.setPlaceholderText("")
        self.facility_input.setClearButtonEnabled(True)
        self.facility_input.returnPressed.connect(self.continue_to_dashboard)

        self.error_label = QLabel("")
        self.error_label.setObjectName("errorText")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        button = QPushButton("Continue")
        button.setObjectName("primaryButton")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.continue_to_dashboard)

        for widget in (self.facility_input, self.error_label, button):
            layout.addWidget(widget)

        root.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        root.addStretch()

    def continue_to_dashboard(self):
        name = self.facility_input.text().strip()
        if not name:
            self.error_label.setText("")
            self.facility_input.setFocus()
            return
        self.error_label.clear()
        self.callback(name)

#======================================================================================================#
class HospitalDashboard(QWidget):
    def __init__(self, facility_name):
        super().__init__()
        self.setObjectName("centralWidget")
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)
        header = QHBoxLayout()
        group = QVBoxLayout()
        group.setSpacing(5)

        for text, name in (
            ("LeptoTrack", "pageTitle"),
            (facility_name, "facilityName"),
            ("", "pageSubtitle"),
            ("SINGLE-HOSPITAL DASHBOARD", "scopeLabel")
        ):
            label = QLabel(text)
            label.setObjectName(name)
            group.addWidget(label)
        badge = QLabel("HOSPITAL MONITORING")
        badge.setObjectName("statusBadge")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addLayout(group)
        header.addStretch()
        header.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)
        stats = QGridLayout()
        stats.setHorizontalSpacing(14)
        stats.setVerticalSpacing(14)
        for col, name in enumerate((
            "Total Reported Cases", "Active Cases",
            "Recovered Cases", "Reported Deaths"
        )):
            stats.addWidget(StatCard(name), 0, col)
        root.addLayout(stats)
        row = QHBoxLayout()
        row.setSpacing(16)
        trend = QFrame()
        trend.setObjectName("panel")
        tl = QVBoxLayout(trend)
        tl.setContentsMargins(18, 16, 18, 18)
        tl.setSpacing(10)
        title = QLabel("Weekly Case Trend")
        title.setObjectName("sectionTitle")
        chart = QLabel("")
        chart.setObjectName("chartPlaceholder")
        chart.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart.setMinimumHeight(250)
        tl.addWidget(title)
        tl.addWidget(chart, 1)
        capacity = QFrame()
        capacity.setObjectName("panel")
        cl = QVBoxLayout(capacity)
        cl.setContentsMargins(18, 16, 18, 18)
        cl.setSpacing(12)
        title = QLabel("Hospital Bed Capacity")
        title.setObjectName("sectionTitle")
        note = QLabel("")
        note.setObjectName("capacitySummary")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setWordWrap(True)
        note.setMinimumHeight(110)
        cl.addWidget(title)
        cl.addWidget(note, 1)
        cl.addWidget(CapacityBar("Hospital Beds"))
        cl.addWidget(CapacityBar("ICU Beds"))
        row.addWidget(trend, 3)
        row.addWidget(capacity, 2)
        root.addLayout(row)
        panel = QFrame()
        panel.setObjectName("panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)
        for text, name in (
            ("Hospital Reporting Status", "sectionTitle"),
            ("", "mutedText")
        ):
            label = QLabel(text)
            label.setObjectName(name)
            layout.addWidget(label)
        root.addWidget(panel)

        actions = QHBoxLayout()
        title = QLabel("Hospital Actions")
        title.setObjectName("sectionTitle")
        actions.addWidget(title)
        actions.addStretch()
        for text, role in (
            ("Edit Record", "edit"),
            ("Delete Record", "delete"),
            ("Refresh", "refresh")
        ):
            button = QPushButton(text)
            button.setProperty("role", role)
            button.setCursor(Qt.CursorShape.ArrowCursor)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            actions.addWidget(button)
        root.addLayout(actions)
        root.addStretch()
#======================================================================================================#
class LeptoTrack(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LeptoTrack")
        self.resize(1280, 850)
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.front_page = FacilityFrontPage(self.show_dashboard)
        self.pages.addWidget(self.front_page)
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "style.qss")
        try:
            with open(path, encoding="utf-8") as file:
                self.setStyleSheet(file.read())
        except OSError as error:
            print(f"Could not load style.qss: {error}")
    def show_dashboard(self, name):
        dashboard = HospitalDashboard(name)
        self.pages.addWidget(dashboard)
        self.pages.setCurrentWidget(dashboard)
        self.setWindowTitle(f"LeptoTrack | {name}")
#======================================================================================================#
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LeptoTrack()
    window.show()
    sys.exit(app.exec())