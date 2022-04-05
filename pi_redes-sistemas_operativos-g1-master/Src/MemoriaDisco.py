MAX_BYTES_ON_DISC = 1160
class Memoria:
    def __init__(self):
        self.string_pre_disco = ""
        self.Memoria_Disco = []
        self.Orden_de_ips = []
        self.index_init = 0
        self.tamano = 0
    def colocar_provincia(self,my_ip):
        temp_ip = ""
        for index in range(0,29):
            if index < 2 :
                self.string_pre_disco+= my_ip[index]
                temp_ip+= my_ip[index]
            else:
                self.string_pre_disco+='0'
        temp_ip+="000"
        self.Orden_de_ips.append(temp_ip)
        temp_ip = ""
        my_id = my_ip[2]
        my_id += my_ip[3]
        my_partner = self.conocer_mi_pareja(my_id)
        temp = my_id[0]
        temp+= my_id[1]
        if my_partner < 10:
            temp += '0'
            temp += str(my_partner)
        else:
            temp += str(my_partner)
        temp_ip = temp
        temp_ip += "0"
        self.Orden_de_ips.append(temp_ip)
        for index in range(0,29):
            if index < 4:
                self.string_pre_disco+= temp[index]
            else:
                self.string_pre_disco+= '0'

    def ingresar_ip_a_disco(self,ip):
        self.Orden_de_ips.append(ip)
        for index in range(0,29):
            if index < 5:
                self.string_pre_disco+= ip[index]
            else:
                self.string_pre_disco+= '0'

    def inicializar_disco(self,my_ip):
        if my_ip[2:4] != "00":
            self.tamano = 20 * 58
            temp_ip = ""
            temp_ip = my_ip
            self.colocar_provincia(temp_ip)
            temp_ip = temp_ip.rstrip(temp_ip[-1])
            for index in range(1,9):
                new_ip=temp_ip+str(index)
                self.ingresar_ip_a_disco(new_ip)
            temp_ip = my_ip
            self.emparejar_cantonales(temp_ip)
            self.copiar_string_a_disco()
        else:
            self.tamano = 8 * 58
            self.inicializar_router_provincial(my_ip[0:2])
            self.copiar_string_a_disco()
    

    def ingresar_espacio_mi_ip_frontera(self):
        self.Orden_de_ips.append("00000")
        for index in range(0,29):
            self.string_pre_disco += "0"

    def ingresar_ips_provinciales(self,my_id,pareja):
        for index in range(1,17):
            if index != int(my_id):
                if index != int(pareja):
                    if len(str(index)) == 1:
                        self.string_pre_disco += "0"
                        self.string_pre_disco += str(index)
                        ip = "0" + str(index) + "000"
                        self.Orden_de_ips.append(ip)
                        for index2 in range (2,29):
                            self.string_pre_disco += "0"
                    else:
                        ip = str(index) + "000"
                        self.Orden_de_ips.append(ip)
                        self.string_pre_disco += str(index)
                        for index2 in range (2,29):
                            self.string_pre_disco += "0"
                            
    def inicializar_router_provincial(self,my_id):
        pareja =  self.conocer_mi_pareja(my_id)
        str_pareja = str(pareja)
        if len(str_pareja) == 1:
            self.string_pre_disco+="0"
            self.string_pre_disco+= str_pareja
            ip = "0" + str_pareja + "000"
            self.Orden_de_ips.append(ip)
        else:
            ip = str_pareja + "000"
            self.string_pre_disco+= str_pareja
            self.Orden_de_ips.append(ip)
        for index in range(2,29):
            self.string_pre_disco+= "0"
        self.ingresar_espacio_mi_ip_frontera()
        self.ingresar_ips_provinciales(my_id,pareja)

    def conocer_mi_pareja(self,my_id):
        int_id = int(my_id)
        if int_id%2==0:
            int_id = int_id-1
            return int_id
        else:
            int_id = int_id+1
            return int_id

    def emparejar_cantonales(self,my_ip):
        my_id = my_ip[2]
        my_id += my_ip[3]
        my_partner = self.conocer_mi_pareja(my_id)
        temp_fijo = my_ip[0]
        temp_fijo += my_ip[1]
        for index in range(1,33):
            temp = temp_fijo
            if index != int(my_id):
                if index < 10:
                    if index != my_partner:
                        temp+='0'
                        temp+=str(index)
                        temp+='0'
                        self.ingresar_ip_a_disco(temp)
                else:
                    if index != my_partner:
                        temp+=str(index)
                        temp+='0'
                        self.ingresar_ip_a_disco(temp)

    def modificar_pagina(self,num_pagina,pagina):
        espacio = (num_pagina-1) * 58
        caracter = ''
        counter = 0
        for index in range(espacio,espacio+58):
            caracter = pagina[counter]
            self.Memoria_Disco[index] = caracter
            counter += 1

    def conseguir_pagina(self,num_pagina):
        pagina = num_pagina-1
        espacio = pagina * 58
        info = []
        for index in range(espacio,espacio+58):
            info.append(self.Memoria_Disco[index])
        return info 
    def copiar_string_a_disco(self):
        for index in range(0,self.tamano):
            self.Memoria_Disco.append(self.string_pre_disco[index].encode())

    def know_page_by_ip(self,ip):
        index = self.Orden_de_ips.index(ip)
        if index % 2 == 0 :
            index = int((index+2)/2)
        else:
            index = int((index+1)/2)
        return index
