#!/bin/bash
#Conseguir los valores que van a generar la red
echo -n Ingrese el numero de Routers Provinciales:
read numero_provincias
echo $numero_provincias

echo -n Ingrese el numero de Routers Cantonales:
read numero_cantones
echo $numero_cantones

echo -n Ingrese el numero de Areas de Salud:
read numero_areas
echo $numero_areas

#generar la topologia de la red y el archivo de configuracion
cd Src
gnome-terminal -e "bash -c \" python3 generate_topology.py $numero_provincias $numero_cantones $numero_areas ; exec bash\"" 

sleep 1

cd Src

for index_cantonal in `seq 1 $numero_cantones`
do
    gnome-terminal -e "bash -c \" python3 Intra_provincial_router.py 1 $index_cantonal; exec bash\"" 
done
 
for index_cantonal in `seq 1 $numero_cantones`
do
    for index_area in `seq 1 $numero_areas`
    do
        gnome-terminal -e "bash -c \" python3 Server.py 1 $index_cantonal $index_area; exec bash\"" 
    done
done


echo "Press any key to close terminals"
read -n 1
if [ $? = 0 ] ; then
kill $(pgrep bash) ;
else
echo "waiting for the keypress"
fi
done