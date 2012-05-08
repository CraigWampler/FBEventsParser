'''
Created on Apr 23, 2012

@author: Craig
'''

import optparse
import tempfile
import os
import re
from Pattern import *
from xml.dom.minidom import parse, parseString
import shutil
import webbrowser


optparser = optparse.OptionParser()
#optparser.add_option("-i", "--inputFolder", dest="inputFolder", default="../../../data/DF1MessagesAndChatsWithDF2/raw", help="Location of facebook session to parse")
optparser.add_option("-i", "--inputFolder", dest="inputFolder", default="../../../data/CompleteSession/raw", help="Location of facebook session to parse")
#optparser.add_option("-i", "--inputFolder", dest="inputFolder", default="../../../data/ChattingWithWes/raw", help="Location of facebook session to parse")
#optparser.add_option("-t", "--tmpFolder", dest="tmpFolder", default=tempfile.tempdir, help="Temporary Folder")

(opts, args) = optparser.parse_args()



class FBEventsParser(object):
    def __init__(self):
        """
        pattern is a Pattern - in future maybe we accept a list of patterns
        """
        self.eventRegex = re.compile(r"(\d+)_c.txt")
        self.hostRegex = re.compile(r"^Host: (.*)$", re.M)      
        self.urlRegex = re.compile('(GET|POST) http[s]?://(.*) HTTP.*')
        self.httpStatusRegex = re.compile(r"HTTP.*([0-9]{3,3}).*$", re.M)
        self.contentTypeRegex = re.compile(r"Content-Type: (.*/.*);{0,1}[ ]?.*$", re.M |re.I)
        self.sslConnectRegex = re.compile(r"CONNECT .* .*",re.M)
        self.patterns = []

    def addPattern(self, pattern):
        self.patterns.append(pattern)
    
    def getTimesFromXml(self, fXml):
        """
        fXml is the read in XML file. Need to parse it and get the ClientDoneRequest and ServerDoneRequest
        fields from the SessionTimers xml element
        """
        dom = parseString(fXml)
        sessionTimers = dom.getElementsByTagName('SessionTimers')[0]
        return (sessionTimers.getAttribute('ClientDoneRequest'),
                sessionTimers.getAttribute('ServerDoneResponse'))
    

    def splitHtmlConversation(self, clientReqData):
        splitPoint = '\r\n\r\n'
        indexOfSplit = clientReqData.find(splitPoint)
        if indexOfSplit == -1:
            splitPoint = '\n\n'
            indexOfSplit = clientReqData.find(splitPoint)
        
        return (clientReqData[:indexOfSplit], 
                clientReqData[indexOfSplit + len(splitPoint):])
    
    
    def parseClientReqIntoEvent(self, eventArgs, clientReqData, clientReqTime):
        (header, body) = self.splitHtmlConversation(clientReqData)
        eventArgs['host'] = self.hostRegex.findall(header)[0]
        eventArgs['url'] = self.urlRegex.findall(header)[0][1]
        eventArgs['clientReqTime'] = clientReqTime
        eventArgs['postContents'] = body if len(body) > 0 else None
        return eventArgs
        
    
    
    def parseServerRespIntoEvent(self, eventArgs, serverRespData, serverRespTime):
        (header, body) = self.splitHtmlConversation(serverRespData)      
        eventArgs['serverRespTime'] = serverRespTime   
        eventArgs['httpStatus'] = self.httpStatusRegex.findall(header)[0]
        ct = self.contentTypeRegex.findall(header)[0]
        ct = ct[:-1] if ct[-1] == ';' else ct  # strip trialing semicolon
        eventArgs['content_type'] = ct
        eventArgs['contents'] = body
        
        
        return eventArgs
    
    
    def process(self, pathToSessionizedEvents):
        for _, _, filenames in os.walk(opts.inputFolder):
            for filename in filenames:
                fMatch = self.eventRegex.match(filename)                
                # our regex only searches for the client request. If found, we consume the 
                # xml and server response. But in this part, the response and xml are not searched for
                if None != fMatch:                    
                    fPrefix = fMatch.group(1)
                    #if (fPrefix != '266'): continue
                    #print fPrefix
                    xmlFile = fPrefix + '_m.xml'
                    serverResponse = fPrefix + "_s.txt"
                    
                    fClient = None
                    fXml = None
                    fServer = None
                    
                    # Read all file contents, checking for errors
                    try:
                        fClient = open(os.path.join(opts.inputFolder,filename), 'rb').read()
                        fXml = open(os.path.join(opts.inputFolder,xmlFile)).read()
                        fServer = open(os.path.join(opts.inputFolder,serverResponse), 'rb').read()
                        
                        (clientReqTime, serverRespTime) = self.getTimesFromXml(fXml)
                        
                        # Make sure this isn't an SSL connect setup
                        if not self.sslConnectRegex.search(fClient):                        
                            eventArgs = {}
                            eventArgs = self.parseClientReqIntoEvent(eventArgs, fClient, clientReqTime)
                            eventArgs = self.parseServerRespIntoEvent(eventArgs, fServer, serverRespTime)
                            
                            for p in self.patterns:
                                p.processEvent(Event(**eventArgs))
                        
                    except IOError as e:
                        print e
                        # we couldn't open all three files, so ignore this --
                        # inf future, we could go on, if we could get the Xml and client file...
                        continue
                    except Exception:
                        continue
                    
                   
                    
                    


if __name__ == '__main__':
    tmpDir = tempfile.gettempdir()
    tmpDir = os.path.join(tmpDir, 'fb')
    
    if os.path.exists(tmpDir):
        shutil.rmtree(tmpDir)
    
    os.makedirs(tmpDir)
    
    output = Output(tmpDir)
    
    chatPat = ChatPattern(output)
    lp = LoginPattern(output)
    picPat = PictureUploadPattern(output)
    
    fbe = FBEventsParser()
    fbe.addPattern(chatPat)
    fbe.addPattern(picPat)
    fbe.addPattern(lp)
    fbe.process(opts.inputFolder)
    
    output.dumpToFile()
    
    url = os.path.join(tmpDir, 'index.html')
    print url
    webbrowser.open(url, new=1)