#!/usr/bin/env python

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtGui import QCursor
from PyQt4.QtGui import QPushButton
from PyQt4.QtCore import pyqtSlot, SIGNAL, SLOT, QThread
import sys
from babel import Locale
from subprocess import check_output

import google_say


class LanguagesMenu(QtGui.QMenu):
    def __init__(self, languages):
        super(LanguagesMenu, self).__init__()
        self.language = None
        self.languages = languages
        for lang in self.languages:
            action = self.addAction(Locale(lang).display_name.capitalize())
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
    def __init__(self, text, language):
        super(SpeakerThread, self).__init__()
        self.text = text
        self.language = language

    def run(self):
        google_say.start_speaking(self.text, self.language)
        # while True:
        #     print("background thread")
        #     self.sleep(1)


class MainWindow(QtGui.QWidget):
    def __init__(self, text, language):
        super(MainWindow, self).__init__()

        self.text = text
        self.language = language
        self.thread = None

        language_name = Locale(self.language).display_name.capitalize()
        self.setWindowTitle(language_name)

        layout = QtGui.QHBoxLayout()
        label = QtGui.QLabel(self)
        label.setText("Speaking in '%s'" % language_name)
        button = QPushButton("Stop")
        self.connect(button, SIGNAL("clicked()"), self, SLOT("__on_stop()"))
        layout.addWidget(label)
        layout.addWidget(button)
        self.setLayout(layout)

    def __del__(self):
        self.stop_speaking()
        super(MainWindow, self).__del__()

    def start_speaking(self):
        self.thread = SpeakerThread(self.text, self.language)
        self.thread.start()

    def stop_speaking(self):
        self.thread.terminate()

    def show(self):
        super(MainWindow, self).show()
        self.start_speaking()

    @pyqtSlot()
    def __on_stop(self):
        self.close()


def load_languages():
    return ["en", "uk", "ru"]


def load_selected_text():
    output_text = check_output(["cat", "sample.txt"])
    # output_text = check_output(["xclip", "--selection", "primary", "-out"])
    return output_text


def main():
    text = load_selected_text()
    print(text)
    languages = load_languages()
    app = QtGui.QApplication(sys.argv)
    menu = LanguagesMenu(languages)
    language = menu.pick_language()
    print("language after menu closed is %s" % language)
    if language is not None:
        main_window = MainWindow(text, language)
        main_window.show()
        sys.exit(app.exec_())
    else:
        print("Language not selected, quitting")


if __name__ == '__main__':
    main()