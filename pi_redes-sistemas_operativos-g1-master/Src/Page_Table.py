class Nodo: 
    def __init__(self,numero):
        self.pagina = numero
        self.presencia = 0
        self.espacio_ram = numero
        self.siguiente = None

    def __repr__(self):
        return self.presencia

class Lista:
    def __init__(self,tamano):
        self.primera = None
        self.max_nodos = tamano

    def append(self,numero):
        Nueva = Nodo(numero)
        if self.primera is None:
            self.primera = Nueva
        else:
            temporal = self.primera
            while(temporal.siguiente):
                temporal = temporal.siguiente
            temporal.siguiente = Nueva

    def imprimir_lista(self):
        printval = self.primera
        while (printval):
            print(f'[Página: {printval.pagina} : {printval.presencia}]\n')
            printval = printval.siguiente

    def inicializar_lista(self):
        for index in range(1,self.max_nodos+1):
            self.append(index)

    def buscar_en_tabla(self,a_buscar):
        condition = True
        temporal = self.primera
        presencia = -1
        while(condition):
            if(temporal):
                if temporal.pagina == a_buscar:
                    condition = False
                    presencia = temporal.presencia
                temporal = temporal.siguiente
            else:
                condition = False
        return presencia

    def modificar_tabla(self,pagina_agregada,espacio):
        temporal = self.primera
        while temporal is not None:
            if temporal.espacio_ram == espacio:
                temporal.presencia = 0
                temporal.espacio_ram = temporal.pagina
            if temporal.pagina == pagina_agregada:
                temporal.presencia = 1
                temporal.espacio_ram = espacio
            temporal = temporal.siguiente
        
    def solicitar_memoria_virtual(self,num_pagina):
        temporal = self.primera
        while temporal is not None:
            if temporal.pagina == num_pagina:
                return temporal.espacio_ram
            temporal = temporal.siguiente 

    def conseguir_espacio_ram(self,num_pagina):
        temporal = self.primera
        while temporal is not None:
            if temporal.presencia != 0:
                if temporal.pagina == num_pagina:
                    return temporal.espacio_ram
            temporal = temporal.siguiente 

    def conseguir_num_dado_espacio(self,espacio):
        temporal = self.primera
        while temporal is not None:
            if temporal.presencia != 0:
                if temporal.espacio_ram == espacio:
                    return temporal.pagina
                elif temporal.siguiente == self.primera:
                    return -1
                else:
                    temporal = temporal.siguiente
            else:
                temporal = temporal.siguiente
        return -1

        
