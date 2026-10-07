import sys
import os
import re
import platform
import subprocess
import time

import psutil

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QFrame,
)


def fmt_bytes(value):
    value = float(value or 0)

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024

    return f"{value:.1f} PB"


def fmt_speed(value):
    return f"{fmt_bytes(value)}/s"


def fmt_temp(value):
    return "N/A" if value is None else f"{value:.1f} °C"


def uptime():
    seconds = int(time.time() - psutil.boot_time())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def get_cpu_model():
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass

    return platform.processor() or "Unbekannt"


def get_os():
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            text = f.read()

        match = re.search(
            r'^PRETTY_NAME="?(.+?)"?$',
            text,
            re.MULTILINE,
        )

        if match:
            return match.group(1)

    except Exception:
        pass

    return platform.system()


def get_gpu():
    try:
        result = subprocess.run(
            ["sh", "-c", "lspci | grep -Ei 'VGA|3D|Display'"],
            capture_output=True,
            text=True,
            timeout=2,
        )

        lines = result.stdout.strip().splitlines()

        if lines:
            return " | ".join(
                line.split(":", 2)[-1].strip()
                for line in lines
            )

    except Exception:
        pass

    return "Nicht erkannt"


def read_sensors():
    data = {
        "cpu_temp": None,
        "fan": None,
        "pwm": None,
        "wifi_temp": None,
        "pch_temp": None,
        "nvme_temp": None,
    }

    try:
        result = subprocess.run(
            ["sensors"],
            capture_output=True,
            text=True,
            timeout=2,
        )

        text = result.stdout

        match = re.search(
            r"thinkpad-isa-0000.*?"
            r"fan1:\s+(\d+)\s+RPM.*?"
            r"CPU:\s+\+?([\d.]+)°C.*?"
            r"pwm1:\s+([\d.]+)%",
            text,
            re.S,
        )

        if match:
            data["fan"] = float(match.group(1))
            data["cpu_temp"] = float(match.group(2))
            data["pwm"] = float(match.group(3))

        match = re.search(
            r"iwlwifi_1-virtual-0.*?"
            r"temp1:\s+\+?([\d.]+)°C",
            text,
            re.S,
        )

        if match:
            data["wifi_temp"] = float(match.group(1))

        match = re.search(
            r"pch_skylake-virtual-0.*?"
            r"temp1:\s+\+?([\d.]+)°C",
            text,
            re.S,
        )

        if match:
            data["pch_temp"] = float(match.group(1))

        match = re.search(
            r"nvme-pci-[^\n]+.*?"
            r"Composite:\s+\+?([\d.]+)°C",
            text,
            re.S,
        )

        if match:
            data["nvme_temp"] = float(match.group(1))

    except Exception:
        pass

    return data


def get_battery():
    data = {
        "percent": None,
        "status": "N/A",
        "voltage": None,
        "power": None,
    }

    try:
        battery = psutil.sensors_battery()

        if battery:
            data["percent"] = battery.percent
            data["status"] = (
                "Netzbetrieb"
                if battery.power_plugged
                else "Akku"
            )

    except Exception:
        pass

    base = "/sys/class/power_supply/BAT0"

    try:
        with open(f"{base}/capacity") as f:
            data["percent"] = float(f.read().strip())
    except Exception:
        pass

    try:
        with open(f"{base}/status") as f:
            data["status"] = f.read().strip()
    except Exception:
        pass

    try:
        with open(f"{base}/voltage_now") as f:
            data["voltage"] = float(f.read().strip()) / 1_000_000
    except Exception:
        pass

    try:
        with open(f"{base}/power_now") as f:
            data["power"] = float(f.read().strip()) / 1_000_000
    except Exception:
        pass

    return data


class Card(QFrame):

    def __init__(self, title):
        super().__init__()

        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")

        layout.addWidget(title_label)

        self.layout_box = layout


class BarCard(Card):

    def __init__(self, title):
        super().__init__(title)

        self.value = QLabel("--")
        self.value.setObjectName("BigValue")

        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(7)

        self.layout_box.addWidget(self.value)
        self.layout_box.addWidget(self.bar)

    def set_value(self, value):
        self.value.setText(f"{value:.1f} %")
        self.bar.setValue(int(value))


