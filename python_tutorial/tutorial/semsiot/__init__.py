import csv
import json
import time

try:
    import queue as q
except ImportError:
    import Queue as q
import threading

import requests

class IOTDevice(object):

    registerURL = '/api/Register'
    
    def __init__(self):
        self.dataAgeWindow = 10 # seconds. Only try to send data that is less than x seconds old
        self.clearOutQueueWhenBehind = True
        self.commandCheckInterval = 20 # seconds. Check for commands at least this often
        self.baseURL = 'https://semsiot.3m.com'
        self.reportQueue = q.Queue()
        self.unacknowledgedCommands = {}
        self.commandQueue = q.Queue()
        self.commandAckQueue = q.Queue()
        self.registrationInfo = None
        self.serialNumber = None
        self.apiKey = None
        self.applicationId = None
        self.session = requests.session()        
        return
        
    def Start(self):
        if not self.apiKey:
            raise ValueError("apiKey was not provided, or is not a string, or is empty")
        if not self.serialNumber:
            raise ValueError("serialNumber was not provided, or is not a string, or is empty")
        if not self.applicationId:
            raise ValueError("applicationId was not provided, or is not a string, or is empty")
        if not self.baseURL:
            raise ValueError("baseURL was not provided, or is not a string, or is empty")
        if self.commandCheckInterval < 1:
            raise ValueError("commandCheckInterval cannot be less than 1")
            
        self.__destroyed = False
        self.__sendRemainingMessages = False
        time.clock()
        self.reporterThread = threading.Thread(target=self.__reportWorker)
        self.reporterThread.start()
        self.commandRetrieverThread = threading.Thread(target=self.__commandRetriever)
        self.commandRetrieverThread.start()
        return
         
    def WaitForRegistrationBlocking(self):
        if self.registrationInfo is not None:
            return
        delay = 0.05
        while not self.__register():
            delay = min(60*30, delay * 2)
            print("Failed to register. Delaying " + str(delay) + " seconds")
            time.sleep(delay)
            pass
        print("Registered")
        return
      
    def AcknowledgeCommand(self, command, payloadDictionary=None):
       deviceCommandId = command["deviceCommandId"]
       payloadDictionary['deviceCommandId'] = deviceCommandId
       self.commandAckQueue.put( { 'deviceCommandId' : deviceCommandId, 'payloadDictionary' : payloadDictionary } )
       return
       
    def ProcessNewCommands(self):
        commands = []
        
        try:
            while True:
                command = self.commandQueue.get(False)
                commands.append(command)
                self.commandQueue.task_done()
        except q.Empty:
            pass     
                       
        return commands
    
    #def ReportBinaryDataAsync(self, data, metadata):
       #return
       
    def ReportDataAsync(self, item):
       size = self.reportQueue.qsize()
       self.reportQueue.put( { 'item': item, 'timestamp': time.clock() }  )
       print ("Data queued. Size of queue is currently " + str(size+1))
       return
        
    def Stop(self, sendRemainingMessages=False):
        self.__sendRemainingMessages = sendRemainingMessages
        self.__destroyed = True
        if sendRemainingMessages:
            while True:
                qSize = self.reportQueue.qsize()
                if qSize == 0:
                    break
                else:
                    print ("Waiting for remaining messages to be sent. " + str(qSize ) + " remain")
                    time.sleep(0.3)
        self.reporterThread.join()
        self.commandRetrieverThread.join()
        return
    
    def __commandRetriever(self):
        commandCheckDelay = 1
        
        while True:
            response = self.__executeWithRetries("POST", self.baseURL + '/api/Command/Pending', {})
            if response.status_code == 200:
                newCommands = 0
                commands = response.json()["Commands"]
                for command in commands:
                    commandId = command['deviceCommandId']
                    if commandId not in self.unacknowledgedCommands:
                        commandCheckDelay = 1
                        newCommands = newCommands + 1
                        self.unacknowledgedCommands[commandId] = command
                        self.commandQueue.put(command)
                print ("Command lookup successful, " + str(newCommands) + " new commands")

            else:
                print ("Command lookup failed")           
            
            # todo: adapt commandCheckInterval based on recent command occurence
            
            commandCheckDelay = commandCheckDelay * 2
            commandCheckDelay = min(commandCheckDelay, self.commandCheckInterval)
            print ("Waiting " + str(commandCheckDelay) + " seconds until checking for commands")

            for i in range(commandCheckDelay*5):                
                commandAck = None
                try:
                    commandsAcked = 0
                    while True:
                        commandAck = self.commandAckQueue.get(False)
                        if commandAck is not None:
                            payloadDictionary = commandAck['payloadDictionary']
                            response = self.__executeWithRetries("PATCH", self.baseURL + '/api/Command', payloadDictionary)
                            print ("Command ack response: " + str(response.status_code))
                            del self.unacknowledgedCommands[commandAck['deviceCommandId']]
                            self.commandAckQueue.task_done()
                            commandsAcked = commandsAcked + 1
                            if commandsAcked > 5:
                                break
                except q.Empty:
                    pass     

                time.sleep(0.2)
                if self.__destroyed is True:
                    print ("Stopping command retrieval worker")
                    return
                  
    #incorporate binary and batch into report worker process
                  
    def __reportWorker(self):
        eventHubFailCount = 0
        fallbackUseCount = 0
        skipEventHub = False
        
        while True:
            task = None
        
            stopIfNoTasks = False
            if self.__destroyed is True:
                if self.__sendRemainingMessages:
                    stopIfNoTasks = True
                else:
                    print ("Stopping command retrieval")
                    return
            try:
                task = self.reportQueue.get(True, 0.5)
            except q.Empty:
                pass     
                    
            if task is None:
               if stopIfNoTasks:
                    print ("Stopping report worker")
                    return
               continue
               
            self.reportQueue.task_done()
            
            deltaT = time.clock() - task["timestamp"]
            

            if self.dataAgeWindow != 0 and deltaT >= self.dataAgeWindow:
                print ("Ignoring data due to age " + str(deltaT) + " seconds. Max is " + str(self.dataAgeWindow))
                if self.clearOutQueueWhenBehind:
                    print ("Clearing data queue")
                    while True:
                        try:
                            task = self.reportQueue.get(False)
                            self.reportQueue.task_done()
                        except q.Empty:
                            break
                continue
            
            #print ("Got task with time delta " + str(deltaT))
                
            payloadDictionary = {} #task["item"] # {}

            taskItem = task["item"];
            taskItem["SubmissionDelayDelta"] = deltaT
            batch = [taskItem] 

	    maxSendInterval = 10000;

	    startms = time.time()*1000.0
            while len(batch) < 20:
                try:
                    additionaltask = self.reportQueue.get(True, 1)  #TODO doesn't seem to support fractional seconds
                    endms = time.time()*1000.0

                    additionalTaskItem = additionaltask["item"];
                    additionaldeltaT = time.clock() - additionaltask["timestamp"]
                    batch.append(additionalTaskItem)
                    self.reportQueue.task_done()

                    if endms- startms > maxSendInterval:
                        break
                except q.Empty:
                    pass

            payloadDictionary["BatchArray"] = batch
            print("Sending " + str(len(batch)))

            #print(json.dumps(payloadDictionary));
            registered = False
            if self.registrationInfo is not None:
                registered = True
            else:
                if self.__register():
                    registered = True
                else:
                    # failed to register. what to do with data?
                    pass
                    
            tryFallback = False
            if registered:
                if skipEventHub:
                    print ("Bypassing event hub for another " + str(25-fallbackUseCount) + " more data reports")
                    tryFallback = True
                else:
                    EventHubUrl = self.registrationInfo["EventHubUrl"]
                    EventHubKey =   self.registrationInfo["EventHubKey"]

                    # send to event hub first
                    response = self.__executeWithRetries("POST", EventHubUrl, payloadDictionary, additionalHeaders = { "Authorization" : EventHubKey} )
                    
                    if response is not None and response.status_code == 401:
                        print ("Authorization to Event Hub is invalid or expired")
                        self.registrationInfo = None      
                        continue
                    elif response is not None and response.status_code == 201:
                        #print(response.status_code)
                        print ("Succesfully posted data to Event Hub")
                        # reset counter now that we succeeded
                        eventHubFailCount = 0
                    else:
                        tryFallback = True
                        print ("Failed to post data to Event Hub")
                        if response is not None:
                            print (response.status_code)
                            print (response.text)
                    
                if tryFallback:
                    print ("Attempting to use fallback")
                    fallbackResponse = self.__executeWithRetries("POST", self.baseURL + '/api/Data', payloadDictionary)
                    
                    if fallbackResponse is not None and fallbackResponse.status_code == 401:
                        print ("Authorization to fallback using API is invalid or expired")
                        self.registrationInfo = None      
                        continue
                    elif fallbackResponse is not None and (fallbackResponse.status_code == 201 or fallbackResponse.status_code == 200):
                       # print(fallbackResponse.status_code)
                        print ("Succesfully posted data to fallback using API")
                        if skipEventHub:
                            fallbackUseCount = fallbackUseCount + 1
                            
                            if fallbackUseCount >= 25:
                                skipEventHub = False
                                fallbackUseCount = 0
                        else:
                            eventHubFailCount = eventHubFailCount + 1
                            print ("Will bypass event hub after " + str(5-eventHubFailCount) + " more sequential failures")
                            if eventHubFailCount >= 5:
                                skipEventHub = True
                                eventHubFailCount = 0
                    else:                           
                        print ("Failed to post data to fallback using API")
                        print (fallbackResponse.status_code)
                        print (fallbackResponse.text)
          
        return
        
    def __register(self):
        response = self.__executeWithRetries("POST", self.baseURL + self.registerURL, {})
        #print (response.status_code)
        if response.status_code == 200:
            self.registrationInfo = response.json()
            print ("Registration successful.")
            print ("EventHub: " + self.registrationInfo["EventHubUrl"])
            return True
        else:
            print ("Registration failed.")
            return False
        pass

    def __executeWithRetries(self, httpVerb, url, payload, additionalHeaders={}, retries=3, timeout=1.1, timeout_increase_factor=2, delay=0.05, delay_increase_factor=2, max_delay = 10, ):
        headers = {'Content-type': 'application/json'}
        headers.update(additionalHeaders)
        
        basePayload={
            'serialNumber': self.serialNumber,
            'applicationId': self.applicationId,
            'apiKey': self.apiKey
        }
        basePayload.update(payload)
        
        #print (basePayload)
        tries = 0
        for i in range(retries):
            response = None;
            methods = {
                "POST" : self.session.post,
                "PATCH" : self.session.patch
            }
            try:
		    #print(json.dumps(basePayload))
                method = methods.get(httpVerb)
                if method is None:
                    raise ArgumentException
                response = method(url, data=json.dumps(basePayload), headers=headers, timeout=timeout)

                return response              
            except requests.RequestException as e:
                print( str(e))
                pass
             
            tries = tries + 1
            timeout = timeout * timeout_increase_factor
            delay =  min(delay*delay_increase_factor, max_delay)
            #print("Will retry " + str(tries) + " of " + str(retries) + " in " +  str(delay) + " seconds")
            time.sleep(delay)
            pass
        return None
        
