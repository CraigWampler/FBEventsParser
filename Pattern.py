'''
Created on Apr 23, 2012

@author: Craig
'''
from string import Template
import os
import re
import urlparse
import urllib
import json

# styles from http://coding.smashingmagazine.com/2008/08/13/top-10-css-table-designs/
class Output(object):
    """
    Generates html
    """
    styleCss = """
    
#hor-zebra
{
    font-family: "Lucida Sans Unicode", "Lucida Grande", Sans-Serif;
    font-size: 12px;
    margin: 45px;
    /*width: 480px;*/
    text-align: left;
    border-collapse: collapse;
}
#hor-zebra h1
{
    font-size: 24px;
    font-weight: normal;
}
#hor-zebra th
{
    font-size: 14px;
    font-weight: normal;
    padding: 10px 8px;
    color: #039;
}
#hor-zebra td
{
    padding: 8px;
    color: #669;
    vertical-align:top;
}
#hor-zebra .odd
{
    background: #e8edff; 
}

    """
    htmlHeader = Template("""
         <html>
 <head>
 <title>Facebook Session</title>
 <style type="text/css">
<!--

@import url("style.css");

-->
</style>

 </head>
 <body id="hor-zebra">
 <H1>Facebook Dump</H1>
 <table id="hor-zebra" summary="Facebook Session">
    <tr>
        <th scope="col">Time</th>
        <th scope="col">Action</th>
        <th scope="col">Content-Type</th>
        <th scope="col">Contents</th>
    </tr>
    """)
    htmlFooter = Template("""
        </table>
 </body></html>
    """)
    chatMessage = Template("""
    <tr class="${evenOrOdd}">
        <td>${time}</td>
        <td>Chat Message</td>
        <td>${content_type}</td>
        <td>${whoFrom} -&gt; ${whoTo}<br>${message}</td>
    </tr>
    """)
    
    loginAttempt = Template("""
    <tr class="${evenOrOdd}">
        <td>${time}</td>
        <td>Login Attempt</td>
        <td>N/A</td>
        <td>${email}: ${password}</td>
    </tr>
    """)
    
    imageUpload = Template("""
    <tr class="${evenOrOdd}">
        <td>${time}</td>
        <td>Image Upload</td>
        <td>${content_type}</td>
        <td><a href="${imgFileName}">${fileName}<br> <img width="300" src="${imgFileName}"></a></td>
    </tr>
    """)
    
    unkRecvd = Template("""
    <DIV>URL: ${url} <br>
    Time: ${time} <br>
    Content-Type: ${content_type} <br>
    Text recvd: ${text}</DIV>
    """)
    
    def __init__(self, outputFolder):
        self.outputEven = True
        self.outputFolder = outputFolder
        self.pictureCounter = 0
        self.outputs = []
    
    def outputUnk(self, url, time, content_type, text):
        unk = self.unkRecvd.safe_substitute({'text':text,
                                             'time':time,
                                             'content_type':content_type,
                                             'url':url})
        self.outputs.append(unk)
    
    def getEvenOrOdd(self):
        ret = 'even' if self.outputEven else 'odd'
        self.outputEven = not self.outputEven
        return ret
    
#    def outputChatMessage(self, time, content_type, message):
#        d = {}
#        d['evenOrOdd'] = self.getEvenOrOdd()
#        d['message'] = message
#        d['content_type'] = content_type
#        d['time'] = time
#        d['whoTo'] = d['whoFrom'] = 'Unk'
#        self.outputs.append(self.chatMessage.safe_substitute(d))
        
    def outputChatMessageKnown(self, time, content_type, whoFrom, whoTo, message):
        d = {}
        d['evenOrOdd'] = self.getEvenOrOdd()
        d['message'] = message
        d['content_type'] = content_type
        d['time'] = time
        d['whoTo'] = whoTo 
        d['whoFrom'] = whoFrom
        self.outputs.append(self.chatMessage.safe_substitute(d))
    
    def outputLoginAttempt(self, time, email, password):
        d = {}
        d['evenOrOdd'] = self.getEvenOrOdd()
        d['time'] = time
        d['email'] = email
        d['password'] = password
        self.outputs.append(self.loginAttempt.safe_substitute(d))
        
    def outputUploadedImage(self, time, content_type, fileName, fileEnding, imgData):
        d = {}
        d['evenOrOdd'] = self.getEvenOrOdd()
        d['time'] = time
        d['content_type'] = content_type
        
        outFileName = self.getPictureFilename(fileEnding)
        
        self.writeOutToFile(outFileName, imgData)
        
        d['imgFileName'] = outFileName
        d['fileName'] = fileName
        
        self.outputs.append(self.imageUpload.safe_substitute(d))
        

    def writeOutToFile(self, fileName, data):
        fOut = open(os.path.join(self.outputFolder, fileName), 'wb')
        fOut.write(data)
        fOut.close()

    def dumpToFile(self):
        fileName = 'index.html'
        data = self.htmlHeader.safe_substitute()
        for o in self.outputs:
            data += o
        data += self.htmlFooter.safe_substitute()
        
        self.writeOutToFile(fileName, data)
        self.writeOutToFile('style.css', self.styleCss)
        
    def getPictureFilename(self, fileEnding):
        fName = '%d.%s' % (self.pictureCounter, fileEnding)
        self.pictureCounter += 1
        return fName 

