import struct
import socket

class Datagram:
    """
    As a reminder, here is the basic shape of a TCP header. This class will
    serve as a proxy for an actual TCP header since we won't be using the specified
    sizes but we will be defining all of the fields.

    0         4         8         12         16         20         24         28         32
    +-------------------------------------------------------------------------------------+
    |         Source Port (2 bytes)          |         Destination Port (2 bytes)         |
    +-------------------------------------------------------------------------------------+
    |                            Sequence Number (4 bytes)                                |
    +-------------------------------------------------------------------------------------+
    |                         Acknowledgment Number (4 bytes)                             |
    +-------------------------------------------------------------------------------------+
    | Data Offset |Res  |        Flags       |           Window Size (2 bytes)            |
    +-------------------------------------------------------------------------------------+
    |           Checksum (2 bytes)           |            Urgent Pointer (2 bytes)        |
    +-------------------------------------------------------------------------------------+
    
    As a preview for the network layer, here is the basic IP header.

    0         4         8         12         16         20         24         28         32
    +-------------------------------------------------------------------------------------+
    | Version |   IHL   |Type of Service(ToS)|                Total Length                |
    +-------------------------------------------------------------------------------------+
    |            Identification              |Flags|      Fragment Offset (13 bits)       |
    +-------------------------------------------------------------------------------------+
             TTL        |      Protocol      |          Header Checksum (16 bits)         |
    +-------------------------------------------------------------------------------------+
    |                             Source IP Address (32 bits)                             |
    +-------------------------------------------------------------------------------------+
    |                           Destination IP Address (32 bits)                          |
    +-------------------------------------------------------------------------------------+

    """
     
    def __init__(self, ip_ver=4, ip_ihl=5, ip_tos=0, ip_tot_len=40, ip_frag_off=0, 
                   ip_ttl=255, ip_proto=socket.IPPROTO_TCP, ip_check=0, source_ip='127.0.0.2', dest_ip='127.128.0.1',
                   source_port=18000, dest_port=8080, seq_num=0, ack_num=0, data_offset=5, 
                   reserved=0, flags=0, window_size=3, checksum=0, urgent_pointer=0, 
                   data=''):


        self.ip_ver = ip_ver  # IPv4
        self.ip_ihl = ip_ihl # Internet Header Length
        self.ip_tos = ip_tos  # Type of Service
        self.ip_tot_len = ip_tot_len  # Total length (IP header + TCP header)
        self.ip_id = seq_num
        self.ip_frag_off = ip_frag_off  # Fragment offset
        self.ip_ttl = ip_ttl  # Time to Live
        self.ip_proto = ip_proto  # Protocol
        self.ip_check = ip_check  # Checksum (initially 0, kernel will fill in)
        self.ip_saddr = source_ip  # Source address
        self.ip_daddr = dest_ip  # Destination address

                
        self.source_port = source_port
        self.dest_port = dest_port
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.data_offset = data_offset  # This should be in 32-bit words, default to 5 (5 * 4 bytes = 20 bytes)
        self.reserved = reserved
        self.flags = flags
        self.window_size = window_size
        self.checksum = checksum
        self.urgent_pointer = urgent_pointer

        self.data = data

    def to_bytes(self):
        
        data_offset_reserved = (self.data_offset << 4) + self.reserved
        tcp_header = struct.pack('!HHLLBBHHH',
                                self.source_port,
                                self.dest_port,
                                self.seq_num,
                                self.ack_num,
                                data_offset_reserved,
                                self.flags,
                                self.window_size,
                                self.checksum,
                                self.urgent_pointer)
        
        ip_ihl_ver = (self.ip_ver << 4) + self.ip_ihl        
        ip_header = struct.pack('!BBHHHBBH4s4s',
                                ip_ihl_ver, 
                                self.ip_tos, 
                                self.ip_tot_len, 
                                self.ip_id, 
                                self.ip_frag_off, 
                                self.ip_ttl, 
                                self.ip_proto, 
                                self.ip_check, 
                                socket.inet_aton(self.ip_saddr), 
                                socket.inet_aton(self.ip_daddr))
        
        datagram = ip_header + tcp_header + self.data.encode()
        return datagram
    
    @classmethod
    def from_bytes(cls, data):
        """
        Parse a struct bytes object and update the TCP header attributes.
        """
        unpacked_tcp_header = struct.unpack('!HHLLBBHHH', data[40:60])
        
        source_port = unpacked_tcp_header[0]
        dest_port = unpacked_tcp_header[1]
        seq_num = unpacked_tcp_header[2]
        ack_num = unpacked_tcp_header[3]
        data_offset_reserved = unpacked_tcp_header[4]
        flags = unpacked_tcp_header[5]
        window_size = unpacked_tcp_header[6]
        checksum = unpacked_tcp_header[7]
        urgent_pointer = unpacked_tcp_header[8]

        unpacked_ip_header = struct.unpack('!BBHHHBBH4s4s', data[20:40])

        ip_ihl_ver = unpacked_ip_header[0]
        ip_tos = unpacked_ip_header[1]
        ip_tot_len = unpacked_ip_header[2]
        ip_id = unpacked_ip_header[3]
        ip_frag_off = unpacked_ip_header[4]
        ip_ttl = unpacked_ip_header[5]
        ip_proto = unpacked_ip_header[6]
        ip_check = unpacked_ip_header[7]
        ip_saddr = socket.inet_ntoa(unpacked_ip_header[8])
        ip_daddr = socket.inet_ntoa(unpacked_ip_header[9])

        data_offset = (data_offset_reserved >> 4) & 0xF
        reserved = data_offset_reserved & 0xF

        ip_ver = (ip_ihl_ver >> 4) & 0xF
        ip_ihl = ip_ihl_ver & 0xF

        data = data[60:].decode()

        return cls(ip_ver, ip_ihl, ip_tos, ip_tot_len, ip_frag_off, 
                   ip_ttl, ip_proto, ip_check, ip_saddr, ip_daddr,
                   source_port, dest_port, seq_num, ack_num, data_offset, 
                   reserved, flags, window_size, checksum, urgent_pointer, 
                   data)
