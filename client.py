from os import initgroups
from rich.console import Console
from twisted.internet import reactor
from twisted.internet import endpoints
from twisted.internet.error import ReactorAlreadyInstalledError
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.application.internet import ClientService

import uuid
import json



#! udp kullanılmadığı sürece factoryler kullanılır.
#! inconsistency den kaçınılmalı.


class Client(Protocol):
    def __init__(self) -> None:
        #reactor.callInThread(self.foo) #! bloklayan fonksiyonlarda bunu kullanmak daha mantıklı. Çünkü event loop bloklanmamalı. 

        self.client_id = str(uuid.uuid4())

    def connectionMade(self):
        self.send_message()

    def dataReceived(self, data):
        print(data.decode("utf-8"))
    
    def send_message(self,data="-"):
        d = {
            "machine" : "client",
            "id" : self.client_id,
            "data" : data
        }

        self.transport.write(self.__encode_json(d))
    
    @staticmethod
    def __encode_json(data):
        return json.dumps(data).encode("utf-8")
    
    @staticmethod
    def __decode_json(data):
        return json.loads(data.decode("utf-8"))


class CliFactory(ReconnectingClientFactory):
    def buildProtocol(self, addr):
        return Client()
    
    def clientConnectionFailed(self, connector, reason):
        print(reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

        #! bağlantının başarısız olduğu durumlarda çağırılır.
        #! mesela SERVERA ULAŞAMAMAK
    
    def clientConnectionLost(self, connector, reason):
        print(reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

        #! bağlantının kesildiği durumlarda çağırılır.
        #! mesela clientın internet bağlantısının kesilmesi.
        #? neden reconnecting client factory kullanılıyor?
        #? bunun yerine connector.reconnect() kullanılabilir ancak
        #? reconnecting client factory her saniyede bir tekrar bağlanmayı dener.
        #? connector sadece bir kere dener ve bırakır.

if __name__ == "__main__":
    endpoint = TCP4ClientEndpoint(reactor, "localhost", 7322)
    #endpoint.connect(CliFactory())

    reconnector = ClientService(endpoint, CliFactory())
    reconnector.startService()

    try:
        reactor.run()
    except KeyboardInterrupt:
        reactor.stop()
        
