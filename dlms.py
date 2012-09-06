#!/usr/local/bin/python

from __future__ import print_function

import serial

class dlmsError(Exception):
  def __init__(self, reason):
    self.reason = reason
  def __str__(self):
    return repr(self.reason)

class dlms(object):
  # States
  CR_RECEIVED = 1
  NL_RECEIVED = 2
  STX_RECEIVED = 3
  ETX_RECEIVED = 4
  ERROR = 99

  # ASCII chars
  STX = 2 # start of text
  EXT = 3 # end of text
  NL = 10 # new line
  CR = 13 # carriage return
  SPACE = 32

  def __init__(self, serial_port = "/dev/cuaU3"):
    self.ser = serial.Serial(
      port = serial_port,
      baudrate = 300,
      bytesize = serial.SEVENBITS,
      parity = serial.PARITY_EVEN,
      timeout = 3.0)

  def query(self):
    self.ser.write("/?!\r\n")
    state = 0
    id = ""
    message_body = ""
    sum = 0
    while True:
      a = self.ser.read(1)
      if len(a) == 0:
        raise dlmsError("Rx Timeout")
      b = bytearray(a)[0]
      if state == 0:
        # Read ID string
        if b >= SPACE:
          id += a
        elif b == CR:
          state = CR_RECEIVED
        else:
          raise dlmsError(
              "Illegal char in ident 0x%02x" % b)
          state = ERROR
      elif state == CR_RECEIVED:
        # NL ending ID string
        if b != NL:
          raise dlmsError(
              "Ident has 0x%02x after CR" % b)
          state = ERROR
        else:
          state = NL_RECEIVED
      elif state == NL_RECEIVED:
        # STX
        if b != STX:
          raise dlmsError(
              "Expected STX not 0x%02x" % b)
          state = ERROR
        else:
          state = STX_RECEIVED
      elif state == STX_RECEIVED:
        # message body
        sum ^= b
        if b != ETX:
          message_body += a
        else:
          state = ETX_RECEIVED
      elif state == ETX_RECEIVED:
        # Checksum
        if sum != b:
          raise dlmsError(
              "Checksum Mismatch")
          state = ERROR
        else:
          return self.parse(id, message_body)
      elif state == ERROR:
        # Error, flush
        pass
    assert False

  def parse(self, id, message_body):
    l = list()
    l.append(id)
    l.append(dict())
    message_body = message_body.split("\r\n")
    if message_body[-1] != "":
      raise dlmsError(
          "Last data item lacks CRNL")
    if message_body[-2] != "!":
      raise dlmsError(
          "Last data item not '!'")
    for i in message_body[:-2]:
      if i[-1] != ")":
        raise dlmsError(
            "Last char of data item not ')'")
        return None
      i = i[:-1].split("(")
      j = i[1].split("*")
      l[1][i[0]] = j
    return l


if __name__ == "__main__":
  foo = dlms()

  a = foo.query()
  print("%16s: %s" % ("identifier", a[0]))
  print("")
  for i in a[1]:
    j = a[1][i]
    if len(j) == 2:
      print("%16s: %s [%s]" % (i, j[0], j[1]))
    else:
      print("%16s: %s" % (i, j[0]))
