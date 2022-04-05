import re
import csv
import socket
import random
from os import system
CREDENTIAL_IP = 'localhost'
CREDENTIAL_PORT = 2121
SERVER_IP = 'localhost'
SERVER_PORT = 5003
CLIENT_TIMEOUT = 5
class Client:
    # init all the connection info
    def __init__(self):
        self.UDP_sock = None    # Socket for UDP server
        self.TCP_sock = None    # Socket for TCP server
        self.document_name = ""
        self.packages = []  #Array to save all the packages
        self.total_packages = 0

    # creates client UDP socket
    def configure_client_UDP(self):
        # create UDP socket 
        print('\nCreating UDP socket...')
        self.UDP_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print('[Socket created]\n')

    # creates client TCP socket
    def configure_client_TCP(self):
        # create TCP socket
        print(f'Creating TCP socket...')
        self.TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (CREDENTIAL_IP, CREDENTIAL_PORT)
        self.TCP_sock.connect(server_address)
        print(f'Socket created\n')

    # send user info to log in
    def interact_with_server_TCP(self):
        try:
            message = input("User_Name: ")
            message += ','
            password = input("Password: ")
            message+=password
            self.configure_client_TCP()
            # Send data
            self.TCP_sock.sendall(message.encode())

            # Look for the response
            data = self.TCP_sock.recv(1024)
            data = data.decode()
            if data == "1":
                print(f'  \n--Authentication Success')
            else:
                print(f'  \n--Authentication Denied')
            
            return data

        finally:
            # close socket
            print('\nClosing TCP socket...')
            self.TCP_sock.close()
            print('[Socket closed]')
    
    # used to send packages with the data to the server    
    def interact_with_server_UDP(self):
        print("Enviando documento....")
        try:
            # connect to server and send the number of packages
            number_of_packages = str(len(self.packages))
                # removes all the commas in the message, they don´t need to be counted
            number_of_packages = self.fill_with_trash(number_of_packages,1024)
            self.UDP_sock.sendto(number_of_packages.encode('utf-8'), (SERVER_IP, SERVER_PORT))
            
            # receive new port to interact with
            new_port, server_address = self.UDP_sock.recvfrom(1024)
            new_port = new_port.decode('utf-8')
            new_port = re.sub('\$',"",new_port)
            # send packages to server
            self.send_my_packages(new_port)

        except OSError as err:
            print(err)

        finally:
            # close socket
            self.UDP_sock.close()
            print('[Socket closed]')

    # send all the client packages
    def send_my_packages(self, new_port):
        #create UDP socket
        missing_random_package = random.randint(0,len(self.packages))
        message = ""
        #send all the packages to the server
        for i in range(0, len(self.packages)-2):
            if missing_random_package != i:
                message = self.packages[i]
                self.UDP_sock.sendto(message.encode('utf-8'), (SERVER_IP, int(new_port)))
        self.UDP_sock.settimeout(CLIENT_TIMEOUT)
        try: 
            while True:
                # Recieve the missing packages
                package_missing, server_address = self.UDP_sock.recvfrom(1024)
                package_missing = package_missing.decode('utf-8')
                package_missing = re.sub('\$',"",package_missing)
                if package_missing == "n":
                    break
                else:
                    print(f"Server asked for: {package_missing}")
                    number_of_package = int(package_missing)
                    number_of_package = number_of_package 
                    new_message = self.packages[number_of_package]
                    # Send the missing package to the server
                    self.UDP_sock.sendto(new_message.encode('utf-8'), (SERVER_IP, int(new_port)))
        except KeyboardInterrupt:
            print("Signal received")
        
    # opens the csv file with the vaccinated people info
    def openCSV(self, csvToOpen):
        file_info = ""
        with open(csvToOpen) as csv_archive:
            csv_reader = csv.reader(csv_archive, delimiter=',')
            # for every line in the csv
            for line in csv_reader:
                #for all the chars in each line
                for i in range(0, len(line)):
                    # append a comma to every position in line
                    file_info += line[i] + "," 
                file_info = file_info[:-1]
                # append a line jump at the end of every line
                file_info += "\n"            
        return file_info

    # creates all the packages with the correct size
    def create_packages(self, file_info):
        max_size = 1020
        # array will store all the packages
        all_packages = []
        package = ""
        # go over every char in file info
        for i in range(0, len(file_info)):
            if i % max_size == 0 and i != 0:
                # add the package to all the packages
                all_packages.append(package)
                package = "" 
            package += file_info[i] #concatenate the info in the i position to a package                
        all_packages.append(package)
        number_of_packages = len(all_packages)
        all_packages[number_of_packages-1] = self.fill_with_trash(package, max_size)
        return all_packages

    def enumerate_packages(self, all_packages):
        # if the package amount is of one digit (0001), add three 0
        # if the package amount is of tow digits (0010), add two 0
        # if the package amount is of three digits (0100), add one 0
        switcher = {1: "000" , 2: "00" , 3: "0" }
        message = ""
        for i in range(0, len(all_packages)):
            message = str(i)
            # if the sms size is less than 4 (4 = max amount of digits for the label) 
            if len(message) < 4:
                # apply the switcher
                all_packages[i] = switcher[len(message)] + str(i) + all_packages[i]
            else:
                all_packages[i] = str(i) + all_packages[i]
        return all_packages
         
    # fill the last message with $$$ if needed     
    def fill_with_trash(self,message, package_size):
        package_to_complete = message
        size_package_complete = len(package_to_complete)
        bytes_needed = "$" * (package_size - size_package_complete)
        package_to_complete+=bytes_needed
        return package_to_complete
        
    #Create the packages
    def build(self):
        file_information = self.openCSV(self.document_name)
        print("Procesando documento...")
        all_packages = self.create_packages(file_information)
        self.packages = self.enumerate_packages(all_packages)
        print("Documento procesado.")

    def run_menu(self):
        condition = True
        #response = self.interact_with_server_TCP()
        response = '1' 
        if response == '1':
            while(condition):
                self.document_name = input("Nombre del documento a enviar: ")
                self.build()
                self.configure_client_UDP()
                self.interact_with_server_UDP()
                print("Documento enviado")
                condicion = input("Desea salirse del programa? (Si/No)")
                if condicion == 'Si':
                    condition = False
                else:
                    system('clear')
        

def main():
    client = Client()
    client.run_menu()
    # TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_address = ('localhost', 5080)
    # TCP_sock.connect(server_address)
    # TCP_sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server_address = ('localhost', 5082)
    # TCP_sock2.connect(server_address)
    # mensaje = "01012"
    # TCP_sock.send(mensaje.encode())
    # package = TCP_sock2.recv(1024)
    # print(package)

if __name__ == '__main__':
    main()
