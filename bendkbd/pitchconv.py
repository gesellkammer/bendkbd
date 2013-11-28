import math

def f2m(freq, A4=440):
    """
    convert a frequency in Hz to a midi-note
    """
    return 12 * math.log(freq/A4, 2) + 69

def m2f(midinote, A4=440):
    return 2**((midinote - 69)/12.) * A4

_notes = '-1C -1C# -1D -1D# -1E -1F -1F# -1G -1G# -1A -1A# -1B 0C 0C# 0D 0D# 0E 0F 0F# 0G 0G# 0A 0A# 0B 1C 1C# 1D 1D# 1E 1F 1F# 1G 1G# 1A 1A# 1B 2C 2C# 2D 2D# 2E 2F 2F# 2G 2G# 2A 2A# 2B 3C 3C# 3D 3D# 3E 3F 3F# 3G 3G# 3A 3A# 3B 4C 4C# 4D 4D# 4E 4F 4F# 4G 4G# 4A 4A# 4B 5C 5C# 5D 5D# 5E 5F 5F# 5G 5G# 5A 5A# 5B 6C 6C# 6D 6D# 6E 6F 6F# 6G 6G# 6A 6A# 6B 7C 7C# 7D 7D# 7E 7F 7F# 7G 7G# 7A 7A# 7B 8C 8C# 8D 8D# 8E 8F 8F# 8G 8G# 8A 8A# 8B 9C 9C# 9D 9D# 9E 9F 9F#'.split()

def m2n(midinote):
    base = int(midinote)
    rest = midinote - base
    if rest > 0.5:
        base += 1
        rest = rest - 1
    rest = int(rest * 100 + 0.5)
    if rest == 0:
        reststr = ""  
    elif rest == 50:
        reststr = '+'
    elif rest == -50:
        reststr = '-'
    elif rest > 0:
        reststr = '+%d' % rest
    elif rest < 0:
        reststr = '-%d' % abs(rest)
    return _notes[base]+reststr
    
def f2n(freq):
    midinote = f2m(freq)
    note = m2n(midinote)
    
def n2m(note):
    raise NotImplemented
    
def n2f(note):
    m = n2m(note)
    f = m2f(m)
    return f  
    
        
