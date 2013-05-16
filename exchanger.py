__author__ = 'Stanislav Ushakov'

from threading import Thread, Lock
from SocketServer import BaseRequestHandler, TCPServer
import socket
import pickle

class SimpleRandomExchanger:
    """
    Class represents simple exchanger that simulates communicating wth the other
    nodes. Simply returns randomly generated lymphocytes.
    """
    def __init__(self, generator):
        self.generator = generator

    def set_lymphocytes_to_exchange(self, lymphocytes):
        """
        Set the lymphocytes using for exchange - these lymphocytes will
        be given to the other node when requested.
        """
        self.to_exchange = lymphocytes

    def get_lymphocytes(self):
        """
        Returns lymphocytes from the other node.
        In this class - simply randomly generated.
        """
        return self.generator()

class LocalhostNodesManager:
    """
    This class is used for getting information about other running nodes.
    This class simply returns ports on current machine.
    """
    def __init__(self, node_number, all_nodes):
        """
        Initializes manager with the number of the current node and number of
        all nodes.
        """
        self.self_host = 'localhost'
        self.base_port = 5000
        self.self_port = self.base_port + node_number
        self.other_nodes = [(self.self_host, p)
                       for p in range(self.base_port + 1, self.base_port + all_nodes + 1)
                       if p != self.self_port]
        self.other_nodes_len = all_nodes - 1
        self.current_node = 0

    def get_self_address(self):
        """
        Returns address of the current node in form(host, port).
        """
        return self.self_host, self.self_port

    def get_next_node_address(self):
        """
        Returns address of the next running node to exchange.
        (host, port)
        """
        result = self.other_nodes[self.current_node]
        self.current_node = (self.current_node + 1) % self.other_nodes_len
        return result

class TCPHandler(BaseRequestHandler):
    """
    The RequestHandler class for this node.
    """

    def handle(self):
        """
        Main method - receive dummy data and send currently stored lymphocytes -
        first pickle them.
        """
        self.request.recv(1024)
        self.request.sendall(pickle.dumps(self.server.lymphocytes_getter()))

class ServerThread(Thread):
    """
    This Thread class is used for keeping always open socket for incoming
    connections. This thread must send currently storing lymphocytes.
    """
    def __init__(self, host, port, lymphocytes_getter):
        """
        Initializes thread with host and port that this node is listening for,
        function that returns currently stored lymphocytes.
        """
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.lymphocytes_getter = lymphocytes_getter

    def run(self):
        """
        Main thread method. Open socket and waiting for connections.
        """
        server = TCPServer((self.host, self.port), TCPHandler)
        server.lymphocytes_getter = self.lymphocytes_getter

        #runs forever - so make this thread daemon
        server.serve_forever()

class GetterThread(Thread):
    """
    This Thread class is used for getting lymphocytes from another node.
    """
    def __init__(self, node_address, lymphocytes_setter):
        """
        Initializes thread with the address of node being requested and
        method that will store received lymphocytes.
        """
        Thread.__init__(self)
        self.address = node_address
        self.lymphocytes_setter = lymphocytes_setter

    def run(self):
        """
        Main thread method. Creates socket, receives data, unpickle it
        and call setter function.
        """
        try:
            sock =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(self.address)

            #send dummy data
            sock.sendall(bytes("Give me", "utf-8"))
            received = sock.recv(1024)
            while True:
                data = sock.recv(1024)
                if not data: break
                received += data
            lymphocytes = pickle.loads(received)
            self.lymphocytes_setter(lymphocytes)
        except ConnectionRefusedError:
            #Don't bother. May be it's better to add more logic to determine
            #permanent connection errors.
            pass
        finally:
            sock.close()


class PeerToPeerExchanger:
    """
    Class represents p2p exchanger. Addresses of the other peers are
    provided by special manager object. Connect to one of this nodes and ask
    for lymphocytes.
    """
    def __init__(self, nodes_manager):
        """
        Initializes exchanger with the host and port of this node.
        nodes_addresses - list of (host, port) other nodes addresses.
        """
        self.lock_to_exchange = Lock()
        self.lock_to_return = Lock()
        self.nodes_manager = nodes_manager

        #start server thread
        self.server_thread = ServerThread(self.nodes_manager.get_self_address()[0],
                                          self.nodes_manager.get_self_address()[1],
                                          self._get_lymphocytes_to_exchange)
        self.server_thread.setDaemon(daemonic=True)
        self.server_thread.start()

        #prepare lymphocytes to return
        self.to_return = []
        self._receive_lymphocytes()

        self.to_exchange = []

    def set_lymphocytes_to_exchange(self, lymphocytes):
        """
        Set the lymphocytes using for exchange - these lymphocytes will
        be given to the other node when requested.
        """
        self.lock_to_exchange.acquire()
        self.to_exchange = lymphocytes
        self.lock_to_exchange.release()

    def get_lymphocytes(self):
        """
        Returns lymphocytes from the other node. And start to
        receive the new ones.
        """
        self.lock_to_return.acquire()
        lymphocytes = self.to_return[:]
        self.lock_to_return.release()

        self._receive_lymphocytes()

        return lymphocytes

    def _get_lymphocytes_to_exchange(self):
        """
        This thread-safe method returns lymphocytes that are going to
        be sent to another node.
        """
        self.lock_to_exchange.acquire()
        lymphocytes = self.to_exchange[:]
        self.lock_to_exchange.release()
        return lymphocytes

    def _set_lymphocytes_to_return(self, lymphocytes):
        """
        This thread-safe method sets lymphocytes returned from another
        node.
        """
        self.lock_to_return.acquire()
        self.to_return = lymphocytes
        self.lock_to_return.release()

    def _receive_lymphocytes(self):
        """
        Starts thread that is getting lymphocytes from another node.
        """
        getter_thread = GetterThread(self.nodes_manager.get_next_node_address(),
                                     self._set_lymphocytes_to_return)
        getter_thread.start()