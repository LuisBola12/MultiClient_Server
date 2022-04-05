import networkx as nx
import random
import os
import sys
import matplotlib.pyplot as plt

port = 5000

# Concatenates and return the logical IP of a province
def generate_inter_ip(node):
  result = ""
  node = int(node)+1
  if node > 9:
    result += str(node) + " 00 " + "0"
  else:
    result += "0"+str(node) + " 00 " + "0"

  return result

# Concatenates and return the logical IP of canton
def generate_intra_ip(node, sub_node):
  result = ""
  node = int(node)+1
  sub_node = int(sub_node)+1
  #province
  if node > 9:
    result += str(node)+" "
  else:
    result += "0"+str(node)+" "

  #canton
  if sub_node > 9:
    result += str(sub_node)+" "
  else:
    result += "0"+str(sub_node)+" "

  result += "0"

  return result

def generate_health_ip(node, sub_node, area):
  area_ip = ""

  # Gets acurate number of logic ip
  node = int(node)+1
  sub_node = int(sub_node)+1
  area = int(area+1)

  #province
  if node > 9:
    area_ip += str(node)+" "
  else:
    area_ip += "0"+str(node)+" "

  #canton
  if sub_node > 9:
    area_ip += str(sub_node)+" "
  else:
    area_ip += "0"+str(sub_node)+" "

  #healt area
  area_ip += str(area)

  return area_ip

# Writes the inter provincial network on the red_conf_file 
def write_inter_provincial_data(file, graph):
  global port
  file.write("nodes" + os.linesep)
  for node in graph.nodes:
    ip = generate_inter_ip(int(node))
    file.write(ip + os.linesep)

  file.write("edges" + os.linesep)
  for e in graph.edges:
    cost = random.randint(1,9)

    ip1 = generate_inter_ip(int(e[0]))
    ip2 = generate_inter_ip(int(e[1]))

    file.write( ip1 + "," +  ip2 + ","  + str(cost) + "," +  str(port) + os.linesep)
    port+=1

# adds an edge to the provincial node to one of the subnetwork
def create_random_edges(node, graph,file):
  global port
  first = True
  for sub_nodes in graph.nodes:
    edge_to_provincial = random.randint(0,1)
    cost = random.randint(1,9)
    if edge_to_provincial == 0 or first == True :
      ip1 = generate_inter_ip(int(node))
      ip2 = generate_intra_ip(node, sub_nodes)
      file.write( ip1 + "," +  ip2 + ","  + str(cost) + "," +  str(port) + os.linesep)
      first = False
      port+=1

# adds the edges of the subnetwork to the file
def write_edges(node, graph,file):
  global port
  for e in graph.edges:
    cost = random.randint(1,9)
    ip1 = generate_intra_ip(node, int(e[0]))
    ip2 = generate_intra_ip(node, int(e[1]))
    file.write( ip1 + "," +  ip2 + ","  + str(cost) + "," +  str(port) + os.linesep)
    port += 1

# Create a sub network with n nodes for each node in graph and creates the red_conf_file
def create_sub_networks(graph, n, health_area_count):
  file = open("red_conf.csv", "w")
  write_inter_provincial_data(file, graph)

  for node in graph.nodes:
    intra_provincial_graph = nx.connected_watts_strogatz_graph(n, 3, 0.3, tries=100, seed=None)

    file.write("nodes" +os.linesep)
    for sub_nodes in intra_provincial_graph.nodes:
      ip = generate_intra_ip(node, sub_nodes)
      file.write(ip + os.linesep)
      
    create_health_areas(node, intra_provincial_graph, file, health_area_count)
    file.write("edges" +os.linesep)

    create_random_edges(node, intra_provincial_graph, file)

    write_edges(node, intra_provincial_graph, file)

# Create the health areas of each canton
def create_health_areas(node, sub_nodes, file, health_area_count):
  global port
  for sub_node in sub_nodes.nodes:
    file.write("nodes" +os.linesep)
    for area in range(health_area_count):
      area_ip = generate_health_ip(node, sub_node, area)
      file.write(area_ip  + "," +  str(port) + os.linesep)
      port += 1
    
    file.write("edges" +os.linesep)
    for area in range(health_area_count):
      cost = random.randint(1,9)
      canton_ip = generate_intra_ip(node, sub_node)
      area_ip = generate_health_ip(node, sub_node, area)
      file.write(canton_ip + "," +  area_ip + ","  + str(cost) + "," +  str(port)  +  os.linesep)
      port+=1

# Used to print graph
def read_conf(graph):
  file = open("red_conf.csv", "r")

  # Using readlines()
  Lines = file.readlines()

  type = True
  for line in Lines:
    if line.strip() == "nodes":
      type = True
    else:
      if line.strip() == "edges":
        type = False
      else:        
        if type == True:
          tok = line.strip().split(",")
          graph.add_node(str(tok[0]))
        else:
          tok = line.strip().split(",")
          graph.add_edge(str(tok[0]), str(tok[1]))

  file.close()

# Effect: Create a configuration file with a random topology
# Requires: valid number of provincial, valid number of cantonal routers for each provincial router
# Modify: red_conf.csv
if __name__ == "__main__":
  # set node count for each graph
  inter_provincial_count = int(sys.argv[1])
  intra_provincial_count = int(sys.argv[2])
  health_area_count = int(sys.argv[3])

  # create random inter provincial topology
  inter_provincial_graph = nx.connected_watts_strogatz_graph(inter_provincial_count, 3, 0.3, tries=100, seed=None)

  # create random intra provincial topology for each node in inter_provincial_graph
  create_sub_networks(inter_provincial_graph, intra_provincial_count, health_area_count)

  #print
  final_topology_graph = nx.empty_graph()
  read_conf(final_topology_graph)
  nx.draw(final_topology_graph)
  plt.show()
