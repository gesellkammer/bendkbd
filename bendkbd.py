#!/usr/bin/env python
import sys
import time
from PySide.QtCore import *
from PySide.QtGui  import *
import liblo
from bendkbd import core
from bendkbd.pitchconv import m2f, m2n

global qt_app

class GUI(QWidget):
    def __init__(self):
        # Initialize the object as a QWidget and
        # set its title and minimum width
        QWidget.__init__(self)
        self.keyb = core.Bendkbd("*")
        self.A4 = 442
        self.setup_widgets()
        
        self.register('bendchanged', self.set_bend)
        self.register('noteon', self.noteon)
        self.register('pitchoffset', lambda pitchoffset: self.pitchoffset.setText("%d cents" % int(pitchoffset)))

    def register(self, hookname, func):
        self.keyb.eventhooks.setdefault(hookname, []).append(func)

    def set_bend(self, bend):
        bendstr = str(int(bend*100))
        self.bend.setText(bendstr)  

    def noteon(self, physicalnote, midinote, velocity):
        s = "%s Hz (%s)" % (str(int(m2f(midinote, self.A4))).rjust(3), m2n(midinote))
        self.freq.setText(s)

    def setup_widgets(self):
        self.setWindowTitle('bendkbd')
        self.setMinimumWidth(500)
 
        # Create the QVBoxLayout that lays out the whole form
        self.layout = QVBoxLayout()
 
        # Create the form layout that manages the labeled controls
        self.form_layout = QFormLayout()
        self.form_layout.setFormAlignment(Qt.AlignTop | Qt.AlignLeft)

        font1 = QFont()
        font1.setFamily("Helvetica")
        font1.setPointSize(24)

        fontfixed = QFont()
        fontfixed.setFamily("Courier New")
        fontfixed.setPointSize(24)

        fontsmall = QFont()
        fontsmall.setFamily("Helvetica")
        fontsmall.setPointSize(12)

        palette1 = QPalette()
        palette1.setColor(QPalette.Foreground, "#2095F0")

        def createcontrol(value=0, font=None):
            font = font or fontfixed
            ctrl = QLabel(str(value), self)
            ctrl.setFont(font)
            ctrl.setPalette(palette1)
            return ctrl

        def statictext(text):
            t = QLabel(text, self)
            t.setFont(font1)
            return t

        self.bend = createcontrol()
        self.freq = createcontrol()
        self.pitchoffset = createcontrol()

        staticbend = statictext('BEND ')
        staticconn = statictext('SOURCES ')
        staticfreq = statictext('FREQ ')
        staticoffset = statictext('OFFSET')

        enabled_sources = [source for source, enabled in self.keyb.enabled_sources.iteritems() if enabled]
        enabled_sources_text = ", ".join(enabled_sources)
        connectedlabel = QLabel(enabled_sources_text, self)
        connectedlabel.setFont(fontsmall)
        connectedlabel.setPalette(palette1)

        self.form_layout.addRow(staticconn, connectedlabel)
        self.form_layout.addRow(staticbend, self.bend)
        self.form_layout.addRow(staticoffset, self.pitchoffset)
        self.form_layout.addRow(staticfreq, self.freq)
        
        # Add the form layout to the main VBox layout
        self.layout.addLayout(self.form_layout)
 
        # Add stretch to separate the form layout from the button
        self.layout.addStretch(1)
 
        # Create a horizontal box layout to hold the button
        self.button_box = QHBoxLayout()
 
        # Add stretch to push the button to the far right
 
        self.quit_button = QPushButton('Quit', self)
        self.quit_button.clicked.connect(QCoreApplication.instance().quit)

        # Add it to the button box
        # self.button_box.addWidget(console_button)

        self.button_box.addStretch(1)
        self.button_box.addWidget(self.quit_button)

        # Add the button box to the bottom of the main VBox layout
        self.layout.addLayout(self.button_box)
 
        # Set the VBox layout as the window's main layout
        self.setLayout(self.layout)

    def action_console(self):
        pass

    def run(self):
        # Show the form
        print "running!"
        
        self.show()
        # Run the qt application
        qt_app.exec_()
 
def startgui():
    # Create an instance of the application window and run it
    global qt_app
    qt_app = QApplication(sys.argv)
    app = GUI()
    app.run()
    time.sleep(0.2)

if __name__ == '__main__':
    startgui()