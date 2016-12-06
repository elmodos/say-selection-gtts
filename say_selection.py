#!/usr/bin/env python

import sys
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtGui import QCursor
from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import pyqtSlot, SIGNAL, SLOT
from babel import Locale
from subprocess import check_output

# subdir
from elmodosgoogletts import google_say


class LanguagesMenu(QtGui.QMenu):
    def __init__(self, languages):
        super(LanguagesMenu, self).__init__()
        self.language = None
        self.languages = languages
        for lang in self.languages:
            action = self.addAction(Locale(lang[0]).display_name.capitalize())
            action.language = lang
            self.connect(action, SIGNAL("triggered()"), self, SLOT("__on_language_selected()"))

    def pick_language(self):
        self.exec_(QCursor.pos())
        return self.language

    @pyqtSlot()
    def __on_language_selected(self):
        action = self.sender()
        self.language = action.language


class SpeakerThread(QtCore.QThread):
    def __init__(self, text, language, speed):
        super(SpeakerThread, self).__init__()
        self.text = text
        self.language = language
        self.speed = speed
        self.signal_cheech_finished = QtCore.SIGNAL("signal")

    def run(self):
        google_say.start_speaking(self.text, self.language, self.speed)
        self.emit(self.signal_cheech_finished)

    def terminate(self):
        google_say.stop_speaking()
        super(SpeakerThread, self).terminate()


class MainWindow(QtGui.QWidget):
    def __init__(self, text, language, speed):
        super(MainWindow, self).__init__()

        # storing values for future use
        self.text = text
        self.language = language
        self.speed = speed
        self.thread = None

        # converting language codes into display names like "en" to "English"
        language_name = Locale(self.language).display_name.capitalize()

        self.setWindowTitle(language_name)

        # horizontal layout
        layout = QtGui.QHBoxLayout()

        # label
        label = QtGui.QLabel(self)
        label.setText("Speaking in '%s'" % language_name)

        # button
        button = QPushButton("Stop")
        self.connect(button, SIGNAL("clicked()"), self, SLOT("__on_stop()"))

        # show up
        layout.addWidget(label)
        layout.addWidget(button)
        self.setLayout(layout)

    def closeEvent(self, QCloseEvent):
        self.stop_speaking()
        QCloseEvent.accept()

    def start_speaking(self):
        self.thread = SpeakerThread(self.text, self.language, self.speed)
        self.connect(self.thread, self.thread.signal_cheech_finished, self, SLOT("__on_speech_finished()"))
        self.thread.start()

    def stop_speaking(self):
        self.thread.terminate()

    def show(self):
        super(MainWindow, self).show()
        self.start_speaking()

    @pyqtSlot()
    def __on_stop(self):
        # will trigger to kill reader thread
        self.close()

    @pyqtSlot()
    def __on_speech_finished(self):
        print("speech ended")
        self.close()


def load_languages():
    # languages.list file should containd language codes in ISO 639-1
    with open("languages.list") as f:
        langs = f.readlines()
    return [lang.strip("\n").split(" ") for lang in langs]


def load_selected_text():
    # calling xclip to get current selected text
    output_text = check_output(["xclip", "--selection", "primary", "-out"])
    # output_text = check_output(["cat", "sample.txt"])
    return output_text


def lock_to_single_process():
    try:
        import socket
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind("\0com.github.say-selection-gtts")
        return s
    except socket.error:
        print("Another instance appears to be running")
        return None


def main():
    # preliminary data
    text = load_selected_text()
    languages = load_languages()

    # QApplication should be instantinated before showing QMenu
    app = QtGui.QApplication(sys.argv)

    # asking for language
    menu = LanguagesMenu(languages)
    language = menu.pick_language()

    if language is not None:
        language_code = language[0]
        speed = language[1] if len(language) >= 2 else "1.0"
        main_window = MainWindow(text=text, language=language_code, speed=speed)
        main_window.show()
        sys.exit(app.exec_())
    else:
        # menu can be dismissed with click outside or Esc key
        print("Language not selected, quitting")


if __name__ == '__main__':
    s = lock_to_single_process()
    if s is not None:
        main()
    s.close()
