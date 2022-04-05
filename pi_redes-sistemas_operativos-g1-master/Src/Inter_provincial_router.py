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

class Router_Provincial():
    # init all the server info
    def __init__(self,complete_ip,province_id):
        self.province_id = province_id      # the id of the router
        self.complete_ip = complete_ip      # the logic ip of the router
        self.neighbors = []                 # list with the information of each neighbour(ip, port, cost, who binds)
        self.who_i_have = []                # list of the ip of each neighbour
        self.sockets_list = []              # list to save the sockets that connect
        self.sockets_bind = []              # list to save the sockets that bind
        self.sockets_by_id = []             # list of sockets by id
        self.queue_list_recv = []           # list of queues to receive all the message for each connection
        self.queue_list_send = []           # list of queues to send all the message for each connection
        self.semaphores_list = []           # list to save the semaphores to producers
        self.routers_disconnected = []      # list to save the routers that have disconnected
        self.thread_lock = threading.Lock() # lock to protect the threads
        self.complete_memory = memory.MemoriaCompleta(1,self.complete_ip) # The memory system of the router (here we have the routing table)

    # Read the configuration file
    # This method search for the router and its connections in the file
    def read_conf_router(self):
        file = open("red_conf.csv","r")
        lines = file.readlines()
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
                        if str(tok[0]).replace(" ","") == self.complete_ip:
                            my_port = {}
                    if type == False :
                        tok = index.strip().split(",")
                        if str(tok[0]).replace(" ","") == self.complete_ip:
                            neighbor = (str(tok[1]).replace(" ",""),str(tok[2]).replace(" ",""),str(tok[3]).replace(" ",""),1)
                            self.neighbors.append(neighbor)

                        if str(tok[1]).replace(" ","") == self.complete_ip:
                            neighbor = (str(tok[0]).replace(" ",""),str(tok[2]).replace(" ",""),str(tok[3]).replace(" ",""),0)
                            self.neighbors.append(neighbor)
        print(self.neighbors)
        file.close()

    # This method search for the lowest cost connection of the frontier routers
    def define_my_frontier_connection(self):
        lowest = ("0","100","0",0)
        for index in self.neighbors:
            if index[0][2:4] != "00":
                if int(lowest[1]) > int(index[1]):
                    lowest = index
        return lowest

    # This method helps to know where on the page the search IP is located
    def know_order(self,ip):
        id = int(ip[0:2])
        if id % 2 == 0:
            temp_id = id-1
            if temp_id == int(self.province_id):
                return 0
            else:
                return 29
        else:
            temp_id = id+1
            if temp_id == self.province_id:
                return 0
            else:
                return 0

    # This method stores in the memory the routing table
    def init_memory(self):
        for index in self.neighbors:
            if index[0] not in self.routers_disconnected:
                self.who_i_have.append(index[0])
                if index[0][2:4] == "00":
                    id = self.know_order(index[0])
                    new_pagina = self.complete_memory.conseguir_pagina(index[0])
                    iter = 0
                    way = index[0]
                    for index2 in range (5+id,10+id):
                        new_pagina[index2] = way[iter].encode('utf-8')
                        iter+=1
                    iter = 0
                    cost = index[1]
                    if len(cost)==1:
                        temp_cost = "0"
                        temp_cost+= cost
                        cost = temp_cost
                    for index2 in range(10+id,12+id):
                        new_pagina[index2] = cost[iter].encode('utf-8')
                        iter+=1
                    iter=0
                    host = "000localhost"
                    for index2 in range(12+id,24+id):
                        new_pagina[index2] = host[iter].encode('utf-8')
                        iter+=1
                    iter =0
                    port = str(index[2])
                    if len(port) < 5:
                        temp_port = "0"
                        temp_port+= port
                        port = temp_port
                    for index2 in range(24+id,29+id):
                        new_pagina[index2] = port[iter].encode('utf-8')
                        iter+=1
                    self.complete_memory.modificar_pagina(index[0],new_pagina)

            info = self.define_my_frontier_connection()
            new_pagina = self.complete_memory.conseguir_pagina("00000")
            iter = 0
            way = info[0]
            for index2 in range (5+29,10+29):
                new_pagina[index2] = way[iter].encode('utf-8')
                iter+=1
            iter = 0
            cost = info[1]
            if len(cost)==1:
                temp_cost = "0"
                temp_cost+= cost
                cost = temp_cost
            for index2 in range(10+29,12+29):
                new_pagina[index2] = cost[iter].encode('utf-8')
                iter+=1
            iter=0
            host = "000localhost"
            for index2 in range(12+29,24+29):
                new_pagina[index2] = host[iter].encode('utf-8')
                iter+=1
            iter =0
            port = str(info[2])
            if len(port) < 5:
                temp_port = "0"
                temp_port+= port
                port = temp_port
            for index2 in range(24+29,29+29):
                new_pagina[index2] = port[iter].encode('utf-8')
                iter+=1
            self.complete_memory.modificar_pagina("00000",new_pagina)
        
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
    def rcv_on_bind(self,client_sock,clien_address,id):
        who_sends = self.neighbors[id]
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
        who_sends = self.neighbors[id]
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
    
    # This method sends the routing table. This is for the Vector Distance Protocol
    def send_my_table(self,id):
        dicc_to_send = {}
        who_info = self.neighbors[id]
        dicc_to_send = self.get_my_complete_table()
        dicc_to_send_string = json.dumps(dicc_to_send)
        complete_string = "0"
        complete_string += "99"
        complete_string += "00"
        complete_string += self.complete_ip
        complete_string += self.complete_ip
        complete_string += who_info[0]
        complete_string += dicc_to_send_string
        for index in range(len(complete_string),1024):
            complete_string += "$"
        self.queue_list_send[id].put(complete_string)

    # This method pepares the updated routing table to be send and puts it in the sender queue
    def prepare_my_update(self,my_update):
        iter = 0
        for index in self.neighbors:
            if index[0][2:4] == "00":
                if index[0] in self.who_i_have:
                    update_message = ""
                    string = json.dumps(my_update)
                    update_message+= "0"
                    update_message+= "99"
                    update_message+= "00"
                    update_message+= self.complete_ip
                    update_message+= self.complete_ip
                    update_message+= index[0]
                    update_message+= string
                    for index in range(len(update_message),1024):
                        update_message+="$"
                    self.queue_list_send[iter].put(update_message)
            iter+=1
    
    # This method return the routing table
    def get_my_complete_table(self):
        update_table = {}
        for index in self.who_i_have:
            if index[2:4]=="00":
                page = self.complete_memory.conseguir_pagina(index)
                #print(page)
                id = self.know_order(index)
                table_cost = page[10+id:12+id]
                string_cost = str(table_cost[0].decode('utf-8')) + str(table_cost[1].decode('utf-8'))
                update_table[index] = string_cost
        return update_table

    # This method analize the table and makes the updates needed according to the
    # routing tables sent by its neighbours           
    def analyze_my_table(self,neighboor_table,peso,who_sends):
        self.thread_lock.acquire()
        number = 0
        actual_table = "{"
        for index in neighboor_table:
            if index == "{":
                number+= 1
            else:
                if (number >= 1) & (index != "$"):
                    actual_table +=  index   
        dicc_recv =  json.loads(actual_table)
        new_tupla = ()
        for index in dicc_recv:
            if index != self.complete_ip:
                if index not in self.routers_disconnected:
                    if index in self.who_i_have:
                        my_info = self.complete_memory.conseguir_pagina(index)
                        index_peso = dicc_recv[index]
                        id = self.know_order(index)
                        last_way =  my_info[5+id:10+id]
                        last_way_str = ""
                        for index2 in last_way:
                            last_way_str+= index2.decode('utf-8')
                        table_cost = my_info[10+id:12+id]
                        string_cost = str(table_cost[0].decode('utf-8')) + str(table_cost[1].decode('utf-8'))
                        if (int(index_peso)+int(peso)) < int(string_cost):
                            new_tupla = (who_sends,str(int(index_peso) + int(peso)))
                            print(f'UPDATING my table ["{index}" : {last_way_str},{string_cost}] to ["{index}":{new_tupla}]')
                            iter = 0
                            for index2 in range(5+id,10+id):
                                my_info[index2] = who_sends[iter].encode('utf-8')
                                iter+=1
                            iter=0
                            new_cost = new_tupla[1]
                            for index2 in range(10+id,12+id):
                                if len(new_cost) == 1:
                                    my_info[index2] = "0".encode('utf-8')
                                    my_info[index2+1] = new_cost.encode('utf-8')
                                    break
                                else:
                                    my_info[index2] = new_cost[iter].encode('utf-8')
                                iter+=1
                            iter=0
                            self.complete_memory.modificar_pagina(index,my_info)
                            new_update = self.get_my_complete_table()
                            self.prepare_my_update(new_update)
                    else:
                        index_peso = dicc_recv[index]
                        new_tupla = (who_sends,str(int(index_peso) + int(peso)))
                        my_info = self.complete_memory.conseguir_pagina(index)
                        id = self.know_order(index)
                        iter = 0
                        cost = new_tupla[1]
                        for index2 in range(5+id,10+id):
                            my_info[index2] = who_sends[iter].encode('utf-8')
                            iter+=1
                    
                        iter = 0
                        str_cost = str(cost)
                        for index2 in range(10+id,12+id):
                            if len(cost) == 1:
                                my_info[index2] = "0".encode('utf-8')
                                my_info[index2+1] = str_cost.encode('utf-8')
                                break
                            else:
                                my_info[index2] = str_cost[iter].encode('utf-8')
                            iter+=1

                        iter = 0
                        self.complete_memory.modificar_pagina(index,my_info)
                        self.who_i_have.append(index)
                        print(f'ADDING a new connection["{index}"] : [{who_sends,cost}]')
                        new_update = self.get_my_complete_table()
                        self.prepare_my_update(new_update)
        print(self.get_my_complete_table())
        self.thread_lock.release()

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
            if my_info[0][2:4] == "00":
                self.send_my_table(id)
                
            self.rcv_on_bind(client_sock,client_address,id)
            #self.send_all_my_adress() 
        else:
            my_sock = self.connect_sock('localhost', int(my_info[2]))
            if my_info[0][2:4] == "00":
                self.send_my_table(id)
            self.rcv_on_connect(my_sock,id)
            #self.send_all_my_adress() 
            # accepts all the connections received

    # This method sends the packages that are in the sender queue
    def send_my_queue_info(self,id,my_sock):
        while not self.queue_list_send[id].empty():
            package = str(self.queue_list_send[id].get())
            print(f'Package sent to {my_sock.getsockname()}')
            my_sock.send(package.encode('utf-8'))
    
    # This method handle the consumer thread. This thread send packages.
    # We need to analize the purpose of each package. (0: is a table, 1: is a package, 2 is a desconnection message)
    def handle_connections_consumer(self, id):
        id = int(id)
        while True:
            self.semaphores_list[id].acquire()
            package = self.queue_list_recv[id].get()
            if package == "-1":
                break
            purpose = package[0]
            max_jumps = int(package[1:3])
            actual_jumps = int(package[3:5])
            origin = package[5:10]
            last_router = package[10:15]
            destiny = package[15:20]
            size = len(package)
            message = package[20:size]
            # Package that needs to be send
            if purpose == "1":
                if actual_jumps == max_jumps:
                    print("Message discarted because of excesive jumps")
                else:
                    actual_jumps+=1
                    str_actual_jumps = ""
                    if len(str(actual_jumps)) == 1:
                    	str_actual_jumps = "0" + str(actual_jumps)
                    last_router = self.complete_ip
                    new_message = purpose + str(max_jumps) + str_actual_jumps + origin + last_router + destiny + message
                    if destiny[0:2] == self.province_id:
                        page = self.complete_memory.conseguir_pagina("00000")
                        by_who = ""
                        for index in range(34,39):
                            by_who += page[index].decode('utf-8')
                        self.thread_lock.acquire()
                        index = self.who_i_have.index(by_who)
                        self.thread_lock.release()
                        self.queue_list_send[index].put(new_message)
                    else:
                        province = destiny[0:2] + "000"
                        page = self.complete_memory.conseguir_pagina(province)
                        by_who = ""
                        index2 = self.know_order(province)
                        for index in range(5+index2,10+index2):
                            by_who += page[index].decode('utf-8')
                        self.thread_lock.acquire()
                        index = self.who_i_have.index(by_who)
                        self.thread_lock.release()
                        self.queue_list_send[index].put(new_message)
            # Table sent from a neighbour (need to be analize to update the routing table)
            elif purpose == "0":
                if origin[2:4] == "00":
                    info = self.complete_memory.conseguir_pagina(origin)
                    plus_id = self.know_order(origin)
                    cost = info[10+ plus_id : 12+plus_id]
                    str_cost = str(cost[0].decode('utf-8')) + str(cost[1].decode('utf-8'))
                    self.analyze_my_table(package,str_cost,origin)
            # A disconnection message
            elif purpose == "2":
                #self.rework_my_table(origin,package)
                self.forward_disconnect_message(origin,package)
                self.routers_disconnected.append(origin)
                self.clear_my_table()
                self.who_i_have.clear()
                self.init_memory()
                table = self.get_my_complete_table()
                self.prepare_my_update(table)
                print(table)
   
    # This method clear the routing table            
    def clear_my_table(self):
        self.thread_lock.acquire()
        for index in self.who_i_have:
            if index[2:4] == "00":
                id = self.know_order(index)
                page = self.complete_memory.conseguir_pagina(index)
                for index2 in range(5+id,28+id):
                    page[index2] = "0".encode('utf-8')
                self.complete_memory.modificar_pagina(index,page)
        self.thread_lock.release()

    # This method sends the disconnection message           
    def forward_disconnect_message(self,router_disconnected,package):
        iter = 0
        for index in self.neighbors:
            if router_disconnected in self.routers_disconnected:
                break
            if index[0][2:4] =="00":
                if index[0] != router_disconnected:
                    if index[0] not in self.routers_disconnected:
                        self.queue_list_send[iter].put(package)
            iter+=1
         
        
    def rework_my_table(self,router_disconnected,package):
        self.thread_lock.acquire()
        router_to_eliminate = []
        if router_disconnected not in self.routers_disconnected:
            if router_disconnected in self.who_i_have:
                if router_disconnected[2:4] == "00":
                    for index in self.who_i_have:
                        if index[2:4] == "00":
                            page = self.complete_memory.conseguir_pagina(index)
                            id = self.know_order(index)
                            destiny = ""
                            for index4 in range(0+id,5+id):
                                destiny+= page[index4].decode('utf-8')
                            way = ""
                            for index2 in range(5+id,10+id):
                                way += page[index2].decode('utf-8')
                            if way == router_disconnected:
                                if destiny != router_disconnected:
                                    is_in = False
                                    old_neigh = None
                                    for neigh in self.neighbors:
                                        if neigh[0] == destiny:
                                            is_in = True
                                            old_neigh = neigh
                                    if is_in == True:
                                        iter = 0
                                        for index2 in range(5+id,10+id):
                                            page[index2] = destiny[iter].encode('utf-8')
                                            iter+=1
                                        str_cost = old_neigh[1]
                                        iter = 0
                                        for index3 in range(10+id,12+id):
                                            if len(str_cost) == 1:
                                                page[index3] = "0".encode('utf-8')
                                                page[index3+1] = str_cost[iter].encode('utf-8')
                                                break
                                            else:
                                                page[index3] = str_cost[iter].encode('utf-8')
                                            iter += 1
                                        print(f"UPDATING MY TABLE [{destiny}:{destiny},{str_cost}]")
                                    else:
                                        for index2 in range(5+id,10+id):
                                            page[index2] = "0".encode('utf-8')
                                        for index3 in range(10+id,12+id):
                                            page[index3] = "0".encode('utf-8')
                                        print(f"ELIMINATING THIS CONNECTION FROM MY TABLE [{destiny}]")
                                        router_to_eliminate.append(destiny)
                                                    
                                else:
                                    for index2 in range(5+id,10+id):
                                        page[index2] = "0".encode('utf-8')
                                    for index3 in range(10+id,12+id):
                                        page[index3] = "0".encode('utf-8')
                                    router_to_eliminate.append(router_disconnected)
                                    print(f"ELIMINATING THIS CONNECTION FROM MY TABLE [{destiny}]")
                                    self.complete_memory.modificar_pagina(index,page)
                else:
                    page = self.complete_memory.conseguir_pagina("00000")
                    page_router = ""
                    for index in range(34,39):
                        page_router += page[index].decode('utf-8')
                    if page_router == router_disconnected:
                        new_data = self.define_my_frontier_connection()
                        iter = 0
                        ip = new_data[0]
                        for index2 in range(34,39):
                            page[index2] = ip[iter].encode('utf-8')
                            iter += 1
                        cost = str(new_data[1])
                        ter = 0
                        for index3 in range(39,41):
                            if len(cost) == 1:
                                page[index3] = "0".encode('utf-8')
                                page[index3+1] = ip[iter].encode('utf-8')
                                break
                            else:
                                page[index3] = ip[iter].encode('utf-8')
                            iter += 1
                    self.complete_memory.modificar_pagina("00000",page)
            self.routers_disconnected.append(router_disconnected)
            iter = 0
            for index5 in self.neighbors:
                if index5[0][2:4] =="00":
                    if index5[0] != router_disconnected:
                        if index5[0] not in self.routers_disconnected:
                            self.queue_list_send[iter].put(package)
                iter+=1
            iter = 0
            for index6 in self.neighbors:
                if index6[0] not in router_to_eliminate:
                    if index6[0][2:4] == "00":
                        print(index6[0])
                        self.send_my_table(iter)
                iter+=1
        for index in router_to_eliminate:
            self.who_i_have.remove(index)
        self.thread_lock.release()

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
                
    # This method makes a join for each thread created
    def join_threads(self, producers_list, consumers_list):
        for consumer, producer in zip(producers_list, consumers_list):
            consumer.join()
            producer.join()
            
    # This method creates all the threads and makes the join for each thread
    def create_connections(self):
        print("Creating connections")
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
            if index[0][2:4] == "00":
                if index[0] in self.who_i_have:
                    self.queue_list_send[iter].put(package)
            iter += 1
            
    # This method close each socket created in the router
    def shutdown_router(self):
        print('\nShutting down router\n')
        self.send_disconnect_message()
        time.sleep(1)  
               
        for sock in self.sockets_list:
            sock_Address = sock.getsockname()
            print(f'Socket {sock_Address} closed')
            sock.close()
            
        for sock in self.sockets_bind:
            sock_Address = sock.getsockname()
            print(f'Socket {sock_Address} closed')
            sock.close()
            
        print('\n[Router off]')


def main():
    temp = str(sys.argv[1])
    if len(temp) == 1:
        province_id = "0" + temp
    else:
        province_id = temp
    complete_ip = province_id + "000"
    router = Router_Provincial(complete_ip,province_id)
    router.read_conf_router()
    router.init_memory()
    router.create_connections()

    
if __name__ == '__main__':
    main()