class CoreCard(QFrame):

    def __init__(self, number):
        super().__init__()

        self.setObjectName("Core")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(7, 5, 7, 5)
        layout.setSpacing(2)

        self.name = QLabel(f"CPU {number}")
        self.name.setObjectName("CoreName")

        self.value = QLabel("0 %")
        self.value.setObjectName("CoreValue")

        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(5)

        layout.addWidget(self.name)
        layout.addWidget(self.value)
        layout.addWidget(self.bar)

    def update_value(self, value):
        self.value.setText(f"{value:.0f} %")
        self.bar.setValue(int(value))


class SystemMonitor(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("System Monitor")
        self.resize(1200, 850)

        self.last_net = psutil.net_io_counters()
        self.last_time = time.time()

        self.build_ui()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

        self.update_data()

    def build_ui(self):

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()

        main = QVBoxLayout(container)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(8)

        header = QHBoxLayout()

        title_box = QVBoxLayout()

        title = QLabel("System Monitor")
        title.setObjectName("Title")

        subtitle = QLabel("Live-Systemübersicht")
        subtitle.setObjectName("Subtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        self.clock = QLabel("--:--:--")
        self.clock.setObjectName("Clock")

        header.addLayout(title_box)
        header.addStretch()
        header.addWidget(self.clock)

        main.addLayout(header)

        top = QGridLayout()
        top.setSpacing(7)

        self.cpu_card = BarCard("CPU")
        self.ram_card = BarCard("RAM")
        self.swap_card = BarCard("SWAP")
        self.temp_card = Card("CPU Temperatur")

        self.cpu_temp = QLabel("--")
        self.cpu_temp.setObjectName("BigValue")

        self.temp_card.layout_box.addWidget(self.cpu_temp)

        top.addWidget(self.cpu_card, 0, 0)
        top.addWidget(self.ram_card, 0, 1)
        top.addWidget(self.swap_card, 0, 2)
        top.addWidget(self.temp_card, 0, 3)

        main.addLayout(top)

        info_row = QHBoxLayout()
        info_row.setSpacing(7)

        cpu = Card("CPU")

        self.cpu_model = QLabel("--")
        self.cpu_model.setWordWrap(True)

        self.cpu_info = QLabel("--")
        self.load_info = QLabel("--")

        for label in [
            self.cpu_model,
            self.cpu_info,
            self.load_info,
        ]:
            label.setObjectName("Info")
            cpu.layout_box.addWidget(label)

        temps = Card("Temperaturen")

        self.temp_cpu = QLabel("--")
        self.temp_wifi = QLabel("--")
        self.temp_pch = QLabel("--")
        self.temp_nvme = QLabel("--")

        for label in [
            self.temp_cpu,
            self.temp_wifi,
            self.temp_pch,
            self.temp_nvme,
        ]:
            label.setObjectName("Info")
            temps.layout_box.addWidget(label)

        info_row.addWidget(cpu, 2)
        info_row.addWidget(temps, 1)

        main.addLayout(info_row)

        cores = Card("Einzelne CPU-Kerne")

        self.core_grid = QGridLayout()
        self.core_grid.setSpacing(5)

        self.core_widgets = []

        count = psutil.cpu_count(logical=True) or 1

        for i in range(count):

            widget = CoreCard(i)

            self.core_widgets.append(widget)

            self.core_grid.addWidget(
                widget,
                i // 4,
                i % 4,
            )

        cores.layout_box.addLayout(self.core_grid)

        main.addWidget(cores)

        hardware_row = QHBoxLayout()
        hardware_row.setSpacing(7)

        hardware = Card("Hardware")

        self.gpu = QLabel("--")
        self.fan = QLabel("--")
        self.pwm = QLabel("--")

        for label in [
            self.gpu,
            self.fan,
            self.pwm,
        ]:
            label.setObjectName("Info")
            label.setWordWrap(True)
            hardware.layout_box.addWidget(label)

        system = Card("System")

        self.os_label = QLabel("--")
        self.kernel = QLabel("--")
        self.desktop = QLabel("--")
        self.hostname = QLabel("--")
        self.python = QLabel("--")

        for label in [
            self.os_label,
            self.kernel,
            self.desktop,
            self.hostname,
            self.python,
        ]:
            label.setObjectName("Info")
            label.setWordWrap(True)
            system.layout_box.addWidget(label)

        hardware_row.addWidget(hardware)
        hardware_row.addWidget(system)

        main.addLayout(hardware_row)

        lower = QHBoxLayout()
        lower.setSpacing(7)

        disk = Card("SSD")

        self.disk_info = QLabel("--")
        self.disk_info.setObjectName("Info")

        self.disk_bar = QProgressBar()
        self.disk_bar.setTextVisible(False)
        self.disk_bar.setFixedHeight(7)

        disk.layout_box.addWidget(self.disk_info)
        disk.layout_box.addWidget(self.disk_bar)

        network = Card("Netzwerk")

        self.down = QLabel("--")
        self.up = QLabel("--")
        self.total_down = QLabel("--")
        self.total_up = QLabel("--")
        self.interfaces = QLabel("--")

        for label in [
            self.down,
            self.up,
            self.total_down,
            self.total_up,
            self.interfaces,
        ]:
            label.setObjectName("Info")
            label.setWordWrap(True)
            network.layout_box.addWidget(label)

        battery = Card("Akku")

        self.battery = QLabel("--")
        self.battery_status = QLabel("--")
        self.battery_voltage = QLabel("--")
        self.battery_power = QLabel("--")

        for label in [
            self.battery,
            self.battery_status,
            self.battery_voltage,
            self.battery_power,
        ]:
            label.setObjectName("Info")
            battery.layout_box.addWidget(label)

        lower.addWidget(disk)
        lower.addWidget(network)
        lower.addWidget(battery)

        main.addLayout(lower)

        processes = Card("Top-Prozesse")

        self.process_labels = []

        for _ in range(7):

            label = QLabel("--")
            label.setObjectName("Process")

            self.process_labels.append(label)
            processes.layout_box.addWidget(label)

        main.addWidget(processes)

        self.footer = QLabel("--")
        self.footer.setObjectName("Footer")

        main.addWidget(self.footer)

        scroll.setWidget(container)
        self.setCentralWidget(scroll)

    def update_data(self):

        now = time.time()

        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        swap = psutil.swap_memory()

        sensors = read_sensors()

        self.cpu_card.set_value(cpu)
        self.ram_card.set_value(ram.percent)
        self.swap_card.set_value(swap.percent)

        self.cpu_temp.setText(
            fmt_temp(sensors["cpu_temp"])
        )

        self.temp_cpu.setText(
            f"CPU: {fmt_temp(sensors['cpu_temp'])}"
        )

        self.temp_wifi.setText(
            f"WLAN: {fmt_temp(sensors['wifi_temp'])}"
        )

        self.temp_pch.setText(
            f"PCH: {fmt_temp(sensors['pch_temp'])}"
        )

        self.temp_nvme.setText(
            f"NVMe: {fmt_temp(sensors['nvme_temp'])}"
        )

        self.cpu_model.setText(
            get_cpu_model()
        )

        freq = psutil.cpu_freq()

        if freq:
            frequency = f"{freq.current / 1000:.2f} GHz"
        else:
            frequency = "N/A"

        cores = psutil.cpu_count(logical=False) or 0
        threads = psutil.cpu_count(logical=True) or 0

        self.cpu_info.setText(
            f"Takt: {frequency}  •  Kerne: {cores}  •  Threads: {threads}"
        )

        load = os.getloadavg()

        self.load_info.setText(
            f"Load: {load[0]:.2f} / {load[1]:.2f} / {load[2]:.2f}"
        )

        per_cpu = psutil.cpu_percent(
            interval=None,
            percpu=True,
        )

        for i, value in enumerate(per_cpu):

            if i < len(self.core_widgets):
                self.core_widgets[i].update_value(value)

        self.gpu.setText(
            f"GPU: {get_gpu()}"
        )

        self.fan.setText(
            f"Lüfter: {sensors['fan']:.0f} RPM"
            if sensors["fan"] is not None
            else "Lüfter: N/A"
        )

        self.pwm.setText(
            f"PWM: {sensors['pwm']:.0f} %"
            if sensors["pwm"] is not None
            else "PWM: N/A"
        )

        self.os_label.setText(
            f"OS: {get_os()}"
        )

        self.kernel.setText(
            f"Kernel: {platform.release()}"
        )

        self.desktop.setText(
            f"Desktop: {os.environ.get('XDG_CURRENT_DESKTOP', 'N/A')} / "
            f"{os.environ.get('XDG_SESSION_TYPE', 'N/A')}"
        )

        self.hostname.setText(
            f"Hostname: {platform.node()}"
        )

        self.python.setText(
            f"Python: {platform.python_version()}"
        )

        disk = psutil.disk_usage("/")

        self.disk_info.setText(
            f"Benutzt: {fmt_bytes(disk.used)}  •  "
            f"Frei: {fmt_bytes(disk.free)}  •  "
            f"Gesamt: {fmt_bytes(disk.total)}  •  "
            f"{disk.percent:.1f} %"
        )

        self.disk_bar.setValue(
            int(disk.percent)
        )

        net = psutil.net_io_counters()

        elapsed = max(now - self.last_time, 0.001)

        download = (
            net.bytes_recv - self.last_net.bytes_recv
        ) / elapsed

        upload = (
            net.bytes_sent - self.last_net.bytes_sent
        ) / elapsed

        self.down.setText(
            f"↓ Download: {fmt_speed(download)}"
        )

        self.up.setText(
            f"↑ Upload: {fmt_speed(upload)}"
        )

        self.total_down.setText(
            f"↓ Gesamt: {fmt_bytes(net.bytes_recv)}"
        )

        self.total_up.setText(
            f"↑ Gesamt: {fmt_bytes(net.bytes_sent)}"
        )

        interfaces = [
            name
            for name, info in psutil.net_if_stats().items()
            if info.isup
        ]

        self.interfaces.setText(
            "Interfaces: " + ", ".join(interfaces)
        )

        self.last_net = net
        self.last_time = now

        battery = get_battery()

        if battery["percent"] is not None:
            self.battery.setText(
                f"Akku: {battery['percent']:.0f} %"
            )
        else:
            self.battery.setText(
                "Akku: N/A"
            )

        self.battery_status.setText(
            f"Status: {battery['status']}"
        )

        self.battery_voltage.setText(
            f"Spannung: {battery['voltage']:.2f} V"
            if battery["voltage"] is not None
            else "Spannung: N/A"
        )

        self.battery_power.setText(
            f"Leistung: {battery['power']:.2f} W"
            if battery["power"] is not None
            else "Leistung: N/A"
        )

        processes = []

        for proc in psutil.process_iter(
            [
                "pid",
                "name",
                "cpu_percent",
                "memory_percent",
            ]
        ):

            try:

                info = proc.info

                processes.append(
                    (
                        info["cpu_percent"] or 0,
                        info["memory_percent"] or 0,
                        info["pid"],
                        info["name"] or "?",
                    )
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
            ):
                pass

        processes.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        for i, label in enumerate(self.process_labels):

            if i < len(processes):

                cpu_p, ram_p, pid, name = processes[i]

                label.setText(
                    f"{name[:28]:<28} "
                    f"PID {pid:<7} "
                    f"CPU {cpu_p:5.1f}%  "
                    f"RAM {ram_p:5.1f}%"
                )

            else:
                label.setText("--")

        self.clock.setText(
            time.strftime("%H:%M:%S")
        )

        self.footer.setText(
            f"Uptime: {uptime()}   •   "
            f"Prozesse: {len(processes)}   •   "
            f"Aktualisierung: 1 Sekunde"
        )


STYLE = """
QMainWindow {
    background: #0b0f14;
}

QScrollArea {
    background: #0b0f14;
}

QWidget {
    color: #e6edf3;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 12px;
}

QLabel#Title {
    font-size: 25px;
    font-weight: 700;
    color: #ffffff;
}

QLabel#Subtitle {
    color: #7d8996;
    font-size: 12px;
}

QLabel#Clock {
    color: #58a6ff;
    font-size: 23px;
    font-weight: 600;
}

QFrame#Card {
    background: #111820;
    border: 1px solid #202a35;
    border-radius: 9px;
}

QLabel#CardTitle {
    color: #8b98a7;
    font-size: 11px;
    font-weight: 700;
}

QLabel#BigValue {
    color: #58a6ff;
    font-size: 21px;
    font-weight: 700;
}

QLabel#Info {
    color: #d7dee7;
    padding: 2px 0;
}

QLabel#Process {
    background: #151d26;
    border-radius: 4px;
    padding: 5px;
    color: #c9d1d9;
    font-family: monospace;
    font-size: 11px;
}

QLabel#Footer {
    color: #697684;
    font-size: 11px;
}

QFrame#Core {
    background: #151d26;
    border: 1px solid #273341;
    border-radius: 6px;
}

QLabel#CoreName {
    color: #7d8996;
    font-size: 10px;
}

QLabel#CoreValue {
    color: #e6edf3;
    font-size: 13px;
    font-weight: 600;
}

QProgressBar {
    background: #202832;
    border: none;
    border-radius: 3px;
}

QProgressBar::chunk {
    background: #3498db;
    border-radius: 3px;
}

QScrollBar:vertical {
    background: #0b0f14;
    width: 9px;
}

QScrollBar::handle:vertical {
    background: #303b48;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""


def main():

    app = QApplication(sys.argv)

    app.setApplicationName("System Monitor")
    app.setStyleSheet(STYLE)

    window = SystemMonitor()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
