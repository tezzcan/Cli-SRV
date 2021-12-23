import random
from twisted.internet import reactor
from twisted.internet import protocol
from twisted.internet.protocol import Protocol, connectionDone
from twisted.internet.protocol import ServerFactory as SrvFactory
from twisted.internet.endpoints import TCP4ServerEndpoint

from rich import inspect, print

import json
#! reactor -> asenkron while True gibi düşün. Event Loop u sürdürür.
#! factory -> kalıcı değişiklikleri tutabileceğimiz bir nesne. Protokol varlıkları yaratır. TCP ihityaç duyar
#! endpoint -> representation of an address

class Manager(Protocol):
    def __init__(self,nodes) -> None:
        self.nodes = nodes
        self.node_id = ""
        self.node_client_table = {}

    def connectionMade(self):
        ...
        #print("Yeni node keşfedildi.")

    def add_node(self, data):
        print(data)
        node_id = data["id"]
        listener_port = data["port"]
            
        if node_id not in self.nodes:
            self.listener_port = listener_port
            self.nodes[node_id] = self
            self.node_id = node_id

    def decideIfNode(self, data):
        if data["machine"] == "node":
            return True
        else:
            return False

    def dataReceived(self, data):
        data = self.__decode_json(data)

        if self.decideIfNode(data):
            if not self.node_id:
                self.add_node(data)
                print(f"Node ID : [red]{self.node_id}[/red] -- [green]ONLINE[/green]")
                
                d = {
                    "data" : "ok"
                }
                self.transport.write(self.__encode_json(d))

                return

            for _, protocol in self.nodes.items():
                inspect(protocol)
                inspect(data)
                if protocol != self:
                    protocol.transport.write(f"<{self.node_id}> {data}".encode("utf-8"))
        else:
            #? eğer node değilse bir clientdır
            #? bu clientı bir nodeun altına ata
            
            if self.checkClientHasNode(data): ...#? eğer client nodea aitse   
            else:
                if self.nodes: #? en az bir node aktifse
                    random_node = random.choice(list(self.nodes.keys())) #! şimdilik random node, sonrasında sıralı

                    assigned_node_ip = self.nodes[random_node].transport.hostname
                    assigned_node_port = self.nodes[random_node].listener_port

                    inspect(self.transport,methods=True)

                    d = {
                        "machine" : "manager",
                        "process" : "assign_node",
                        "assigned_node_ip" : assigned_node_ip,
                        "assigned_node_port" : assigned_node_port,
                    }

                    self.transport.write(self.__encode_json(d))
                    self.transport.loseConnection()
                    #self.nodes[random_node].transport.write(data.encode("utf-8"))


                    #self.node_client_table[random_node] = data["id"]
    
    def checkClientHasNode(self, data):
        for _, value in self.node_client_table.items():
                if value == data["id"]:
                    return True
        
        return False


    def send_message(self, data):
        self.transport.write(data.encode("utf-8"))
    
    def connectionLost(self, reason=connectionDone):
        if not self.node_id: return
            
        print(f"Node ID : [red]{self.node_id}[/red] -- [red]OFFLINE[/red]")
        del self.nodes[self.node_id]

    @staticmethod
    def __encode_json(data):
        return json.dumps(data).encode("utf-8")
    
    @staticmethod
    def __decode_json(data):
        return json.loads(data.decode("utf-8"))
            


class ManagerFactory(SrvFactory):
    def __init__(self) -> None:
        self.nodes = {}

    def buildProtocol(self, addr):
        return Manager(self.nodes)


if __name__ == "__main__":
    endpoint = TCP4ServerEndpoint(reactor, 7322)
    endpoint.listen(ManagerFactory())
    print("Manager 7322 portu üzerinde başlatıldı.")
    reactor.run()