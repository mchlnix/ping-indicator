# Removes log functionality again
# Now writes avg ping to log
# Now keeps track of sent and lost pings and writes it to .config/pingindicator/ping.log
# Now resets instantly
# Now resets the indicator icon as well
# Removed the string representation
# Added Min and Max information
# Fixed stderr leaking into terminal
# Now only prints used timeout, when one was given via commandline argument
# Code now fits on 80 character terminals
# Now updates the menu even when timeouts happen
import os
from collections import deque
from math import ceil
from subprocess import CalledProcessError, STDOUT, check_output
from sys import argv, exit
from time import strftime

from PySide2.QtCore import QRect, QSize, QTimer
from PySide2.QtGui import QColor, QIcon, QImage, QPainter, QPixmap
from PySide2.QtWidgets import QApplication, QMainWindow, QMenu, QSystemTrayIcon

timeout = 2000  # in ms
packet_amount = 22  # also width of indicator icon in pixels
min_scale = 1.0 / 100  # in 1/ms
indicator_image_height = 22  # in unity
mid_thres = 2 / 3.0  # of timeout
good_thres = 1 / 3.0  # of timeout


def avg(sequence):
    return int(sum(sequence) / len(sequence))


class PingIndicator(QMainWindow):
    def __init__(self, address="8.8.8.8"):
        super(PingIndicator, self).__init__()

        self.icon = QImage(QSize(packet_amount, indicator_image_height), QImage.Format_RGBA8888)

        self.online = True

        self.destination = address

        self.packets = deque([], packet_amount)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip(address)

        self.update_timer = QTimer(self)
        self.update_timer.setInterval(int(timeout * 1.05))
        self.update_timer.timeout.connect(self.update_indicator)

        self.update_timer.start()

        self.last_time_online = strftime("%H:%M:%S")

        self.reset()

    def update_icon(self):
        self.icon.fill(QColor(0, 0, 0, 0))

        painter = QPainter(self.icon)

        (width, height) = self.icon.size().toTuple()
        width -= 1
        height -= 1

        painter.fillRect(QRect(0, 0, width, height), QColor(0, 0, 0, 0))

        try:
            scale = min(1.0 / max(self.packets), min_scale)
        except ValueError:
            scale = min_scale

        for index, ping in enumerate(list(reversed(self.packets))):
            x = ping / float(timeout)

            color = QColor(
                int(-324 * x ** 2 + 390 * x + 138),  # R
                int(-480 * x ** 2 + 254 * x + 226),  # G
                int(-212 * x ** 2 + 160 * x + 52),  # B
                255,
            )

            scaled_height = ceil(scale * ping * height)

            painter.fillRect(QRect(width - index, height - scaled_height, 1, scaled_height), color)

        self.tray_icon.setIcon(QIcon(QPixmap(self.icon)))
        self.tray_icon.show()

    def update_indicator(self):
        try:
            new_env = dict(os.environ)
            new_env['LC_ALL'] = 'C'

            output = check_output(
                ["ping", "-c", "1", "-W", str(timeout / 1000), self.destination], stderr=STDOUT, env=new_env,
            ).decode(
                "ascii"
            )  # man ping

            for line in output.splitlines():
                pos = line.find("time=")
                if pos != -1:
                    new_label = line[pos + 5: -3].center(4)
                    self.packets.append(round(float(new_label), 2))

                    if not self.online:
                        self.online = True
                        self.tray_icon.contextMenu().actions()[0].setText("Last disconnect: " + self.last_time_online)
                    else:
                        self.last_time_online = strftime("%H:%M:%S")

                    break
            else:
                raise ValueError("No time could be parsed.")

        except CalledProcessError as cpe:
            self.packets.append(timeout)

            if self.online:
                self.online = False
                self.tray_icon.contextMenu().actions()[0].setText("Offline since: " + strftime("%H:%M:%S"))

            print(cpe)
        except KeyboardInterrupt:
            self.close()

        self.update_icon()
        self.update_menu()

        return True

    def reset(self):
        self.packets.clear()
        self.update_icon()

        menu = QMenu()

        menu.addAction("Online since: " + strftime("%H:%M:%S"))
        menu.addAction("Lost: -, Avg: -")
        menu.addAction("Max: -, Min: -")
        menu.addSeparator()
        menu.addAction("Reset").triggered.connect(self.reset)
        menu.addAction("Quit").triggered.connect(self.close)

        self.tray_icon.setContextMenu(menu)

    def update_menu(self):
        self.tray_icon.contextMenu().actions()[1].setText(
            "Lost: %d, Avg: %dms" % (self.packets.count(timeout), avg(self.packets)),
        )
        self.tray_icon.contextMenu().actions()[2].setText(
            "Max: %dms, Min: %dms" % (max(self.packets), min(self.packets)),
        )


def print_help():
    print("pingindicator [-h,--help] [-a address] [-n name]")
    print("example: pingindicator -a 8.8.8.8 -n 'Google DNS'")


if __name__ == "__main__":
    address = "8.8.8.8"
    name = "Internet"
    skip_next = True

    for index, arg in enumerate(argv):
        if skip_next:
            skip_next = False
            continue

        if arg == "-n":
            name = argv[index + 1]
            skip_next = True
        elif arg == "-a":
            address = argv[index + 1]
            skip_next = True
        elif arg in ["-h", "--help"]:
            print_help()
            exit(0)
        else:
            print_help()
            exit(1)

    app = QApplication()
    ping_indicator = PingIndicator(address)
    app.exec_()
