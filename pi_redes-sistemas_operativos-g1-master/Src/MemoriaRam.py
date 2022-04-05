class Nodo:
    def __init__(self,index):
        self.pagina = []
        self.referencia = 0
        self.modificada = 0
        self.espacio = index
        self.siguiente = None

class Lista_Circular:
    def __init__(self, tamano):
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
            self.manecilla = nuevo_nodo
            nuevo_nodo.siguiente = self.primera
        else:
            temporal = self.primera
            while temporal.siguiente is not self.primera:
                temporal = temporal.siguiente
            temporal.siguiente = nuevo_nodo
            nuevo_nodo.siguiente = self.primera

    #Imprime todo el contenido de la RAM
    def imprimir_ram(self):
        temporal = self.primera
        print(f'[Página: {temporal.pagina} : {temporal.referencia}]\n')
        while temporal.siguiente != self.primera:
            temporal = temporal.siguiente
            print(f'[Página: {temporal.pagina} : {temporal.referencia}]\n')

    #Metodo para bucar a un nuevo_nodo específico de la lista dado un indice
    def conseguir_pagina(self, espacio):
        temporal = self.primera
        while temporal is not None:
            if temporal.espacio == espacio:
                temporal.referencia = 1
                return temporal.pagina
            elif temporal.siguiente == self.primera:
                return -1
            else:
                temporal = temporal.siguiente
        return -1
        
    def construir_ram(self):
        for index in range(0,self.tamano):
            self.append(index)

    def algortimo_reloj(self):
        temp = None
        return_value = []
        while(True):
            if(self.manecilla.referencia == 1):
                self.manecilla.referencia = 0
                temp = self.manecilla.siguiente
                self.manecilla = temp
            else:
                return_value.append(self.manecilla.espacio)
                return_value.append(self.manecilla.modificada)
                temp = self.manecilla.siguiente
                self.manecilla = temp
                break
        return  return_value

    def reemplazar_pagina(self,espacio,pagina):
        temporal = self.primera
        while temporal is not None:
            if temporal.espacio == espacio:
                temporal.referencia = 0
                temporal.modificada = 0
                temporal.pagina = pagina
                return 1
            elif temporal.siguiente == self.primera:
                return -1
            else:
                temporal = temporal.siguiente
        return -1

    def modificar_pagina(self,espacio,pagina):
        temporal = self.primera
        while temporal is not None:
            if temporal.espacio == espacio:
                temporal.referencia = 1
                temporal.modificada = 1
                temporal.pagina = pagina
                return 1
            elif temporal.siguiente == self.primera:
                return -1
            else:
                temporal = temporal.siguiente
        return -1