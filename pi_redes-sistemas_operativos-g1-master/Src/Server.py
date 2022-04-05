import re
import socket
import queue
import threading
import sys
import time
MAX_PIPE_SIZE = 5000000
TIMEOUT_VALUE = 2
class Area_Server():
    # init all the server info
    def __init__(self, host):
        self.port = 0                               # host port of the server
        self.host = host                            # host address of the server
        self.sock = None                            # server Socket that recieve packages from clients
        self.area_id = ""                           # the ID of the area
        self.neighbors = []                         # the neighbours of the server
        self.province_id = ""                       # the province ID
        self.cantonal_id = ""                       # the cantonal ID
        self.complete_ip = ""                       # the complete IP of the server
        self.threads_port = 9100                    # initial thread amount
        self.server_handler = None                  # thread that controls the server
        self.my_router_handler = None               # thread that controls the connections with the router
        self.socket_lock = threading.Lock()         # lock to avoid race conditions
        self.queue_to_be_send = queue.Queue()       # queue to stores the packages to be send
    
    # Read the configuration file
    # This method search for the server and its connections in the file
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
                            self.port = int(tok[1])
                    if type == False :
                        tok = index.strip().split(",")
                        if str(tok[0]).replace(" ","") == self.complete_ip:
                            neighbor = (str(tok[1]).replace(" ",""),str(tok[2]).replace(" ",""),str(tok[3]).replace(" ",""),1)
                            self.neighbors.append(neighbor)

                        if str(tok[1]).replace(" ","") == self.complete_ip:
                            neighbor = (str(tok[0]).replace(" ",""),str(tok[2]).replace(" ",""),str(tok[3]).replace(" ",""),0)
                            self.neighbors.append(neighbor)
        file.close()
        print(self.neighbors)

    # protect the port with the lock created
    def get_port(self):
        self.socket_lock.acquire()
        my_port = self.threads_port
        self.threads_port += 1
        self.socket_lock.release()
        return my_port

    # init the server
    def init_server(self):
        # create the UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #bind server to the adress
        self.sock.bind((self.host, self.port))
        print(f'[Server binded to: {self.host} : {self.port}]\n')
        self.listen_connections()

     # receives the client's info from a socket
    def handle_Client(self, number_of_packages_temp, client_address):
        number_of_packages_temp = re.sub('\$',"",number_of_packages_temp)

        number_of_packages = int(number_of_packages_temp)
        my_port = self.get_port()
        my_port_message = self.fill_with_trash(my_port, 1024)
        self.sock.sendto(str(my_port_message).encode('utf-8'), client_address)
        # creates an UDP socket
        my_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # if the connection can't be made before 3 seconds, throw an exception
        my_sock.settimeout(TIMEOUT_VALUE)
        #bind the server
        my_sock.bind((self.host, my_port))
        packages = []
        condition = True
        while condition:
            try:
                # receives the message from the socket
                message, client_address = my_sock.recvfrom(1024)
                print(f"Message received from: {client_address}")
                message = message.decode('utf-8')
                # add the message to the packages
                packages.append(message)
            except:
                print(f"{TIMEOUT_VALUE}seg Timeout expired")
                self.ask_for_missing_packages(packages, number_of_packages, my_sock, client_address)
                end_connection = "n"
                end_connection = self.fill_with_trash(end_connection,1024)
                # end the connection
                my_sock.sendto(end_connection.encode('utf-8'), client_address)
                print("Closed Connection...")
                break

        print('socket closed')
        my_sock.close()
        # put back all the message
        self.rebuild_packages(packages,number_of_packages)

    # This methos ask the client for the missing packages
    def ask_for_missing_packages(self, packages, number_of_packages, my_sock, client_address):
        my_sock.settimeout(TIMEOUT_VALUE)
        while True:
            try:
                missing_packages = self.check_complete_packages(packages, number_of_packages)
                # if there are none missing packages end connection
                if missing_packages != []:
                    print("Packages missed: ",missing_packages)
                    missed_package = ""
                    for i in missing_packages:
                        # find all the missing packages
                        missed_package = str(i)
                        missed_package = self.fill_with_trash(missed_package,1024)
                        # and try to send them again
                        my_sock.sendto(missed_package.encode('utf-8'), client_address)
                        message, client_address = my_sock.recvfrom(1024)
                        message = message.decode('utf-8')
                        packages.append(message)
                        #once they are sent, finish the connection
                else:
                    break
            except:
                print(f"{TIMEOUT_VALUE}seg Timeout expired")
                continue
        return 1

    # stops the server
    def shutdown(self):
        print(f'\nSERVER SOCKET CLOSED')
        print(f'\nShutting down the server...')
        self.sock.close()

    # listen actively for connections
    def listen_connections(self):
        while True:
            try:
                first_connection, client_address = self.sock.recvfrom(1024)
                first_connection = first_connection.decode('utf-8')
                print(f"Connection received from: {client_address}")
                # creates a thread for every client 
                client_thread = threading.Thread(target=self.handle_Client, args=(first_connection, client_address))
                # Set the thread as a secondary thread
                client_thread.daemon = True
                client_thread.start()
            except KeyboardInterrupt:
                self.shutdown()
                break
    
    # This method rebuild the packages sent by the client
    def rebuild_packages(self, all_packages, number_of_packages):
        rebuild_packages = [""] * number_of_packages
        complete_message = ""
        for i in all_packages:
            #deletes the first 4 positions (control bytes)
            package_number = int(i[0:4])
            if package_number == number_of_packages-1:
                i = self.remove_trash(i)
            # concatenate message to print it
            rebuild_packages[package_number] = i
        #build string that is going to be introduced in the pipe
        for i in rebuild_packages:
            message_temp = i[4:len(i)]
            complete_message += message_temp
        vec_to_enroute = self.separate_to_enroute(complete_message)
        self.construct_enroute_messages(vec_to_enroute)
        self.send_to_router(vec_to_enroute)

    # Removes all the trash in the message
    def remove_trash(self, package):
        trash = ""
        message = ""
        for i in package:
            if i == "$": #trash is equal to three consecutive '$' char
                trash += i
                if len(trash) == 3:
                    break
            else:
                trash = ""
            message += i
        message = message[:-3]
        return message

    # check if all the packages were sent
    def check_complete_packages(self, packages, number_of_packages):
        packages_received = [0] * number_of_packages
        packages_missing = []
        package_number = 0
        # if the packages received are less than the number of packages
        # we have to find the missing packages
        if len(packages) <= number_of_packages:
            for i in packages:
                package_number = int(i[0:4]) #gets the number of the package
                packages_received[package_number] = 1

            for i in range(0, len(packages_received)):
                #in case a package is not in the received ones
                if packages_received[i] == 0:
                    packages_missing.append(i)

        return packages_missing

    # Adds thrash to the messages that are going to be sent
    def fill_with_trash(self,message, size_of_package):
        package_to_complete = str(message)
        size_package_complete = len(package_to_complete)
        bytes_needed = "$" * (size_of_package - size_package_complete)
        package_to_complete+=bytes_needed
        return package_to_complete

    # This method separate the complete package sent by the client (line by line)
    def separate_to_enroute(self,complete_package):
        vec_w_messages = []
        temp_space = ""
        for index in range(0,len(complete_package)):
            if complete_package[index] == '\n':
                temp_space+= complete_package[index]
                vec_w_messages.append(temp_space)
                temp_space = ""
            else:
                temp_space+= complete_package[index]
        vec_w_messages.append(temp_space)
        return vec_w_messages
    
    # This method gets the logic IP to put it into the header of the package to send to the router
    def get_logic_ip(self,str_to_separate):
        number_of_comas = 0
        str_temp = ""
        for index in range(0,len(str_to_separate)):
            if str_to_separate[index] == ',':
                number_of_comas+=1
            if number_of_comas > 1 :
                str_temp += str_to_separate[index]
        str_temp = re.sub(',', "", str_temp)
        return str_temp
    
    # This method constuct the header of the package to send to the router
    def construct_enroute_messages(self,vec_to_enroute):
        str_temp = ""
        for index in range (0,len(vec_to_enroute)):
            str_temp+= "1"
            str_temp+= "99"
            str_temp+= "00"
            str_temp+= self.complete_ip
            str_temp+= self.complete_ip
            str_temp+= self.get_logic_ip(vec_to_enroute[index])
            str_temp+= vec_to_enroute[index]
            for index2 in range(len(str_temp),1024):
                str_temp+= "$"
            vec_to_enroute[index] = str_temp
            str_temp = ""

    # 
    def send_to_router(self,vec_to_enroute):
        for index in range(0,len(vec_to_enroute)):
            self.queue_to_be_send.put(vec_to_enroute[index])
    
    def connect_sock(self,host,port):
        # create TCP socket
        print('Creating socket...')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('[Socket created]')
        # adress of my neighbor
        neighbor_address = (host,port)
        print(f'Connecting to: {host} : {port}...')
        # connect to neighbor
        while True:
            try:
                sock.connect(neighbor_address)
                print(f'Connected to: {host} : {port}...')
                break
            except OSError as err:
                time.sleep(3)
                print("Neighbor is not up...")
        return sock

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
        self.sockets_list.append(sock)
        self.thread_lock.release()
        
        return sock
    def send_my_queue_info(self,client_sock):
        while not self.queue_to_be_send.empty():
            package = self.queue_to_be_send.get()
            if package[15:20] == self.complete_ip:
                package2 = package[20:len(package)]
                package2 = re.sub("\$","",package2)
                print(f"Message sent to my area direct from client: {package2}")
            else:
                client_sock.send(package.encode('utf-8'))


    def rcv_on_connect(self,my_sock):
        my_sock.settimeout(0.5)
        while True:
            try:
                if not self.queue_to_be_send.empty():
                    self.send_my_queue_info(my_sock)
                try: 
                    package = my_sock.recv(1024)
                except:
                    package = None   
                if package:
                    package = package.decode('utf-8')
                    #insert the package in the queue of the list of queues in the given position by the ID
                    self.review_ack(package,my_sock)
                    #self.send(ack)
            except KeyboardInterrupt:
                my_sock.close()
                print(f'TCP SOCK CLOSED')
                break

    def rcv_on_bind(self,client_sock,clien_address):
        client_sock.settimeout(0.5)
        try:
            while True:
                if not self.queue_to_be_send.empty():
                    self.send_my_queue_info(client_sock)
                try:
                    package = client_sock.recv(1024)
                except:
                    package = None
                # if the package exits
                if package:
                    package = package.decode('utf-8')
                    self.review_ack(package,client_sock)
                    # insert the package in the queue of the list of queues in the given position by the ID
                    #self.send(ack)
        except KeyboardInterrupt:
            client_sock.close()
            print(f'TCP SOCK CLOSED')
            
    def review_ack(self,package,client_sock):
        purpose = package[0]
        max_jumps = int(package[1:3])
        actual_jumps = int(package[3:5])
        origin = package[5:10]
        last_router = package[10:15]
        destiny = package[15:20]
        size = len(package)
        message = package[20:size]
        message = re.sub("\$","",message)
        if message != "ack":
            if message == "nack":
                print("Error sending message due to no way to destiny")
            else:
                new_package = "1"
                new_package+= "99"
                new_package+= "00"
                new_package+= self.complete_ip
                new_package+= self.complete_ip
                new_package+= origin
                new_package+= "ack"
                for index in range(len(new_package),1024):
                    new_package+="$"
                client_sock.send(new_package.encode('utf-8'))
                print(f'Message received from {origin} message content: \n {message}')
        else:
            print(f'Confirmation message received from {origin}')
            

    def handle_router_connection(self):
        my_info = self.neighbors[0]
        who_binds = my_info[3]
        if who_binds == 1:
            sock = self.bind_sock("localhost",int(my_info[2]))
            sock.listen()
            client_sock, client_address = sock.accept()
            print(f'Connection established with: {client_address} in port: {my_info[2]}')
            self.rcv_on_bind(client_sock,client_address)
        else: 
            sock = self.connect_sock("localhost",int(my_info[2]))
            print(f'Connection established at port {my_info[2]}')
            self.rcv_on_connect(sock)

    def create_threads(self):
        try:
            router_handler = threading.Thread(target=self.handle_router_connection,
                                                   args=())
            router_handler.setDaemon(True)
            self.my_router_handler = router_handler
            router_handler.start()
            server_handler = threading.Thread(target=self.init_server,
                                                   args=())
            server_handler.setDaemon(True)
            self.server_handler = server_handler
            server_handler.start()
            self.join_my_threads()
        except KeyboardInterrupt:
            self.shutdown()

    def join_my_threads(self):
        self.my_router_handler.join()
        self.server_handler.join()
        
        
def main():
    Server = Area_Server('localhost')
    temp= str(sys.argv[1])
    if len(temp) == 1:
        Server.province_id = "0" + temp
    else:
        Server.province_id = temp
    temp = str(sys.argv[2])
    if len(temp) == 1:
        Server.cantonal_id = "0" + temp
    else:
        Server.cantonal_id = temp
    Server.area_id = str(sys.argv[3])
    Server.complete_ip = Server.province_id + Server.cantonal_id + Server.area_id
    print(Server.complete_ip)
    Server.read_conf_router()
    Server.create_threads()

if __name__ == '__main__':
    main()
