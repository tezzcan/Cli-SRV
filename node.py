from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet.protocol import Protocol, ReconnectingClientFactory, connectionDone
from twisted.internet.protocol import ServerFactory as SrvFactory
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint
from twisted.application.internet import ClientService

import uuid
import random
import json

from rich import inspect, print
from config.node_config import MANAGER_HOST, MANAGER_PORT

#! reactor -> asenkron while True gibi düşün. Event Loop u sürdürür.
#! factory -> kalıcı değişiklikleri tutabileceğimiz bir nesne. Protokol varlıkları yaratır.
#! endpoint -> representation of an address

class Node(Protocol):
    def __init__(self,clients) -> None:
        self.clients = clients
        self.client_id = ""

    def connectionMade(self):
        ...
        #print("Client bağlantısı kabul edildi.")
        

    def add_client(self, data):
        client_id = data
            
        if client_id not in self.clients:
            self.clients[client_id] = self
            self.client_id = client_id

    def dataReceived(self, data):
        data = data.decode("utf-8")
        if not self.client_id:
            self.add_client(data)
            print(f"Client ID : [red]{self.client_id}[/red] -- [green]ONLINE[/green]")
            self.transport.write(f"Bağlantı açık, {self.client_id}".encode("utf-8"))
            return

        for _, protocol in self.clients.items():
            inspect(protocol)
            inspect(data)
            if protocol != self:
                protocol.transport.write(f"<{self.client_id}> {data}".encode("utf-8"))
    

    def send_message(self, data):
        self.transport.write(data.encode("utf-8"))
    
    def connectionLost(self, reason=connectionDone):
        print(f"Client ID : [red]{self.client_id}[/red] -- [red]OFFLINE[/red]")
        del self.clients[self.client_id]
            


class NodeFactory(SrvFactory):
    def __init__(self,listener_port) -> None:
        self.clients = {}
        self.listener_port = listener_port

    def buildProtocol(self, addr):
        return Node(self.clients)
    
    def startFactory(self):
        #! burda managera bağlan ve kendini register et.
        #! ulaşılabilir olduğunu göster. STARTPROTOCOLLL ? factory xdd 😆
        print("[red]Manager aranıyor..[/red]")

        endpoint = TCP4ClientEndpoint(reactor, MANAGER_HOST,MANAGER_PORT)

        ClientService(endpoint, BFactory(self.listener_port)).startService()


class Butler(Protocol):
    def __init__(self,listener_port) -> None:
        self.node_id = str(uuid.uuid4())
        self.listener_port = listener_port

    def connectionMade(self):
        self.send_message()

    def dataReceived(self, data):
        if self.__decode_json(data)["data"] == "ok":
            print("[green]Manager bulundu.[/green]")
    
    def send_message(self,data = "-"):
        d = {
            "machine" : "node",
            "id" : self.node_id,
            "port" : self.listener_port,
            "data" : data
        }

        self.transport.write(self.__encode_json(d))
    
    @staticmethod
    def __encode_json(data):
        return json.dumps(data).encode("utf-8")
    
    @staticmethod
    def __decode_json(data):
        return json.loads(data.decode("utf-8"))

class BFactory(ReconnectingClientFactory):
    def __init__(self,listener_port) -> None:
        self.listener_port = listener_port

    def buildProtocol(self, addr):
        self.resetDelay()
        return Butler(self.listener_port)
    
    def clientConnectionFailed(self, connector, reason):
        print(reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)
    
    def clientConnectionLost(self, connector, reason):
        print(reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

if __name__ == "__main__":
    port = random.randint(10000,60000)
    endpoint = TCP4ServerEndpoint(reactor, port)
    endpoint.listen(NodeFactory(port))

    print(f"Node {port} portu üzerinde başlatıldı.")
    reactor.run()