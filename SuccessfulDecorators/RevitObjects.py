# -*- coding: utf-8 -*-

import hashlib

def removeNonDigits(s):
    """Removes non digits from a string and returns a long of those non digits"""
    n = 0
    for c in s:
        if c.isdigit():
            # Multiply n times 10 to produce the next placeholder!
            n = n * 10 + int(c)
    return n

class RevitSession(object):

    def __init__(self,event):

        # TODO If the event is not an opened event, then its truncated session

        # The number of sessions under a certain key
        # is incremented each time a session is created
        self.sessionCount = 0

        self.key      = event.key
        self.filePath = event.filePath
        self.userName = event.userName
        self.compName = event.compName

        # store active event
        self.activeSync  = None
        self.activePrint = None

        # By default when a Session is created it is closed!
        # self.closed Flag is changed through addOpened and addClosing events
        self.closed = True

        self.pairedEvents = []

        # A simple event log with names
        # Its handy to keep a log of event types occurances for testing
        self.eventsLog = []

        # Set when opened event occurs
        self.timestampStart = None
        # Set when crash or closed event occurs
        # QUESTION for Andrew is it fair to assume that session closes on CrashEvent?
        self.timestampEnd = None
        # Will be set to True if session crashed
        self.crashed = False

    def isRevitSessionTruncated():

        if (self.timestampStart is not None) and (self.timestampEnd is not None):

            return True

        else:
            return False

    def addEvent(self,event):
        # Add an event to this RevitSession
        if event.type == "opened":
          self.addOpened(event)

        if event.type == "synching":
            if not self.activeSync is None:
                # Make the PairedEvent the same event with zero length
                newPair = PairedEvent(self.activeSync,self.activeSync)
                self.pairedEvents.append(newPair)
            self.activeSync = event

            self.eventsLog.append('synching')

        if event.type == "printing":
            if not self.activePrint is None:
                # Make the PairedEvent the same event with zero length
              newPair = PairedEvent(self.activePrint,self.activePrint)
              self.pairedEvents.append(newPair)
            self.activePrint = event

            self.eventsLog.append('printing')

        if event.type == "synched":
            newPair = None
            if self.activeSync is None:
              newPair = PairedEvent(event,event)
            else:
              newPair = PairedEvent(self.activeSync,event)
            self.pairedEvents.append(newPair)
            self.activeSync = None

            self.eventsLog.append('synched')

        if event.type == "printed":
            newPair = None
            if self.activePrint is None:
                # Make the PairedEvent the same event with zero length
              newPair = PairedEvent(event,event)
            else:
              newPair = PairedEvent(self.activePrint,event)
            self.pairedEvents.append(newPair)
            self.activePrint = None

            self.eventsLog.append('printed')

        if event.type == "crash":
            self.addCrash(event)

        if event.type == "closing":
          self.addClosing(event)

    def addCrash(self,event):

        if self.closed == False:

            self.timestampEnd = event.timeStamp
            ##TODO after a Crash should the session be closed? I am assuming that the crash closes the RevitSession
            # so I close it
            self.closed = True
            # Set session crashed to True so that we know that the session crashed
            self.crashed = True

        else:
            if hasattr(self,'debug') and self.debug:
                print "A crash event occured when the session was closed"

        self.eventsLog.append('crash')

    def addClosing(self,event):

        if self.closed == False:

            # Add close timestamp to the session
            self.timestampEnd = event.timeStamp

            self.closed = True
            # Set closed to True so if events are added this will be a truncated session
        else:
            if hasattr(self,'debug') and self.debug:
                print "A session is closing that is already closed!"

        self.eventsLog.append('closing')

    def addOpened(self,event):

        if self.closed == True:

            self.closed = False
            # Set closed to False so events can be added without this being a truncated session
            # Add open timestamp to the session
            self.timestampStart = event.timeStamp

        else:
            if hasattr(self,'debug') and self.debug:
                print "A session is being opened that is not yet closed!"

        self.eventsLog.append('opened')

# this is a generic Revit event,
# constructed from a CSV row from
# a report of Revit events
class BaseEvent(object):

    def __init__(self,vals):

      stampRaw, stampReadable, filePath, siteName, projectName, fileName, appName, eventType, userName, compName = vals

      # filePath, userName, and compName are used
      # to uniquely identify which Revit session an
      # event belongs to; if any of these three do
      # not exist, there is no way to uniquely identify
      # the revit session and so the event is not useful

        # fail early
      if str(filePath) == "null":
        raise Exception("filePath missing, cannot verify event")
      if str(userName) == "null":
        raise Exception("userName missing, cannot verify event")
      if str(compName) == "null":
        raise Exception("compName missing, cannot verify event")

      self.filePath = filePath
      self.userName = userName
      self.compName = compName

      self.type = str(eventType)

      # Current UNX timestamp
      self.timeStamp = removeNonDigits(stampRaw)

      hashValue = str(filePath) + str(userName)+ str(compName)
      m = hashlib.md5()
      m.update(hashValue)
      self.key = m.hexdigest()

# this is a paired Revit event
# constructed from a start and end BaseEvent
# note the start and end event can be the
# same event, which effectively makes the
# event have a 0 length
class PairedEvent(object):
    def __init__(self,startEvent,endEvent):
      self.key  = startEvent.key
      self.type = startEvent.type
      self.filePath = startEvent.filePath
      self.userName = startEvent.userName
      self.compName = startEvent.compName
      self.timestampStart = int(startEvent.timeStamp)
      self.timestampEnd   = int(endEvent.timeStamp)
      self.length = self.timestampEnd - self.timestampStart
