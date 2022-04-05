class Nodo:
    def __init__(self,index):
        self.num_pagina = 0
        self.referencia = 0
        self.espacio_ram = 0
        self.espacio_TLB = index
        self.siguiente = None

class Lista_Circular:
    def __init__(self,tamano):
        self.primera = None
        self.manecilla = None
        self.tamano = tamano

    #Verifica si la lista esta vacía
    def is_empty(self):
        return self.primera is None

    #Inserta un nuevo_nodo en la lista
    def append(self,index):
        nuevo_nodo = Nodo(index)
        if self.is_empty():
            self.primera = nuevo_nodo
            nuevo_nodo.siguiente = self.primera
        else:
            temporal = self.primera
            while temporal.siguiente is not self.primera:
                temporal = temporal.siguiente
            temporal.siguiente = nuevo_nodo
            nuevo_nodo.siguiente = self.primera

    #Imprime todo el contenido de la TLB
    def imprimir_TLB(self):
        temporal = self.primera
        print(f'[Página: {temporal.num_pagina} : {temporal.referencia}]\n')
        while temporal.siguiente != self.primera:
            temporal = temporal.siguiente
            print(f'[Página: {temporal.num_pagina} : {temporal.referencia}]\n')

    #Metodo para bucar a un nuevo_nodo específico de la lista dado un indice
    def conseguir_espacio_pagina(self, to_find):
        temporal = self.primera
        while temporal is not None:
            if temporal.num_pagina == to_find:
                temporal.referencia = 1
                return temporal.espacio_ram
            elif temporal.siguiente == self.primera:
                return -1
            else:
                temporal = temporal.siguiente
        return -1
        
    def algortimo_reloj(self):
        while(True):
            if(self.manecilla.referencia == 1):
                self.manecilla.referencia = 0
                temp = self.manecilla.siguiente
                self.manecilla = temp
            else:
                temp_result = self.manecilla
                temp = self.manecilla.siguiente
                self.manecilla = temp
                return temp_result.espacio_TLB
    def reemplazar_pagina(self,espacio,new_pagina,espacio_ram):
        temporal = self.primera
        while temporal is not None:
            if temporal.espacio_TLB == espacio:
                temporal.referencia = 0
                temporal.espacio_ram = espacio_ram
                temporal.num_pagina = new_pagina
                return 1
            elif temporal.siguiente == self.primera:
                return -1
            else:
                temporal = temporal.siguiente
        return -1
    def inicializar_TLB(self):
        for index in range(0,self.tamano):
            self.append(index)
        self.manecilla = self.primera

