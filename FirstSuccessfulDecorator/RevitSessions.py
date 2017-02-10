# -*- coding: utf-8 -*-
import pickle
import csv
import time
import sys

from RevitObjects import BaseEvent, RevitSession

# the RevitSessionManager establishes a structure
# for the conversion of CSV Revit event data to a
# list of BaseEvent objects, as well as methods for
# pickling those events for later use
class RevitSessionManager(object):

    def __init__(self):
        # Revit sessions are stored under the key for USER,COMPUTER and FILE
        self.debug = False
        self.revitSessionsUnderKeys = {}
        self.loadTime = None
        self.rowCount = 0
        self.skippedRows = 0
        self.badRows = 0
        self.loadedRows = 0

        self.filterArg = None

    def extractSessions(self):
        # Extract all revit sessions from their keys in the dict
        # revitSessionsUnderKeys and place them in one list
        revitSessions = []
        for key in self.revitSessionsUnderKeys.keys():
            revitSessions.extend(self.revitSessionsUnderKeys.get(key))
        return revitSessions

    def callLastRevitSession(self,key):
        """Call the latest revit session under the key"""

        revitSessionsUnderKey = self.revitSessionsUnderKeys.get(key)

        # Raise an Exception if revitSessionsUnderKey is None, this means the key is not in the dict
        # for this USER,COMPUTER and FILEPATH
        if revitSessionsUnderKey is None:
            raise Exception("Key for this User,Computer and FilePath not in revitSessionsUnderKey")
            return

        revitSession = revitSessionsUnderKey[-1]

        return revitSession

    def addRevitSessionToDict(self,key,revitSession):

        # Add the session to the dict under this key for USER,COMPUTER and FILEPATH
        self.revitSessionsUnderKeys[key].append(revitSession)

    def selectRows(func):
        """Only lets rows pass through that have the arg in the row (if the arg is specified and is not None), the intention being able to skip rows that don't contain certain arguements to make testing quicker"""
        #TODO write code for mulitple args

        def wrapper(self,row,arg = None):

            if arg is not None:
                stampRaw, stampReadable, filePath, siteName, projectName, fileName, appName, eventType, userName, compName = row
                inputs = [stampRaw, stampReadable, filePath, siteName, projectName, fileName, appName, eventType, userName, compName]
                print arg
                if arg in inputs:

                    return func(self,row)

                else:
                    newRow = ["null","null","null","null","null","null","null","null","null","null"]
                    print newRow
                    return func(self,newRow)

            return  func(self,row)

        return wrapper

    @selectRows
    def readDataRow(self,row,arg = None):

        # create a generic event from the row data
        event = None
        try:
          event = BaseEvent(row)
        except:
          self.badRows += 1
          self.skippedRows += 1
          return False

        if event is None:
          self.skippedRows += 1
          return False

        # check that the event has all required attributes
        for att in ['type','timeStamp','filePath','userName','compName']:
          if not hasattr(event,att):
            self.skippedRows += 1
            return False

        # Make sure that there is a key in the dict for this revitSession
        # this key will store a list of the Revit Sessions which have OCCURED UNDER this USER,COMPUTER and FILEPATH

        if not event.key in self.revitSessionsUnderKeys.keys():

            # Key for this USER,COMPUTER and FILEPATH not in revitSessionsUnderKeys dict
            # so create a new key for this USER,COMPUTER and FILEPATH
            # this key will store a list of Revit sessions which have OCCURED UNDER this USER,COMPUTER and FILEPATH

            self.revitSessionsUnderKeys[event.key] = []

        # Call the last Revit Session, if one is not there create one
        try:

            session = self.callLastRevitSession(event.key)

            if (session.timestampStart is not None) and (session.timestampEnd is not None):
                # The last session has already been opened and closed, so create a new one

                newRevitSession = RevitSession(event)
                # Get the number of Revit Sessions under this Key, base the session count number on this
                newRevitSession.sessionCount = int(len(self.revitSessionsUnderKeys.get(event.key)))

                newRevitSession.addEvent(event)

                self.addRevitSessionToDict(event.key,newRevitSession)
            else:
                # The last session has not be closed, so add events to it until it is closed
                session.addEvent(event)

                self.addRevitSessionToDict(event.key,session)

        except:
            # No Revit Sessions under this key yet so create one, the first one
            newRevitSession = RevitSession(event)
            # Get the number of Revit Sessions under this Key, base the session count number on this
            newRevitSession.sessionCount = int(len(self.revitSessionsUnderKeys.get(event.key)))

            newRevitSession.addEvent(event)

            self.addRevitSessionToDict(event.key,newRevitSession)

        self.loadedRows += 1

    def loadCSV(self,path,hasHeader):

      startTime = time.time()
      firstRow = True
      print("--> loading CSV @ {0}".format(path))

      with open(path,"r") as revitData:

          revitDataReader = csv.reader(revitData)

          for row in revitDataReader:

              # skip the first row if there is a header
              if firstRow and hasHeader:
                  firstRow = False
                  continue

              self.readDataRow(row,self.filterArg)
              self.rowCount += 1
              # if self.rowCount % 1000 == 0:
              #sys.stdout.write("\r... rows loaded: "+str(self.rowCount));
              sys.stdout.flush()
      sys.stdout.write("\r... rows loaded: "+str(self.rowCount));
      sys.stdout.flush()
      self.loadTime = time.time() - startTime
      revitData.close()

    def report(self):
        print ("--- read %s rows ---" % (self.rowCount))
        template = "--- loaded %s rows (skipped %s) in %s seconds ---"

        print(template % (self.loadedRows,self.skippedRows,self.loadTime))
    def saveCompleteEventsToCSV(self,path):
        # save all non-truncated events to CSV
        extracted = self.extractSessions()
        with open(path,'wb') as csvfile:
            eventWriter = csv.writer(csvfile, delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
            eventWriter.writerow(['session','path','username','computer','timestamp','length','type'])
            # TODO this code assumes that every session has a opened and closing events this is not always correct!!!
            for session in extracted:
              eventWriter.writerow([session.key,session.filePath,session.userName,session.compName,session.timestampStart,None,'opened'])
              # print session.key
              for event in session.pairedEvents:
                # print event.type
                eventWriter.writerow([session.key,session.filePath,session.userName,session.compName,event.timestampStart,event.length,event.type])
              eventWriter.writerow([session.key,session.filePath,session.userName,session.compName,session.timestampEnd,None,'closing'])
        return True

    def saveSessionsToCSV(self,path):
        extracted = self.extractSessions()
        with open(path,'wb') as csvfile:
            sessionWriter = csv.writer(csvfile, delimiter=',',quotechar='"',quoting=csv.QUOTE_MINIMAL)
            sessionWriter.writerow(['session','path','username','computer','timestamp','length','crashed','closed'])
            for session in extracted:
                length = None
                if hasattr(session,'timestampEnd') and hasattr(session,'timestampStart'):
                    if not (session.timestampEnd is None or session.timestampStart is None):
                      length = session.timestampEnd - session.timestampStart
                # print dir(session)
                sessionWriter.writerow([session.key,session.filePath,session.userName,session.compName,session.timestampStart,length,session.crashed,session.closed])


    def pickle(self,path):
        # save extracted revitSessions to a pickled
        # Python object in a text file at the path
        # provided
        revitSessions = self.extractSessions()
        with open(path,'wb') as pickle_out:
            pickle.dump(revitSessions,pickle_out)
            pickle_out.close()
