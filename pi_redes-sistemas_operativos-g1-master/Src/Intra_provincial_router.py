from json import encoder
from os import SCHED_RESET_ON_FORK, truncate
import sys 
import queue
import re
import socket
import threading
import time
import json
from typing import NewType
import MemoriaCompleta as memory

class Router_Cantonal():
    # init all the server info
    def __init__(self,complete_ip,province_id,cantonal_id):
        self.cantonal_id = cantonal_id
        self.province_id = province_id      # the id of the router
        self.complete_ip = complete_ip      # the logic ip of the router
        self.neighbors = []                 # list with the information of each neighbour(ip, port, cost, who binds)             # list of the ip of each neighbour
        self.node_ips = []
        self.direct_neighbors = []
        self.ips_connections = {}
        self.sockets_list = []              # list to save the sockets that connect
        self.sockets_bind = []              # list to save the sockets that bind
        self.sockets_by_id = []             # list of sockets by id
        self.queue_list_recv = []           # list of queues to receive all the message for each connection
        self.queue_list_send = []           # list of queues to send all the message for each connection
        self.semaphores_list = []           # list to save the semaphores to producers
        self.routers_disconnected = []      # list to save the routers that have disconnected
        self.thread_lock = threading.Lock() # lock to protect the threads
        
        
        # ------ LINKED STATE PROTOCOL --------
        self.routing_table = {}
        self.INF = 100000
        self.routing_done = False
        
    # Read the configuration file
    # This method search for the router and its connections in the file
    def read_conf_router(self,complete_ip):
        file = open("red_conf.csv","r")
        lines = file.readlines()
        neighbors = []
        node_ips = []
        type = True
        for index in lines:
            if index.strip() == "nodes":
                type = True
            else:
                if index.strip() == "edges":
                    type = False
                else:
                    if type == True:
                        tok = index.strip().split(",")
                        if str(tok[0]).replace(" ","") == complete_ip:
                            my_port = {}
                    if type == False :
                        tok = index.strip().split(",")
                        if self.complete_ip ==  complete_ip:
                            origen = str(tok[0]).replace(" ", "")
                            #if the ip found is a county, puts it in the vector
                            if origen[4] == "0":
                                if origen[0:2] == self.province_id:
                                    if origen not in node_ips:
                                        node_ips.append(origen)
                        if str(tok[0]).replace(" ","") == complete_ip:
                            neighbor = (str(tok[1]).replace(" ",""),str(tok[2]).replace(" ",""),str(tok[3]).replace(" ",""),1)
                            ip = str(tok[1]).replace(" ","")
                            if self.complete_ip == complete_ip:
                                neighbors.append(neighbor)
                                self.direct_neighbors.append(ip)
                            elif ip[4] == "0":
                                neighbors.append(neighbor)
                        if str(tok[1]).replace(" ","") == complete_ip:
                            neighbor = (str(tok[0]).replace(" ",""),str(tok[2]).replace(" ",""),str(tok[3]).replace(" ",""),0)
                            ip = str(tok[0]).replace(" ","")
                            if self.complete_ip == complete_ip:
                                neighbors.append(neighbor)
                                self.direct_neighbors.append(ip)
                            elif ip[4] == "0":
                                neighbors.append(neighbor)
        if complete_ip == self.complete_ip:
            self.neighbors = neighbors
            self.node_ips = node_ips
        self.append_connections(complete_ip,neighbors)
        file.close()
     
    def append_connections(self,ip,neighbors):
        rout = {}
        rout[ip] = ("0",ip)
        for index in neighbors:
            if index[0][4] == "0":
                rout[index[0]] = (index[1],ip)
                #print(rout[index[0]])
        self.ips_connections[ip] = rout
            
    # This method creates a socket that connect with other router
    def connect_sock(self,host,port):
        # create TCP socket
        print('Creating socket...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('[Socket created]')

        # adress of my neighbor
        neighbor_address = (host,port)
        print(f'Connecting to: {host} : {port}...')

        # connect to neighbor
        # Needs to be in a cycle because the neighbour may not be up yet
        while True:
            try:
                sock.connect(neighbor_address)
                print(f'Connected to: {host} : {port}...')
                break
            except OSError as err:
                time.sleep(3)
                print(f"Neighbor at ({host},{port}) is not up...")

        self.thread_lock.acquire()
        self.sockets_list.append(sock)
        self.thread_lock.release()

        return sock

    # This method creates a socket that binds to wait for connections
    def bind_sock(self, host, port):
        # create TCP socket
        print('Creating socket...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('[Socket created]')

        # bind server to the address
        print(f'Binding at: {host} : {port}...')
        sock.bind((host, port))
        print(f'[Binded at: {host} : {port}]')
        
        self.thread_lock.acquire()
        self.sockets_bind.append(sock)
        self.thread_lock.release()
        
        return sock
    
    # This method creates a queue that recieve and other that send for each connection
    def create_thread_safe_queue(self, thread_count):
        for i in range(0, thread_count):
            # Creates the semaphore for the producer thread
            producer_sem = threading.Semaphore(0)
            self.semaphores_list.append(producer_sem)
            # Creates the reciever queue for each thread
            queue_recv = queue.Queue()
            self.queue_list_recv.append(queue_recv)  
            # Creates the sender queue for each thread
            queue_send = queue.Queue()
            self.queue_list_send.append(queue_send)

    # This method recieve on the sockets that bind
    def rcv_on_bind(self,client_sock,id):
        client_sock.settimeout(0.5)
        while True:
            if not self.queue_list_send[id].empty():
                status = self.send_my_queue_info(id,client_sock)
                if status == 1:
                    break
            try:
                package = client_sock.recv(1024)
            except:
                package = None
            if package: 
                # insert the package in the queue of the list of queues in the given position by the ID
                #self.queue_list_recv[id].put(package.decode('utf-8'))
                package = package.decode("utf-8")
                print(f'Package receive from {client_sock.getsockname()}')
                self.queue_list_recv[id].put(package)
                self.semaphores_list[id].release()
                #print(package.decode())

    # This method recieve on the sockets that connect
    def rcv_on_connect(self,my_sock,id):
        my_sock.settimeout(0.5)
        while True:
            if not self.queue_list_send[id].empty():
                status = self.send_my_queue_info(id,my_sock)
                if status == 1:
                    break
            try:
                package = my_sock.recv(1024)
            except:
                package = None
            if package:
                #self.queue_list_recv[id].put(package.decode('utf-8'))
                package = package.decode('utf-8')
                print(f'Package receive from {my_sock.getsockname()}')
                self.queue_list_recv[id].put(package)
                self.semaphores_list[id].release()
                #self.semaphores_list[id].release()


    # This method handle the producer thread. This thread listen for packages
    def handle_connections_producer(self, id):
        # each producer and consumer has an ID
        id = int(id)
        my_info = self.neighbors[id]
        if int(my_info[3]) == 1:
            my_sock = self.bind_sock('localhost',int(my_info[2]))
            my_sock.listen()
            client_sock, client_address = my_sock.accept()
            print(f'Connection recv from: {client_address} in port: {my_info[2]}')
            if my_info[0][2:4] != "00" and  my_info[0][4] == "0":
                self.compute_routing_table() 
            self.rcv_on_bind(client_sock,id)
        else:
            my_sock = self.connect_sock('localhost', int(my_info[2]))
            if my_info[0][2:4] != "00" and  my_info[0][4] == "0":
                self.compute_routing_table()
            self.rcv_on_connect(my_sock,id)

    def update_routing_table(self,package):
        print("relleno de naruto") 

    # This method sends the packages that are in the sender queue
    def send_my_queue_info(self,id,my_sock):
        while not self.queue_list_send[id].empty():
            package = str(self.queue_list_send[id].get())
            print(f'Package sent to {my_sock.getsockname()}')
            if my_sock:
                my_sock.send(package.encode('utf-8'))
    
    # This method handle the consumer thread. This thread send packages.
    # We need to analize the purpose of each package. (0: is a table, 1: is a package, 2 is a desconnection message)
    def handle_connections_consumer(self, id):
        id = int(id)
        while True:
            self.semaphores_list[id].acquire()
            package = self.queue_list_recv[id].get()
            # here we build the package header
            purpose = package[0]
            max_jumps = int(package[1:3])
            actual_jumps = int(package[3:5])
            origin = package[5:10]
            last_router = package[10:15]
            destiny = package[15:20]
            size = len(package)
            message = package[20:size]
            if purpose == "0":
                self.update_routing_table(package)           
            elif purpose == "1":
                actual_jumps += 1
                if len(str(actual_jumps)) == 1:
                    str_actual_jumps = "0" + str(actual_jumps)
                else:
                    str_actual_jumps = str(actual_jumps)
                new_message = "1" + "99" + str_actual_jumps + origin + self.complete_ip + destiny + message
                #if the message goes to another province
                if destiny[0:2] != self.province_id:
                    province = self.province_id + "000"
                    way = self.routing_table.get(province)
                    actual_way = way[1]
                    if actual_way == self.complete_ip:
                        index = self.direct_neighbors.index(province)
                        self.queue_list_send[index].put(new_message)
                    else:
                        if actual_way in self.routers_disconnected:
                            new_message = "1" + "99" + "0" + self.complete_ip + self.complete_ip + origin + "nack"
                            for index in range(len(new_message),1024):
                                new_message+= "$"
                            self.queue_list_recv[id].put(new_message)
                            self.semaphores_list[id].release()
                            continue
                        if actual_way in self.direct_neighbors:
                            index = self.direct_neighbors.index(actual_way)
                            self.queue_list_send[index].put(new_message)
                            
                        else:
                            while True:
                                if actual_way in self.direct_neighbors:
                                    index = self.direct_neighbors.index(way[1])
                                    self.queue_list_send[index].put(new_message)
                                    break
                                else:
                                    way = self.routing_table.get(actual_way)
                                    actual_way = way[1]      
                # if the message goes to the same county
                elif destiny[2:4] == self.cantonal_id:
                    if destiny in self.direct_neighbors:
                        index = self.direct_neighbors.index(destiny)
                        self.queue_list_send[index].put(new_message)
                #consumer the message goes to another county
                elif destiny[2:4] != self.cantonal_id:
                    county = destiny[0:4] + "0"                                     
                    way = self.routing_table.get(county)
                    actual_way = way[1]
                    if actual_way in self.routers_disconnected:
                        new_message = "1" + "99" + "0" + self.complete_ip + self.complete_ip + origin + "nack"
                        for index in range(len(new_message),1024):
                            new_message+= "$"
                        self.queue_list_recv[id].put(new_message)
                        self.semaphores_list[id].release()
                        continue
                    #if I have a direct way to the other router
                    if actual_way == self.complete_ip:
                        index = self.direct_neighbors.index(county)                
                        self.queue_list_send[index].put(new_message)
                    else:
                        #if the router has a direct way to the other router
                        if actual_way in self.direct_neighbors:
                            index = self.direct_neighbors.index(way[1])
                            self.queue_list_send[index].put(new_message)
                        else:
                            while True:
                                if actual_way in self.direct_neighbors:
                                    index = self.direct_neighbors.index(way[1])
                                    self.queue_list_send[index].put(new_message)
                                    break
                                else:
                                    way = self.routing_table.get(actual_way)
                                    actual_way = way[1]                 
            elif purpose == "2":
                self.forward_disconnect_message(origin, package)
                
                if origin not in self.routers_disconnected:
                    self.routers_disconnected.append(origin)
                    
                print("Disconnections:")    
                print(self.routers_disconnected)
                
                try:
                    if origin in self.node_ips:
                        self.thread_lock.acquire()
                        self.node_ips.remove(origin)    
                        self.thread_lock.release()                               
                except:
                    print("This router is not longer in the list")                  
                
                print("New routing table:")
                self.compute_routing_table()

         
    # This method creates the producer and consumer threads    
    def create_threads(self, producers_list, consumers_list):
        # note: all the lists have the same size
        number_of_conections = len(self.neighbors)
        self.create_thread_safe_queue(number_of_conections)
        id = 0
        while id < number_of_conections:
            try:
                # creates receivers (producers) threads
                producer_thread = threading.Thread(target=self.handle_connections_producer,
                                                   args=(str(id)))
                producer_thread.setDaemon(True)
                producer_thread.start()
                # saves all the producers threads in a list
                producers_list.append(producer_thread)

                # creates senders (consumers) threads
                consumer_thread = threading.Thread(target=self.handle_connections_consumer,
                                                   args=(str(id)))
                consumer_thread.setDaemon(True)
                consumer_thread.start()
                # saves all the producers threads in a list
                consumers_list.append(consumer_thread)
                id+=1
            except OSError as err:
                print(err)
    
    def read_all_connections(self):
        for index in self.node_ips:
            if index != self.complete_ip:
                if index[2:4] != "00":
                    self.read_conf_router(index)

 # This method makes a join for each thread created
    def join_threads(self, producers_list, consumers_list):
        for consumer, producer in zip(producers_list, consumers_list):
            consumer.join()
            producer.join()
            
    # This method creates all the threads and makes the join for each thread
    def create_connections(self):
        self.read_all_connections()
        try:
            producers_list = []
            consumers_list = []
            self.create_threads( producers_list, consumers_list)
            self.join_threads(producers_list, consumers_list)

        except KeyboardInterrupt:
            self.shutdown_router()

    # This method generates the disconnected message that the router sends when it shutdown        
    def send_disconnect_message(self):
        iter = 0
        package = "2"
        package += "99"
        package += "00"
        package += self.complete_ip
        package += self.complete_ip
        package += self.complete_ip
        for index2 in range(20,1024):
            package+= "$"
        for index in self.neighbors:
            if index[0][2:4] != "00":
                self.queue_list_send[iter].put(package)
            iter += 1
    
     # This method sends the disconnection message           
    def forward_disconnect_message(self,router_disconnected,package):
        iter = 0
        for index in self.neighbors:
            #if the router was already disconnected (imposible)
            if router_disconnected in self.routers_disconnected:
                break
            if index[0][2:4] != "00" and index[0][4] == "0":
                if index[0] not in self.routers_disconnected:
                    self.queue_list_send[iter].put(package)
            iter+=1
            
    # This method close each socket created in the router
    def shutdown_router(self):
        print('\nShutting down router\n')
        self.send_disconnect_message()
        time.sleep(1)  
              
        for sock in self.sockets_bind:
            sock_Address = sock.getsockname()
            print(f'Socket {sock_Address} closed')
            sock.close()
        print('\n[Router off]')
        
        #-----------------LINK STATE PROTOCOL -------------------
        
      # used to compute Djisktra  
    def fill_matrix(self):
        net_graph = {}
        for row in self.node_ips:
            net_graph[row] = {}
            # if I go from me to myself, my cost is 0
            for col in self.node_ips:
                 if col == row:
                    net_graph[row][col] = 0
        #else, find all the costs from the second value of the routing table        
        for row in self.node_ips:
            for col in self.node_ips:
                if row in self.ips_connections:
                    if col in self.ips_connections[row]:
                        cost = self.ips_connections[row][col][0]
                        net_graph[row][col] = int(cost)
                else:
                    #if it can't find a way, cost will be INF
                    net_graph[row][col] = self.INF
        return net_graph 
    
      # finds the closest node to where you want to go
    def find_min_distance(self, my_table, visited_nodes):
        min = self.INF
        index = 0
        for node in self.node_ips:
            if my_table[node][0] < min and visited_nodes[node] == False:
                min = my_table[node][0]
                index = self.node_ips.index(node)
        return self.node_ips[index]
    
    #Djisktra algorithm
    def djisktra_algorithm(self):
        my_table = {}
        visited_nodes = {}
        net_graph = self.fill_matrix()
        #initialize matrix with infinite values
        for node in self.node_ips:
            my_table[node] = (self.INF, "00000")          
            visited_nodes[node] = False
            
        my_table[self.complete_ip] = (0, self.complete_ip)   
        for node1 in self.node_ips:
            min_node = self.find_min_distance(my_table, visited_nodes)
            visited_nodes[min_node] = True
            for node2 in self.node_ips:
                if node2 in net_graph[min_node]:       
                    if int(net_graph[min_node][node2]) > 0:
                        if visited_nodes[node2] == False:     
                            updated_cost = int(net_graph[min_node][node2]) + my_table[min_node][0]
                            if int(my_table[node2][0]) > updated_cost:                          
                                my_table[node2] = (updated_cost, min_node)                   
        return my_table
    
    # calculates the best route for every router
    def compute_routing_table(self):
        self.thread_lock.acquire()
        if self.routing_done == False:
            seconds = int(self.complete_ip[3])
            time.sleep(seconds*0.5)
            self.routing_table = self.djisktra_algorithm()
            self.routing_done = True
            print(self.routing_table)
        self.thread_lock.release()
            
def main():
    temp = str(sys.argv[1])
    if len(temp) == 1:
        provincial_id = "0" + temp
    else:
        provincial_id = temp
    temp2 = str(sys.argv[2])
    if len(temp2) == 1:
        cantonal_id = "0" + temp2
    else:
        cantonal_id = temp2
        
    complete_ip = provincial_id + cantonal_id + "0"
    print("This cantonal router is: ", complete_ip)
    router = Router_Cantonal(complete_ip,provincial_id,cantonal_id)
    router.read_conf_router(router.complete_ip)
    router.create_connections()

    
if __name__ == '__main__':
    main()
