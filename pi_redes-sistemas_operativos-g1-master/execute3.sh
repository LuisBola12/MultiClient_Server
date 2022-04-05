#!/bin/bash
#Conseguir los valores que van a generar la red
echo -n Ingrese el numero de Routers Provinciales:
read numero_provincias
echo $numero_provincias

cd Src
for index_provincial in `seq 1 $numero_provincias`
do 
    gnome-terminal -e "bash -c \" python3 Inter_provincial_router.py $index_provincial ; exec bash\"" 
done