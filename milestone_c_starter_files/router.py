import time
import socket
import logging
from pdu import IPHeader, LSADatagram, HTTPDatagram
from graph import Graph

class Router:
    def __init__(self, router_id: str, router_interfaces: dict, direct_connections: dict):
        """
        Initializes a Router object.

        Args:
            router_id (str): Unique identifier for the router.
            router_interfaces (dict): A dictionary of router interfaces in the form {interface_name: (source_ip, dest_ip)}.
            direct_connections (dict): A dictionary of directly connected networks in the form {network: (cost, interface)}.

        Raises:
            Exception: If a socket fails to initialize.
        """
        self.router_id = router_id  
        self.router_interfaces = router_interfaces
        self.direct_connections = direct_connections
        self.lsa_seq_num = 0
        self.interface_sockets = {}
        
        # Initialize sockets for each interface
        for interface, (source, _) in self.router_interfaces.items():
            try:
                int_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
                int_socket.bind((source, 0))
                int_socket.setblocking(False)
                self.interface_sockets[interface] = int_socket
            except Exception as e:
                logging.error(f'Error creating socket for {interface}: {e}')

        # Create a socket for receiving datagrams
        receive_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
        receive_socket.bind(('0.0.0.0', 0))
        receive_socket.setblocking(False)
        self.interface_sockets['rec'] = receive_socket

        # Initialize LSA database, timers, and forwarding table
        self.router_lsa_num = {}
        self.lsdb = {}
        self.lsa_timer = time.time()
        self.forwarding_table = {}

        # Configure logging
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s - %(message)s',
                            handlers=[logging.FileHandler('network_app_router.log', mode='w')]
                            )

        self.initialize_lsdb()

    def initialize_lsdb(self):
        """
        Initializes the Link-State Database (LSDB) with the router's direct connections.
        
        The LSDB is a data structure that holds information about the router's directly connected networks
        and the cost of reaching them.
        
        Returns:
            None
        """

        ### INSERT CODE HERE ###
        # Store the destination, cost, and interface for each direct connection of the router in the LSDB
        # print(self.direct_connections)
        self.lsdb[self.router_id] = []
        for item in self.direct_connections:
            self.lsdb[self.router_id].append((item, self.direct_connections[item][0], self.direct_connections[item][1]))# = self.direct_connections[item]
        # print(self.lsdb)

    def update_lsdb(self, adv_rtr: str, lsa: str):
        """
        Updates the Link-State Database (LSDB) with new information from a received LSA.

        Args:
            adv_rtr (str): The advertising router's ID.
            lsa (str): The LSA data as a string, where each line contains the neighbor, cost, and interface information.

        Returns:
            None
        """
        lsa = [tuple(line.split(',')) for line in lsa.split('\r\n')]
        self.lsdb[adv_rtr] = [(neighbor.strip(), int(cost.strip()), interface.strip()) for neighbor, cost, interface in lsa]
        # print("Updated:",self.lsdb)
        # print("")

    def send_initial_lsa(self):
        """
        Broadcasts the initial Link-State Advertisement (LSA) containing the router's direct connections to all interfaces.

        Returns:
            None

        Logs:
            Logs the sending of the initial LSA.
        """
        for interface, (source, dest) in self.router_interfaces.items():
            int_socket = self.interface_sockets[interface]
            formatted_lsa_data = [f'{neighbor}, {cost}, {interface}' for neighbor, cost, interface in self.lsdb[self.router_id]]
            new_datagram = LSADatagram(source_ip=source, dest_ip='224.0.0.5', adv_rtr=self.router_id, lsa_seq_num=self.lsa_seq_num, lsa_data='\r\n'.join(formatted_lsa_data))
            int_socket.sendto(new_datagram.to_bytes(), (dest, 0))
        logging.info(f'{self.router_id} has sent the initial LSA.')

    def forward_lsa(self, lsa_datagram: LSADatagram, lsa_int: str):
        """
        Forwards a received LSA to all interfaces except the one on which it was received.

        Args:
            lsa_datagram (LSADatagram): The received LSA datagram to be forwarded.
            lsa_int (str): The interface on which the LSA was received.

        Returns:
            None

        Logs:
            Logs the forwarding of the LSA to the destination.
        
        Exceptions:
            Logs any exceptions that occur during forwarding.
        """
        time.sleep(1) # Make sure all initial LSAs are sent before forwarding an LSA
        for interface in self.router_interfaces:
            if interface != lsa_int and lsa_datagram.adv_rtr != self.router_id:
                source, dest = self.router_interfaces[interface]
                int_socket = self.interface_sockets[interface]
                new_datagram = LSADatagram(source_ip=source, dest_ip='224.0.0.5', adv_rtr=lsa_datagram.adv_rtr, lsa_seq_num=lsa_datagram.lsa_seq_num, lsa_data=lsa_datagram.lsa_data)
                try:
                    int_socket.sendto(new_datagram.to_bytes(), (dest, 0))
                    logging.info(f'{self.router_id}: LSA forwarded to {dest}.')
                except Exception as e:
                    logging.error(f'Error forwarding LSA: {e}')

    def process_link_state_advertisement(self, lsa: bytes, interface: str):
        """
        Processes a received Link-State Advertisement (LSA) and updates the LSDB. If the LSA contains new information, 
        the router broadcasts the LSA to its other interfaces.

        Args:
            lsa (bytes): The received LSA in byte form.
            interface (str): The interface on which the LSA was received.

        Returns:
            None

        Raises:
            None
        """

        ### INSERT CODE HERE ###
        ## Convert the lsa packet from bytes to a LSADatagram class object
        dgram = LSADatagram.from_bytes(lsa)

        ## If the LSA is new and not from the router itself:

        if  dgram.adv_rtr != self.router_id and (dgram.adv_rtr not in self.router_lsa_num or dgram.lsa_seq_num > self.router_lsa_num[dgram.adv_rtr]):
        # Reset the LSA timer (Router will assume all LSAs have been received if timer expires - greater than 5 seconds since new LSA received)
            self.lsa_timer = time.time()
        # Update the LSA sequence number for the advertising router
            self.router_lsa_num[dgram.adv_rtr] = dgram.lsa_seq_num
        # Update the LSDB with the LSA data
            self.update_lsdb(dgram.adv_rtr, dgram.lsa_data)
        # Forward the LSA to all other interfaces, except the interface it was received on.
            self.forward_lsa(dgram,interface)
        pass

    def forward_datagram(self, dgram: bytes):
        """
        Forwards an HTTP datagram to the appropriate next hop based on the forwarding table.

        Args:
            dgram (bytes): The datagram received as raw bytes.

        Returns:
            None

        Logs:
            Logs the process of forwarding the datagram to the appropriate next hop.

        Raises:
            Exception: Logs any errors during the forwarding process.
        """

        ### INSERT CODE HERE ###
        ## Convert the datagram bytes to an HTTPDatagram object
        hgram = HTTPDatagram.from_bytes(dgram)

        ## If the next hop for the datagram associated with one of the router interfaces:
        if hgram.next_hop in [connection[0] for connection in self.router_interfaces.values()]:
        # Convert the destination IP address to binary for longest prefix matching
            octets = hgram.ip_daddr.split('.')
            octets = [bin(int(x))[2:] for x in octets]
            octets = ["0"*(8-len(y))+y for y in octets]
            destbits = "".join(["0"*(8-len(y))+y for y in octets])
        # Perform longest prefix match against known networks (those in the forwarding table with a CIDR)
            cidrs = {}
            for item in self.forwarding_table:
                splits = item.split("/")
                if len(splits) != 2:
                    continue
                octets = splits[0].split('.')
                octets = [bin(int(x))[2:] for x in octets]
                octets = ["0"*(8-len(y))+y for y in octets]
                bits = "".join(["0"*(8-len(y))+y for y in octets])
                cidrs[splits[0]] = (bits, splits[1])
            # print("CIDRs:", cidrs)
            # print("Dest bits:", destbits)
            matches = []
            for item in cidrs:
                matchlen = int(cidrs[item][1])
                # print(destbits[:matchlen] , cidrs[item][0][:matchlen])
                if destbits[:matchlen] == cidrs[item][0][:matchlen]:
                    matches.append((item,str(matchlen)))
                    # print("found")
            if len(matches) > 0:
                matches.sort(key=lambda x: x[1], reverse=True)
                interface = self.forwarding_table["/".join(matches[0])][0]
        # Forward the datagram to the correct interface
                source, dest = self.router_interfaces[interface]
                int_socket = self.interface_sockets[interface]
                new_datagram = hgram
                new_datagram.next_hop=dest
                try:
                    int_socket.sendto(new_datagram.to_bytes(), (dest, 0))
                    logging.info(f'{self.router_id}: HTTP forwarded to {dest}.')
                except Exception as e:
                    logging.error(f'Error forwarding HTTP: {e}')
 
    def run_route_alg(self):
        """
        Runs Dijkstra's shortest path algorithm to calculate the shortest paths to all nodes
        in the network and updates the forwarding table based on the LSDB.

        Returns:
            None

        Raises:
            None
        """
        ### INSERT CODE HERE ###
        ## Create the graph by add an edge (the node, neighbor, cost, and interface) for each entry in the LSDB.
        network = Graph()
        for from_id in self.lsdb:
            # print(from_id, ":", self.lsdb[from_id])
            for to_id in self.lsdb[from_id]:
                # print(to_id)
                network.add_edge(from_id, to_id[0], to_id[1], to_id[2])
        # print(network)

        ## Initialization for Djikstra's algorithm
        # Create a set of visited nodes that has the start node only (initially)
        visited = []
        # Set the distance to all known nodes to infinity, except for:
        bestpaths = {}
        #       - the start node, which is initialized to 0
        for con in network.nodes:
            for router in network.nodes[con]:
                bestpaths[router[0]] = (None, None)

        bestpaths[self.router_id] = ([self.router_id], 0)
        # print(bestpaths)
        # print("Best paths:",bestpaths)
        #       - the nodes directly connected to the start node should have distance equal to their cost
        for con in network.nodes[self.router_id]:
            bestpaths[con[0]] = ([(self.router_id,None),(con[0],con[2])], con[1])
        # print("Best paths:",bestpaths)

        for node in network.nodes:
            while node not in visited:
                nodecost = bestpaths[node][1]
                for con in network.nodes[node]:
                    if con not in visited:
                        if bestpaths[con[0]][1] == None or nodecost + con[1] < bestpaths[con[0]][1]:
                            path = bestpaths[node][0].copy()
                            path.append((con[0], con[2]))
                            bestpaths[con[0]] = (path, nodecost+con[1])
                visited.append(node)
        # print(self.router_id,": ", bestpaths,sep="")

        # In order to determine the interface for the best path, track the previous nodes for each node 
        #       on the shortest path from the start node. Initially, set this to (None, None) for each node
        #       to represent that the previous node and it's interface have not been recorded yet.
        # Additionally, store the full path from the start node to each node. Initially, the path to each node
        #       is an empty list since no path has been calculated yet.

        ## Dijkstra's algorithm

        # While not all nodes have been processed (i.e., while N_prime does not include all nodes in the graph)
    
            # Find the node 'w' not in N_prime that has the smallest distance (D[w]) from the source node
            # This is the next node to process
    
            # Add node 'w' to the set of processed nodes N_prime (i.e., its shortest path has been found)
    
            # For all neighbors of node 'w'
        
                # Only consider neighbors that have not been processed yet (i.e., not in N_prime)
            
                # Calculate the potential new distance to this neighbor through node 'w'
            
                # If this new distance is shorter than the current known distance to 'neighbor'
                
                    # Update the shortest known distance to 'neighbor'
                
                    # Update the previous node and interface for 'neighbor', indicating that the
                    # shortest path to 'neighbor' now goes through 'w' and uses the specified interface
                
                    # Update the path to 'neighbor', by appending the (neighbor, interface) tuple
                    # to the path that leads to 'w'

        ## Construct the forwarding table for each node in the graph.
        # For each node, store:
        # 1. The outgoing interface used to reach the node, which is found by accessing the first hop in 'paths[node]' (if a path exists).
        # 2. The shortest known distance to that node from the source, stored in 'D[node]'.
        # If there is no path to the node, the interface is set to None.
        # The resulting forwarding table maps each node to a tuple: (interface, shortest distance).
        forwardtable = {}
        for item in bestpaths:
            # print(bestpaths[item])
            forwardtable[item] = (bestpaths[item][0][-1][1], bestpaths[item][0][-1][0])
        # print(forwardtable)
        # print("")
        self.forwarding_table = forwardtable

    def process_datagrams(self):
        """
        Receives, processes, and forwards incoming datagrams or LSAs. It updates the LSDB and forwarding table as needed,
        and then forwards datagrams to their correct next hop.

        Returns:
            None

        Logs:
            Logs the content of the LSDB and forwarding table.
        """
        while time.time() - self.lsa_timer < 5:
            for interface in self.interface_sockets.keys():
                try:
                    new_datagram_bytes, address = self.interface_sockets[interface].recvfrom(1024)
                    new_datagram = IPHeader.from_bytes(new_datagram_bytes)
                    if new_datagram.ip_daddr == '224.0.0.5' and address[0] in [connection[1] for connection in self.router_interfaces.values()]:
                        self.process_link_state_advertisement(new_datagram_bytes, interface)
                except Exception:
                    continue

        self.run_route_alg()
        time.sleep(1)
        start_time = time.time()
        while time.time() - start_time < 10:
            for interface in self.interface_sockets.keys():
                try:
                    new_datagram_bytes, _ = self.interface_sockets[interface].recvfrom(1024)
                    self.forward_datagram(new_datagram_bytes)
                except Exception:
                    continue

        logging.info(f'{self.router_id} LSDB: {self.lsdb}')
        logging.info(f'{self.router_id} Forwarding Table: {self.forwarding_table}')
        self.shutdown()

    def shutdown(self):
        """
        Shuts down the router by closing all open sockets.

        Returns:
            None

        Logs:
            Logs the shutdown process of the router.
        """
        # Close all interface sockets
        for interface in self.interface_sockets.keys():
            try:
                self.interface_sockets[interface].close()
            except Exception as e:
                logging.error(f'Error closing socket for {interface}: {e}')

# Example usage
if __name__ == "__main__":
    r1_interfaces = {
        'Gi0/1': ('127.0.0.254', '127.0.0.1'), 
        'Gi0/2': ('127.248.0.1', '127.248.0.2'),
        'Gi0/3': ('127.248.4.1', '127.248.4.2')
    }
    
    r1_direct_connections = {
        '127.0.0.0/24': (0, 'Gi0/1'),
        '2.2.2.2': (3, 'Gi0/2'), 
        '3.3.3.3': (9, 'Gi0/3')
    }
    
    R1 = Router('1.1.1.1', r1_interfaces, r1_direct_connections)
    R1.run_route_alg()
    R1.shutdown()