class Event(object):    
    
    def __init__(self, httpStatus,
                       host="", url="", 
                       content_type="", postContents=None, 
                       contents=None, clientReqTime='', serverRespTime=''):
        self.host = host
        self.url = url
        self.content_type = content_type
        self.contents = contents
        self.postContents = postContents
        self.clientReqTime = clientReqTime
        self.serverRespTime = serverRespTime
        self.httpStatus = httpStatus
    
        

class Pattern(object):
    def __init__(self, output):
        self.output = output
        
    """
    Overall Pattern object. Composed of a list of single patterns
    """
    def processEvent(self, event):
        """
        Process an event. If we've run through our state cycle, then
        
        Return true if we have something to dump to html, false if we don't
        """
        pass


class SinglePattern(Pattern):
    def __init__(self, output):
        Pattern.__init__(self, output)
        self.urlMatch = re.compile(r".*")
        
    def doProcessEvent(self, event):
        raise Exception('You did not implement me!')
        
    def processEvent(self, event):
        """
        Process an event. If we've run through our state cycle, then
        """
        if self.urlMatch.search(event.url):
            self.doProcessEvent(event)
        


class DefaultPattern(SinglePattern):
    def processEvent(self, event):
        """
        Process an event. If we've run through our state cycle, then
        """
        content = None
        if (event.contents != None):
            n = 50
            if len(event.contents) < n:
                n = len(event.contents)
            
            content = event.contents[:n]
            
        if event.content_type[0:4] != 'text':
            content = "Not text"
        
        self.output.outputUnk(event.url,
                              event.serverRespTime,
                              event.content_type,
                              content)


class LoginPattern(SinglePattern):

    def __init__(self, output):
        SinglePattern.__init__(self, output)
        #self.chatSentUrlRe = re.compile(r"www\.facebook\.com/ajax/mercury/send_messages.php.*")
        self.urlMatch = re.compile(r".*www\.facebook\.com/login.php\?login_attempt.*")
        
    def doProcessEvent(self, event):
        vars2 = event.postContents.split('&')
        emailAddr = None
        password = None
        
        for v in vars2:
            assignments = v.split('=')
            if 2 == len(assignments) and assignments[0] == 'email':
                emailAddr = urllib.url2pathname(assignments[1])
            elif 2 == len(assignments) and assignments[0] == 'pass':
                password = assignments[1]
        
        self.output.outputLoginAttempt(event.clientReqTime,
                                      emailAddr,
                                      password)    

class PictureUploadPattern(SinglePattern):
     
    def __init__(self, output):
        SinglePattern.__init__(self, output)
        self.urlMatch = re.compile(r"""upload\.facebook\.com/media/upload/photos/flash.*
                                       |
                                        .*\.facebook.com/pic_upload.php.*
                                    """, re.VERBOSE)
     
        
     
    def doProcessEvent(self, event):
        """
        Process an event. If we've run through our state cycle, then
        """
        # find the index of 
        findPicRe = re.compile(r'filename="(.*)"\r\nContent\-Type: (.*)', re.M)
        matches = findPicRe.search(event.postContents)
        if matches:
            fileName = matches.group(1)
            fileType = matches.group(2)
            
            if fileType[-1] == '\r': fileType = fileType[:-1]
            
            indexOfImage = matches.end() # two is for the two carriage returns
            
            imageData = event.postContents[indexOfImage:]
            
            while imageData[0] == '\r' or imageData[0] == '\n':
                imageData = imageData[1:]
            
            self.output.outputUploadedImage(event.clientReqTime,
                                            fileType, 
                                            fileName, 
                                            'jpg', 
                                            imageData)
            
            
        
        
class ChatPattern(SinglePattern):
    
    
    def __init__(self, output):
        SinglePattern.__init__(self, output)
        #self.chatSentUrlRe = re.compile(r"www\.facebook\.com/ajax/mercury/send_messages.php.*")
        self.urlMatch = re.compile(r".*\.channel\.facebook\.com/pull\?channel=.*")
         
     
    def doProcessEvent(self, event):
        """
        Process an event. If we've run through our state cycle, then
        """
        #print event.url
#        if self.chatSentUrlRe.search(event.url):
#            postDict = urlparse.parse_qs(event.postContents)
#            if 'message_batch[0][body]' in postDict:
#                listMsg = postDict['message_batch[0][body]']
#                if len(listMsg) > 0:
#                    pass
##                    self.output.outputChatMessage(event.clientReqTime,
##                                                  event.content_type,
##                                                  listMsg[0])
    
        # may or may not be a chat - must parse the JSON
        text = None
        whoFrom = None
        whoTo = None
        
        if event.contents[0:9] == 'for (;;);':
            js1 = json.loads(event.contents[9:])
            if 'ms' in js1:
                js = js1['ms']
                for item in js:
                    #print js
                    if 'msg' in item:
                        js = item['msg']                            
                        text = js['text']
                    #elif 'from_name' in item:
                        whoFrom = item['from_name']
                    #elif 'to_name' in item:
                        whoTo = item['to_name']
        if (text != None):
            self.output.outputChatMessageKnown(event.clientReqTime,
                                                  event.content_type,
                                                  whoFrom,
                                                  whoTo,
                                                  text)