#!/usr/bin/env python3

import sys
import time
import platform
import psutil

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QProgressBar,
    QFrame,
    QSizePolicy,
)


class CircularGauge(QWidget):
    def __init__(self, title, color):
        super().__init__()

        self.title = title
        self.color = QColor(color)
        self.value = 0

        self.setMinimumSize(230, 230)

    def setValue(self, value):
        self.value = max(0, min(100, float(value)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height())
        margin = 25

        rect = QRectF(
            (self.width() - size) / 2 + margin,
            (self.height() - size) / 2 + margin,
            size - margin * 2,
            size - margin * 2,
        )

        # Hintergrund
        background_pen = QPen(QColor("#303640"))
        background_pen.setWidth(18)
        background_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(background_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Fortschritt
        progress_pen = QPen(self.color)
        progress_pen.setWidth(18)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(progress_pen)

        angle = int(-self.value * 360 / 100 * 16)

        painter.drawArc(
            rect,
            90 * 16,
            angle
        )

        # Prozent
        painter.setPen(QColor("#ffffff"))

        value_font = QFont("Noto Sans")
        value_font.setPointSize(28)
        value_font.setBold(True)

        painter.setFont(value_font)

        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.value:.0f}%"
        )

        # Titel
        title_font = QFont("Noto Sans")
        title_font.setPointSize(10)
        title_font.setBold(True)

        painter.setFont(title_font)

        title_rect = QRectF(
            0,
            self.height() / 2 + 42,
            self.width(),
            30
        )

        painter.drawText(
            title_rect,
            Qt.AlignmentFlag.AlignCenter,
            self.title
        )


class Card(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")


class CoreWidget(QFrame):
    def __init__(self, number):
        super().__init__()

        self.setObjectName("Core")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        self.name = QLabel(f"CORE {number}")
        self.name.setObjectName("CoreName")

        self.usage = QLabel("0 %")
        self.usage.setObjectName("CoreUsage")

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)

        self.temperature = QLabel("Temperatur: -- °C")
        self.temperature.setObjectName("CoreTemp")

        layout.addWidget(self.name)
        layout.addWidget(self.usage)
        layout.addWidget(self.bar)
        layout.addWidget(self.temperature)

    def update_core(self, usage, temperature=None):
        self.usage.setText(f"{usage:.0f} %")
        self.bar.setValue(int(usage))

        if temperature is None:
            self.temperature.setText("Temperatur: -- °C")
        else:
            self.temperature.setText(
                f"Temperatur: {temperature:.1f} °C"
            )


