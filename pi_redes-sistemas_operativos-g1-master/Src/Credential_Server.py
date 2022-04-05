import socket
import threading

class Credential_Server():

    # init all the server info
    def __init__(self, host, port):
        self.host = host            # Host address
        self.port = port            # Host port
        self.sock = None            # Connection socket
        self.users_information = self.read_file("Usuarios.csv")  # users_information

    #init the server
    def init_server(self):
        # create TCP socket
        print('Creating socket...')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print('[Socket created]\n')

        # bind server to the address
        print(f'Binding server to: {self.host} : {self.port}...')
        self.sock.bind((self.host, self.port))
        print(f'[Server binded to: {self.host} : {self.port}]\n')

    # read the file that includes the users information
    def read_file(self, file_name):
        users_and_password = {} # dictionary for user and password
       
       # open the file with the users information
        with open(file_name) as archive:
            for row in archive:
                split_row = row.split(',')
                # match the user with the password
                users_and_password[split_row[0]] = split_row[1]
        return users_and_password
   
    # verify if the password matches each user
    def verify_user(self, users_credential):
        vec = users_credential.split(',')
        user = vec[0] # the name is in the first position of the array
        password = vec[1] #the password is in the second position
        password += '\n'
        if user in self.users_information:
            # if the user matches the password, continue
            if self.users_information[user] == password:
                print("--Authentication success")
                return True
            else:
                #if not, don't continue
                print("--Fatal: Authentication failed")
        else:
            print("--Fatal: Authentication failed")
        print("--Fatal: Access denied")
        return False

    # receives the client's info from a socket
    def handle_client(self, client_sock, client_address):
        try:
            # receive from de client
            data = client_sock.recv(1024)
            credentials = data.decode()
            response = ""
            # if the user is verified, send an authentication
            if self.verify_user(credentials):
                response = "1"
            else:
                response = "0"
            # send the response
            client_sock.sendall(response.encode('utf-8'))

        except OSError as err:
            print(err)

        finally:
            client_sock.close()
            print(f'Client socket closed for {client_address}\n')

   # listen actively for clients connections
    def listen_connections(self):
        try:

            print('Listening for connections...\n')
            self.sock.listen()
            # accept all the connections received
            while True:
                client_sock, client_address = self.sock.accept()
                print(f'Accepted connection from {client_address}')
                # creat a new thread for every new client 
                c_thread = threading.Thread(target=self.handle_client,
                                            args=(client_sock, client_address))
                c_thread.start()

        except KeyboardInterrupt:
            self.shutdown_server()

    # if you push ctrl+C, stop the server
    def shutdown_server(self):
        print('\nShutting down the server...')
        self.sock.close()


def main():
    credential_server = Credential_Server('localhost', 2121)
    credential_server.init_server()
    credential_server.listen_connections()


if __name__ == '__main__':
    main()
