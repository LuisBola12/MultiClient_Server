# Repositorio de PI de Redes y Sistemas Operativos

## :rocket: Equipo Ayuwokis

### Integrantes

- Luis Bolanos Valverde B91145
- Daniela Murillo Murillo B95481
- Jarod Venegas Alpizar B98410
- Jorim G. Wilson Ellis B98615

### Etapa 1: anillo externo

Sistema distribuido para registro de vacunación. Se trata de un país en el que cada ciudadano puede vacunarse en cualquier lugar, pero el sistema debe guardar registro de esa vacuna en las bases de datos específicas del lugar donde reside el ciudadano.
El sistema consta de un servidor local por area de salud, al cual, se conectan los clientes (en este caso serían los trabajadores que registran a las personas) para poder almacenar la informacion de cada persona vacunada. Dentro del servidor que recibe toda esa información deben de haber dos procesos, uno que reciba las conexiones y otro que se encargue de imprimir los mensajes recibidos de estas conexiones. Los procesos se deben de comunicar por medio de un pipe.
