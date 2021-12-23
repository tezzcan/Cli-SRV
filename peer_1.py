from rich import print, inspect
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import uuid
from random import randint

class Client(DatagramProtocol):
    def __init__(self, host, port) -> None:


        self.id = uuid.uuid4()
        self.host = host
        self.port = port

        self.address = (self.host, self.port)
        print(f"Çalışıyor-> id: {self.id}\n{self.host}:{self.port}")

        self.address_book = []
    

    def startProtocol(self):
        reactor.callInThread(self.send_message)

    def datagramReceived(self, data, addr):
        print(f"<{ addr[0] }:{ addr[1] }> { data.decode('utf-8') }")

    def send_message(self):
        while True:
            self.transport.write(input("\n").encode("utf-8"), self.address)



if __name__ == "__main__":
    reactor.listenUDP(7322, Client("127.0.0.1", 7323))
    reactor.run()