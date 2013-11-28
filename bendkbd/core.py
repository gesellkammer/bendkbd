# -*- coding: utf-8 -*-
from __future__ import division
import rtmidi2
from rtmidi2 import splitchannel as _splitchannel
from rtmidi2 import cents2pitchbend, pitchbend2cents

import fnmatch as _fnmatch
import time as _time
import liblo

OSCSEND = liblo.Address('localhost', 7778)

def inports_matching(wildcard):
    inports = rtmidi2.get_in_ports()
    matches = [port for port in inports if _fnmatch.fnmatch(port, wildcard)]
    return matches

class MidiMatchingError(BaseException):
    pass

class Bendkbd(object):
    def __init__(self, receivefrom=None, name='Bendkbd', polychannel=True, sendosc=False, debug=False):
        """
        receivefrom: None to create a virtual port
                     A wildcard to connect to specific devices
                     A number to listen to all devices on a specific channel (0-15)
        """
        self._debug = debug
        self.name = name
        if receivefrom is None:
            midiin = rtmidi2.MidiIn()
            midiin.open_virtual_port(name)
            self.enabled_sources = {name:True}
            self._midiin_close = midiin.close_port
            listentochannel = -1 # --> listen to all channels
            if self._debug:
                print "Listening in virtual port {name} to all channels".format(**locals())
        elif isinstance(receivefrom, int) and 0 <= receivefrom < 16:
            midiin = rtmidi2.MidiIn()
            midiin.open_virtual_port(name)
            self.enabled_sources = {name:True}
            listentochannel = receivefrom
            if self._debug:
                print "Listening to all sources at channel {listentochannel}".format(**locals())
            self._midiin_close = midiin.close_port

        elif isinstance(receivefrom, basestring):
            if "*" in receivefrom or "?" in receivefrom:
                if not inports_matching(receivefrom):
                    raise MidiMatchingError("No ports found matching the given wildcard")
                midiin = rtmidi2.MidiInMulti()
                if self._debug:
                    print "opening ports matching ", receivefrom
                ports_matched = midiin.ports_matching(receivefrom)

                midiin.open_ports(receivefrom, exclude=self.name)
                self._midiin_close = midiin.close_ports
                listentochannel = -1
                self.enabled_sources = {midiin.ports[port]:True for port in midiin.get_openports()}
                if self._debug:
                    print "Listening to sources: ", self.enabled_ports.keys()
            else:
                midiin = rtmidi2.MidiIn()
                midiin.open_port(receivefrom)
                self.enabled_sources = {receivefrom:True}
                listentochannel = -1
                self._midiin_close = midiin.close_port
                if self._debug:
                    print "Listening to source: ", receivefrom
        else:
            raise ValueError("receivefrom must be either None or a midichannel or a wildcard to match sources")
        self.midiin = midiin
        self.channel = listentochannel
        self.notesdown = [0] * 128
        self.assigned_event = [None] * 128
        self._pitchbends = [0] * 16

        self.midiout = rtmidi2.MidiOut()
        self.midiout.open_virtual_port("Bendkbd")
        self.midiin.callback = self.callback
        self._midiin_counter = 0

        self._current_bend = 0
        self._current_channel = 0
        self._global_pitchbend_cents = 0
        self._polychannel = polychannel
        self._sendbend_period_sec = 5
        self._sendbend_lasttime = 0
        self.send_bends()
        self._pitchoffset_cents = 0

        def pitchoffset(chan, cc, value):
            self._pitchoffset_cents = value/127*99
            self.dispatch('pitchoffset', (self._pitchoffset_cents,))

        def pedal(chan, cc, value):
            for i in xrange(16):
                self.midiout.send_cc(i, 64, value)

        self.cchandlers = {
            1: pitchoffset,
            64: pedal
        }

        if sendosc:
            self._initosc()
        self._sendosc = sendosc
        self.eventhooks = {
            'bendchanged': []
        }

    def dispatch(self, hookname, args):
        funcs = self.eventhooks.get(hookname)
        if funcs:
            for func in funcs:
                func(*args)

    def _initosc(self):
        self.oscserver = liblo.Server()
        self._sendosc = True

    def close(self):
        self.midiin.callback = None
        self._midiin_close()
        self.midiout.close_port()

    def noteon(self, physicalnote, midinote, velocity):
        """
        midinote: an integer or fractional midinote
        """
        if self._polychannel:
            channel = self._bend_to_channel(midinote%1)
            midinote = int(midinote)
            self.midiout.send_noteon(channel, midinote, velocity)
            self.keeptrack(physicalnote, midinote, channel)
        else:
            XXX
        if self._sendosc:
            self.oscserver.send(OSCSEND, '/noteon', physicalnote, midinote, velocity)

    def keeptrack(self, physicalnote, midinote, channel):
        prev = self.assigned_event[physicalnote]
        if prev:
            prevnote, prevchan = prev
            self.midiout.send_noteoff(prevchan, prevnote)
        self.assigned_event[physicalnote] = (midinote, channel)

    def noteoff(self, physicalnote):
        midinote, channel = self.assigned_event[physicalnote]
        self.midiout.send_noteoff(channel, midinote)
        self.assigned_event[midinote] = None
        if self._sendosc:
            self.oscserver.send(OSCSEND, '/noteoff', physicalnote, midinote)
    
    def callback(self, msg, time):
        msgtype, channel = _splitchannel(msg[0])
        if self._debug:
            print msgtype, channel, msg[1], msg[2]

        if not(self.channel == -1 or self.channel == channel):
            return

        if self._polychannel:
            now = _time.time()
            if now - self._sendbend_lasttime > self._sendbend_period_sec:
                if self._debug:
                    print "sending bends"
                self.send_bends(now)

        ###########
        # NOTEOFF #
        ###########
        if   msgtype == 128:
            midinote = msg[1]
            self.notesdown[midinote] = 0
            if midinote >= 29:  # <------- F1
                self.noteoff(midinote)
            else:
                self._update_bend()
        ############
        #  NOTEON  #
        ############
        elif msgtype == 144:
            midinote = msg[1]
            vel = msg[2]
            if vel == 0:
                self.notesdown[midinote] = 0
                if midinote >= 29:  # <--- F1
                    self.noteoff(midinote)
                else:
                    self._update_bend()
            else:
                self.notesdown[midinote] = 1
                if midinote < 29:   # <--- F1
                    self._update_bend()
                else:
                    n = midinote+self._current_bend+self._pitchoffset_cents/100.
                    self.noteon(midinote, n, vel)
                    self.dispatch('noteon', (midinote, n, vel))
                    #for func in self.eventhooks['noteon']:
                    #    func(midinote, n, vel)
        elif msgtype == 224: # pitchbend
            pitchbend = msg[1] + (msg[2] << 7)
            self._global_pitchbend_cents = pitchbend2cents(pitchbend, 100)
            if self._debug:
                print "global pitchbend (pitchbend, cents): ", pitchbend, self._global_pitchbend_cents
            self.send_bends()
        elif msgtype == 176:
            # route CC to the channel being pressed
            cc = msg[1]
            chan = self._bend_to_channel(self._current_bend)
            func = self.cchandlers.get(cc)
            if func:
                func(chan, cc, msg[2])
            else:
                self.midiout.send_raw(chan+176, cc, msg[2])
        else:
            chan = self._bend_to_channel(self._current_bend)
            self.midiout.send_message(chan+msgtype, msg[1], msg[2])

    def send_bends(self, timestamp=None):
        for channel in range(16):
            cents = round(channel * 6.25) + self._global_pitchbend_cents
            pitchbend = cents2pitchbend(cents, 200)
            self.midiout.send_pitchbend(channel, pitchbend)
            # self._pitchbends[channel] = pitchbend
            self._sendbend_lasttime = timestamp or _time.time()

    def _update_bend(self):
        notesdown = self.notesdown
        # A0=21, Eb1=27
        #cents = 10*notesdown[21] + 20*notesdown[22] + 40*notesdown[23] + 80*notesdown[24] + 2*notesdown[25] + 4*notesdown[26] + 6*notesdown[27] + 8*notesdown[28]
        cents = 1*notesdown[21] + 2*notesdown[22] + 3*notesdown[23] + 4*notesdown[24] + 5*notesdown[25] + 6*notesdown[26] + 7*notesdown[27]
        cents *= 6.25
        cents = min(cents, 99)
        if self._debug:
            print cents
        self._current_bend = cents/100.
        self.dispatch('bendchanged', (self._current_bend,))
        #for func in self.eventhooks.get('bendchanged'):
        #    func(self._current_bend)

    def _bend_to_channel(self, bend):
        return min(15, round(bend*100 / 6.25))
