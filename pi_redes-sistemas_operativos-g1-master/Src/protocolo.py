import djikstra as djikstra

class LS():
    def __init__(self):
        # array with the ip of all routers
        self.node_ips = []
        # array with the neighbors (each router has one)
        self.all_neighbors = []
        # array with all the router_ip, neighbor and cost
        self.node_info = []
        self.INF = -1
    
    # finds all the neighbors of the node given by the parameter
    def find_neighbors(self, source_node):
        my_neighbors = []
        file = open("red_conf.csv", "r")
        lines = file.readlines()
        is_node = True
        for index in lines:
            if index.strip() == "nodes":
                is_node = True
            else:
                if index.strip() == "edges":
                    is_node = False
                else:
                    if is_node == True:
                        tok = index.strip().split(",")
                    if is_node == False:
                        tok = index.strip().split(",")
                        if str(tok[0]).replace(" ", "") == source_node:
                            origen = str(tok[0]).replace(" ", "")
                            if "00" != origen[2:4]:
                                neighbor = (str(tok[1]).replace(
                                    " ", ""), str(tok[2]).replace(" ", ""), str(tok[3]).replace(" ", ""),1)
                                my_neighbors.append(neighbor)
                        if str(tok[1]).replace(" ", "") == source_node:
                            origen = str(tok[0]).replace(" ", "")
                            if "00" != origen[2:4]:
                                neighbor = (str(tok[0]).replace(
                                    " ", ""), str(tok[2]).replace(" ", ""), str(tok[3]).replace(" ", ""),0)
                                my_neighbors.append(neighbor)
        file.close()
        #print(f"\nVecinos")
        #print(my_neighbors)
        return my_neighbors

    # finds all the routers ips and puts them in a vector
    def add_router_ip(self):
        file = open("red_conf.csv", "r")
        lines = file.readlines()
        is_node = True
        for index in lines:
            if index.strip() == "nodes":
                is_node = True
            else:
                if index.strip() == "edges":
                    is_node = False
                else:
                    if is_node == True:
                        tok = index.strip().split(",")
                        origen = str(tok[0]).replace(" ", "")
                        if "00" != origen[2:4]:                           
                            self.node_ips.append(origen)
        file.close()
        #print(self.node_ips)
        return self.node_ips

    # gets all the neighbors for every router
    def get_all_neighbors(self):
        size = len(self.node_ips)
        for index in range(size):
            self.all_neighbors.append(
                self.find_neighbors(self.node_ips[index]))
        return self.all_neighbors
        #print(*self.all_neighbors, sep="\n")

    # gets all the info from a router and puts it in a triplet inside a vector
    # used to fill the matrix
    def get_node_info(self):
        new_index = 0
        for node in range(len(self.all_neighbors)):
            vecino = 0
            costo = 1
            port = 2
            is_bind = 3
            tok = str(self.all_neighbors[new_index]).strip().split(",")
            for index in range(len(self.all_neighbors[new_index])):
                my_neighbor = str(tok[vecino].replace("[('", ""))
                my_neighbor = str(my_neighbor.replace(" (", ""))
                my_neighbor = str(my_neighbor.replace("'", ""))
                
                my_cost = str(tok[costo].replace("'", ""))
                my_cost = str(my_cost.replace(" ", ""))
 
                my_port = str(tok[port].replace("'", ""))
                my_port = str(my_port.replace("')]", ""))
                my_port = str(my_port.replace(")", ""))
                my_port = str(my_port.replace("]", ""))
                
                self.node_info.append((self.node_ips[node], my_neighbor, my_cost, my_port))
                vecino = vecino+4
                costo = costo+4
                port = port+4          
            new_index += 1
        # for i in range(len(self.node_info)):
        #     origen,vecino,costo,puerto = self.node_info[i]
        #     print("Origen: " + str(origen) + " vecino: " + str(vecino), " Costo: "+ str(costo), "Puerto:" +str(puerto))
        return self.node_info
    
    # fill the matrix with the connection cost according with what we have in the topology
    # used to compute ded shortest path with Djikstra
    def fill_matrix(self):
        size = len(self.node_ips)
        net_graph = [[self.INF for col in range(size)]for row in range(size)]
        columna = 0
        for row in range(size):
            net_graph[row][row] = 0
            for i in range(len(self.node_info)):
                origen, destino, costo, puerto = self.node_info[i]
                if self.node_ips[row] == origen:
                    for j in range(len(self.node_ips)):
                        if self.node_ips[j] == destino:
                            columna = j
                    net_graph[row][columna] = int(costo)
        print("Matriz creada")
        print(*net_graph, sep="\n")
        return net_graph

    def fill_matrix1(self, ips, source_node):
        size = len(ips)
        net_graph = [[self.INF for col in range(size)]for row in range(size)]
        columna = 0
        for row in range(size):
            net_graph[row][row] = 0
            for i in range(len(self.node_info)):
                origen, destino, costo, puerto = self.node_info[i]
                if ips[row] == origen and source_node == origen:
                    for j in range(len(ips)):
                        if ips[j] == destino:
                            columna = j
                    net_graph[row][columna] = int(costo)
        print("Matriz creada")
        print(*net_graph, sep="\n")
        return net_graph

    # build the package to send it to all the neighbors of the source router
    def build_my_package(self, source_node):
        my_package = ""
        neighbors = self.all_neighbors[self.node_ips.index(source_node)]
        my_package += str(neighbors)
        my_package = my_package.replace("[('", "")
        my_package = my_package.replace(" (", "")
        my_package = my_package.replace("'", "")
        my_package = my_package.replace("')", "")
        my_package =my_package.replace("]", "")
        my_package = my_package.replace(" '", "")
        my_package = my_package.replace(" ", "")
        my_package = my_package.replace(")", "")
        print(f"package = {my_package}")
        return my_package
    
    def prueba_vecinos(self, node_id):
        vecinos = self.find_neighbors(int(node_id))
        print(vecinos)
                                   
    def start_linked_state_info(self):
        ips = self.add_router_ip()
        self.find_neighbors(ips[0])
        # self.get_all_neighbors()
        # self.get_node_info()
        # #self.get_node_info()
        # #matrix1 = self.fill_matrix1(ips, ips[0])
        # matrix = self.fill_matrix()
        # djisktra = djikstra.Dijsktra(len(ips))
        # djisktra.djisktra_algorithm(0, matrix)
        
        #self.fill_matrix()
        #self.ls_protocol(self.node_ips[0])
        #self.build_my_package("03011")
        #self.find_neighbors(self.node_ips[0])
        
    # def ls_protocol(self, source_node):
    #     neighbor_list = {}
    #     table = {}
    #     visited_nodes = {}
    #     size = len(self.node_ips)
    #     for node in self.node_ips:
    #         my_node = self.node_ips.index(node)
    #         table[my_node] = neighbor_list
    #         neighbors = self.find_neighbors(my_node)
    #         neighbor_list[node] = neighbors
        
    #     full_table = self.dijkstra_algorithm(source_node, table)
    #     print(full_table)
    #     return full_table
                                             
def main():
    protocol = LS()
    protocol.start_linked_state_info()

if __name__ == '__main__':
    main()

