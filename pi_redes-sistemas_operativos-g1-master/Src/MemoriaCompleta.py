import threading
import MemoriaDisco as Disco
import MemoriaRam as Ram
import Page_Table as Page
import TLB as Tlb
class MemoriaCompleta:
    
    def __init__(self,id,ip_logica):
        self.es_cantonal = id
        self.disco = Disco.Memoria()
        self.mutex = threading.Lock()
        if self.es_cantonal == 0:
            self.disco.inicializar_disco(ip_logica)
            self.ram = Ram.Lista_Circular(8)
            self.ram.construir_ram()
            self.page = Page.Lista(20)
            self.page.inicializar_lista()
            self.tlb = Tlb.Lista_Circular(4)
            self.tlb.inicializar_TLB()
        else:
            self.disco.inicializar_disco(ip_logica)
            self.ram = Ram.Lista_Circular(4)
            self.ram.construir_ram()
            self.page = Page.Lista(8)
            self.page.inicializar_lista()
            self.tlb = Tlb.Lista_Circular(2)
            self.tlb.inicializar_TLB()


    def conseguir_pagina(self,ip):
        self.mutex.acquire()
        num_pagina = self.disco.know_page_by_ip(ip)
        #revisar si la pagina se encuentra en la TLB
        espacio = self.tlb.conseguir_espacio_pagina(num_pagina)
        if espacio == -1:
            #en caso de que no se encuentre en la TLB revisa su presencia en la Page Table
            presencia = self.page.buscar_en_tabla(num_pagina)
            if presencia == 0:
                #en caso de no estar en la ram se busca en disco
                espacio = self.ram.algortimo_reloj()
                #se aplica el algoritmo de reloj para ver la pagina a remplazar
                if espacio[1] == 1:
                    #si la pagina ha sido modificada, debe de remplazar los valores de disco
                    memoria_virtual =  self.page.conseguir_num_dado_espacio(espacio[0])
                    new_pagina = self.ram.conseguir_pagina(espacio[0])
                    self.disco.modificar_pagina(memoria_virtual,new_pagina)
                #se reemplaza la pagina por una en ram
                memoria_virtual = self.page.solicitar_memoria_virtual(num_pagina)
                pagina = self.disco.conseguir_pagina(memoria_virtual)
                self.ram.reemplazar_pagina(espacio[0],pagina)
                #se modifica la page tabla
                self.page.modificar_tabla(num_pagina,espacio[0])
                espacio_tlb = self.tlb.algortimo_reloj()
                self.tlb.reemplazar_pagina(espacio_tlb,num_pagina,espacio[0])
            else:
                #en caso de que este en ram se consigue el espacio en el que este
                espacio_ram = self.page.conseguir_espacio_ram(num_pagina)
                #se consigue una pagina dado un espacio de la ram
                pagina = self.ram.conseguir_pagina(espacio_ram)
                #se revisa la pagina a remplazar dado un algortimo de reloj
                espacio_tlb = self.tlb.algortimo_reloj()
                self.tlb.reemplazar_pagina(espacio_tlb,num_pagina,espacio_ram)
        else:
            #en caso de estar en la TLB, se busca directamente dado un espacio en memoria de ram
            pagina = self.ram.conseguir_pagina(espacio)
        self.mutex.release()
        return pagina

    def modificar_pagina(self,ip,info_modificada):
        self.mutex.acquire()
        num_pagina = self.disco.know_page_by_ip(ip)
        #revisar si la pagina se encuentra en la TLB
        espacio = self.tlb.conseguir_espacio_pagina(num_pagina)
        if espacio == -1:
            #en caso de que no se encuentre en la TLB revisa su presencia en la Page Table
            presencia = self.page.buscar_en_tabla(num_pagina)
            if presencia == 0:
                #en caso de no estar en la ram se busca en disco
                #se aplica el algoritmo de reloj para ver la pagina a remplazar
                espacio = self.ram.algortimo_reloj()
                if espacio[1] == 1:
                    #si la pagina ha sido modificada, debe de remplazar los valores de disco
                    memoria_virtual =  self.page.conseguir_num_dado_espacio(espacio[0])
                    new_pagina = self.ram.conseguir_pagina(espacio[0])
                    self.disco.modificar_pagina(memoria_virtual,new_pagina)
                #se reemplaza la pagina por una en ram
                memoria_virtual = self.page.solicitar_memoria_virtual(num_pagina)
                pagina = self.disco.conseguir_pagina(memoria_virtual)
                self.ram.reemplazar_pagina(espacio[0],pagina)
                #se modifica la page table
                self.ram.modificar_pagina(espacio[0],info_modificada)
                self.page.modificar_tabla(num_pagina,espacio)
                espacio_tlb = self.tlb.algortimo_reloj()
                self.tlb.reemplazar_pagina(espacio_tlb,num_pagina,espacio[0])
            else:
                #en caso de que este en ram se consigue el espacio en el que este
                espacio_ram = self.page.conseguir_espacio_ram(num_pagina) 
                self.ram.modificar_pagina(espacio_ram,info_modificada)
                espacio_tlb = self.tlb.algortimo_reloj()
                self.tlb.reemplazar_pagina(espacio_tlb,num_pagina,espacio_ram)
        else:
            #en caso de estar en la TLB, se busca directamente dado un espacio en memoria de ram
            self.ram.modificar_pagina(espacio,info_modificada)
        self.mutex.release()