class SystemMonitor(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("System Monitor")
        self.resize(1250, 900)
        self.setMinimumSize(1000, 700)

        self.previous_net = psutil.net_io_counters()
        self.previous_net_time = time.monotonic()

        self.core_widgets = []

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system)
        self.timer.start(1000)

        self.update_system()

    # =========================================================
    # UI
    # =========================================================

    def build_ui(self):

        main = QVBoxLayout(self)
        main.setContentsMargins(20, 20, 20, 20)
        main.setSpacing(14)

        # -----------------------------------------------------
        # Header
        # -----------------------------------------------------

        title = QLabel("SYSTEM MONITOR")
        title.setObjectName("Title")

        subtitle = QLabel(
            f"{platform.system()} {platform.release()}  •  "
            f"{platform.machine()}"
        )
        subtitle.setObjectName("Subtitle")

        main.addWidget(title)
        main.addWidget(subtitle)

        # -----------------------------------------------------
        # CPU / RAM
        # -----------------------------------------------------

        gauges = QHBoxLayout()
        gauges.setSpacing(15)

        # CPU
        cpu_card = Card()
        cpu_layout = QVBoxLayout(cpu_card)

        self.cpu_gauge = CircularGauge(
            "CPU AUSLASTUNG",
            "#00d9ff"
        )

        self.cpu_temp = QLabel("CPU Temperatur: -- °C")
        self.cpu_temp.setObjectName("Temperature")

        self.cpu_clock = QLabel("CPU Takt: -- MHz")
        self.cpu_clock.setObjectName("Info")

        self.cpu_model = QLabel("CPU: --")
        self.cpu_model.setObjectName("Info")

        cpu_layout.addWidget(self.cpu_gauge)

        cpu_layout.addWidget(
            self.cpu_temp,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        cpu_layout.addWidget(
            self.cpu_clock,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        cpu_layout.addWidget(
            self.cpu_model,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # RAM
        ram_card = Card()
        ram_layout = QVBoxLayout(ram_card)

        self.ram_gauge = CircularGauge(
            "RAM AUSLASTUNG",
            "#55e67a"
        )

        self.ram_info = QLabel("RAM: --")
        self.ram_info.setObjectName("Info")

        self.ram_free = QLabel("Frei: --")
        self.ram_free.setObjectName("Info")

        ram_layout.addWidget(self.ram_gauge)

        ram_layout.addWidget(
            self.ram_info,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        ram_layout.addWidget(
            self.ram_free,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        gauges.addWidget(cpu_card)
        gauges.addWidget(ram_card)

        main.addLayout(gauges)

        # -----------------------------------------------------
        # CPU Kerne
        # -----------------------------------------------------

        core_card = Card()
        core_layout = QVBoxLayout(core_card)

        core_title = QLabel("CPU-KERNE")
        core_title.setObjectName("SectionTitle")

        core_layout.addWidget(core_title)

        self.core_grid = QGridLayout()
        self.core_grid.setSpacing(8)

        core_count = psutil.cpu_count(logical=True) or 1

        for i in range(core_count):

            widget = CoreWidget(i)

            row = i // 4
            column = i % 4

            self.core_grid.addWidget(
                widget,
                row,
                column
            )

            self.core_widgets.append(widget)

        core_layout.addLayout(self.core_grid)

        main.addWidget(core_card)

        # -----------------------------------------------------
        # Informationen
        # -----------------------------------------------------

        info_card = Card()
        info_layout = QGridLayout(info_card)

        info_title = QLabel("SYSTEM-INFORMATIONEN")
        info_title.setObjectName("SectionTitle")

        info_layout.addWidget(
            info_title,
            0,
            0,
            1,
            4
        )

        self.uptime = QLabel("Uptime: --")
        self.load = QLabel("Load: --")
        self.swap = QLabel("Swap: --")
        self.disk = QLabel("SSD: --")

        self.network = QLabel("Netzwerk: --")
        self.kernel = QLabel("Kernel: --")
        self.memory = QLabel("RAM frei: --")
        self.processes = QLabel("Prozesse: --")

        info_labels = [
            self.uptime,
            self.load,
            self.swap,
            self.disk,
            self.network,
            self.kernel,
            self.memory,
            self.processes,
        ]

        for label in info_labels:
            label.setObjectName("InfoBox")

        positions = [
            (1, 0),
            (1, 1),
            (1, 2),
            (1, 3),
            (2, 0),
            (2, 1),
            (2, 2),
            (2, 3),
        ]

        for label, position in zip(info_labels, positions):
            info_layout.addWidget(label, *position)

        main.addWidget(info_card)

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        self.status = QLabel(
            "● Überwachung aktiv"
        )

        self.status.setObjectName("Status")

        main.addWidget(
            self.status,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

    # =========================================================
    # Temperatur
    # =========================================================

    def get_temperatures(self):

        try:
            sensors = psutil.sensors_temperatures()

            if not sensors:
                return [], None

            core_temps = []

            # Intel
            if "coretemp" in sensors:

                for sensor in sensors["coretemp"]:

                    if sensor.current is not None:

                        if sensor.label.lower().startswith("package"):
                            continue

                        core_temps.append(sensor.current)

                package_temp = None

                for sensor in sensors["coretemp"]:

                    if sensor.current is not None:

                        label = sensor.label.lower()

                        if (
                            "package" in label
                            or "physical id" in label
                        ):
                            package_temp = sensor.current
                            break

                if package_temp is None and core_temps:
                    package_temp = max(core_temps)

                return core_temps, package_temp

            # AMD / andere Systeme
            all_temps = []

            for entries in sensors.values():

                for sensor in entries:

                    if sensor.current is not None:
                        all_temps.append(sensor.current)

            if all_temps:
                return [], max(all_temps)

        except Exception:
            pass

        return [], None

    # =========================================================
    # Uptime
    # =========================================================

    def get_uptime(self):

        seconds = int(time.time() - psutil.boot_time())

        days = seconds // 86400
        seconds %= 86400

        hours = seconds // 3600
        seconds %= 3600

        minutes = seconds // 60

        return f"{days} Tage  {hours:02d}:{minutes:02d}"

    # =========================================================
    # Netzwerk
    # =========================================================

    def get_network(self):

        current = psutil.net_io_counters()
        now = time.monotonic()

        elapsed = now - self.previous_net_time

        if elapsed <= 0:
            return 0, 0

        download = (
            current.bytes_recv -
            self.previous_net.bytes_recv
        ) / elapsed

        upload = (
            current.bytes_sent -
            self.previous_net.bytes_sent
        ) / elapsed

        self.previous_net = current
        self.previous_net_time = now

        return download, upload

    # =========================================================
    # Bytes
    # =========================================================

    def format_bytes(self, value):

        if value >= 1024 ** 3:
            return f"{value / 1024 ** 3:.1f} GB"

        if value >= 1024 ** 2:
            return f"{value / 1024 ** 2:.1f} MB"

        if value >= 1024:
            return f"{value / 1024:.1f} KB"

        return f"{value:.0f} B"

    # =========================================================
    # System aktualisieren
    # =========================================================

    def update_system(self):

        # CPU
        cpu_usage = psutil.cpu_percent(interval=None)

        self.cpu_gauge.setValue(cpu_usage)

        # RAM
        memory = psutil.virtual_memory()

        self.ram_gauge.setValue(memory.percent)

        used = memory.used / 1024 ** 3
        total = memory.total / 1024 ** 3
        available = memory.available / 1024 ** 3

        self.ram_info.setText(
            f"Belegt: {used:.1f} / {total:.1f} GB"
        )

        self.ram_free.setText(
            f"Frei: {available:.1f} GB"
        )

        # CPU Temperatur
        core_temps, package_temp = self.get_temperatures()

        if package_temp is not None:

            self.cpu_temp.setText(
                f"CPU Temperatur: {package_temp:.1f} °C"
            )

        else:

            self.cpu_temp.setText(
                "CPU Temperatur: nicht verfügbar"
            )

        # CPU Frequenz
        try:

            frequency = psutil.cpu_freq()

            if frequency:

                self.cpu_clock.setText(
                    f"CPU Takt: {frequency.current:.0f} MHz"
                )

        except Exception:
            self.cpu_clock.setText(
                "CPU Takt: nicht verfügbar"
            )

        # CPU Modell
        model = platform.processor()

        if not model:
            model = "CPU"

        self.cpu_model.setText(
            model
        )

        # Einzelne Kerne
        core_usage = psutil.cpu_percent(
            interval=None,
            percpu=True
        )

        for i, widget in enumerate(self.core_widgets):

            usage = (
                core_usage[i]
                if i < len(core_usage)
                else 0
            )

            temperature = (
                core_temps[i]
                if i < len(core_temps)
                else None
            )

            widget.update_core(
                usage,
                temperature
            )

        # Uptime
        self.uptime.setText(
            f"Uptime: {self.get_uptime()}"
        )

        # Load
        try:

            load = os_load_average()

            self.load.setText(
                f"Load: {load[0]:.2f} / "
                f"{load[1]:.2f} / "
                f"{load[2]:.2f}"
            )

        except Exception:

            self.load.setText(
                "Load: nicht verfügbar"
            )

        # Swap
        swap = psutil.swap_memory()

        swap_used = swap.used / 1024 ** 3
        swap_total = swap.total / 1024 ** 3

        self.swap.setText(
            f"Swap: {swap_used:.1f} / "
            f"{swap_total:.1f} GB"
        )

        # SSD
        try:

            disk = psutil.disk_usage("/")

            self.disk.setText(
                f"SSD: {disk.percent:.0f}%  •  "
                f"{disk.used / 1024**3:.1f} / "
                f"{disk.total / 1024**3:.1f} GB"
            )

        except Exception:

            self.disk.setText(
                "SSD: nicht verfügbar"
            )

        # Netzwerk
        download, upload = self.get_network()

        self.network.setText(
            f"Netzwerk: ↓ {self.format_bytes(download)}/s  "
            f"↑ {self.format_bytes(upload)}/s"
        )

        # Kernel
        self.kernel.setText(
            f"Kernel: {platform.release()}"
        )

        # RAM
        self.memory.setText(
            f"RAM frei: {available:.1f} GB"
        )

        # Prozesse
        try:

            process_count = len(psutil.pids())

            self.processes.setText(
                f"Prozesse: {process_count}"
            )

        except Exception:

            self.processes.setText(
                "Prozesse: --"
            )

        # Status
        self.status.setText(
            "● Überwachung aktiv  •  Aktualisierung: 1 Sekunde"
        )


def os_load_average():
    return psutil.getloadavg()


def main():

    app = QApplication(sys.argv)

    app.setStyle("Fusion")

    app.setStyleSheet("""
        QWidget {
            background-color: #101318;
            color: #eeeeee;
            font-family: "Noto Sans";
            font-size: 10pt;
        }

        #Title {
            font-size: 26pt;
            font-weight: bold;
            color: #ffffff;
        }

        #Subtitle {
            color: #888888;
        }

        #Card {
            background-color: #181c22;
            border: 1px solid #292f38;
            border-radius: 14px;
        }

        #SectionTitle {
            font-size: 14pt;
            font-weight: bold;
            color: #ffffff;
            padding: 5px;
        }

        #Core {
            background-color: #20252d;
            border: 1px solid #303640;
            border-radius: 10px;
        }

        #CoreName {
            color: #cccccc;
            font-weight: bold;
        }

        #CoreUsage {
            color: #00d9ff;
            font-size: 18pt;
            font-weight: bold;
        }

        #CoreTemp {
            color: #aaaaaa;
            font-size: 9pt;
        }

        QProgressBar {
            background-color: #11151a;
            border: none;
            border-radius: 4px;
        }

        QProgressBar::chunk {
            background-color: #00d9ff;
            border-radius: 4px;
        }

        #Temperature {
            color: #ffb347;
            font-size: 12pt;
            font-weight: bold;
        }

        #Info {
            color: #aaaaaa;
        }

        #InfoBox {
            background-color: #20252d;
            border-radius: 8px;
            padding: 12px;
            color: #dddddd;
        }

        #Status {
            color: #55e67a;
            padding: 5px;
        }
    """)

    window = SystemMonitor()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
