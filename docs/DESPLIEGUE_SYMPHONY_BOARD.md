# Guía de despliegue en Symphony Board

Esta guía describe el proceso completo para desplegar la aplicación en una Symphony Board usando Docker.

## Prerrequisitos

### Hardware Requerido
- Symphony Board (ARM64) con imagen variscite previamente cargada con las características:
  - Servidor ssh
  - Docker
  - Python3
- PC host con linux y docker
- Cable ethernet para conexión ssh
- Cable micro usb para conexión serial


## Preparación Inicial
La conexión del usuario a la aplicación se realizará como se muestra en la Figura. Para ello, el usuario conecta su computador directamente al puerto Ethernet de la Symphony board. Ambos dispositivos deben estar en la misma red local, lo que permite acceder a la interfaz 
web del sistema ingresando la dirección IP de la tarjeta en el navegador. 

![Conexión del usuario a la aplicacion](/docs/figs/modo_de_uso.png)

Estas son las credenciales de acceso:
- IP: 172.20.3.2
- Usuario: root
- Password: proton-ml

### 1. Imagen Variscite

La tarjeta symphony board debe contener previamente la imagen **Variscite** con: Servidor SSH, Docker, Python3.
**Si no cumple estos requisitos**, desde un equipo Linux ejecute el siguiente comando para flashear la imagen [`proton_ml_BASE-SD-v1_0-vSYMPHONY.img.zst`](https://proctek-my.sharepoint.com/:u:/g/personal/diego_medina_proctek_com1/EeKSyZG8nfFBn_-TxyOl8HUBMmh9kbu-7Gqa09WpVNspAg?e=Yzanun) en una tarjeta SD para luego de transferir esta a la tarjeta variscite:

```bash
zstdcat proton_ml_BASE-SD-v1_1-vSYMPHONY.img.zst | sudo dd of=/dev/sda bs=4M && sync
```

> **Nota:** Verifique el nombre del dispositivo de la tarjeta SD con el comando `lsblk` antes de ejecutar la instrucción (reemplace `/dev/sda` si es necesario).



### Procedimiento para Arrancar el SOM desde la Tarjeta SD

1. **Apagado del dispositivo**: Asegúrese de que el interruptor de alimentación (SW7) esté en posición `OFF`.
   
2. **Selección del modo de arranque**: Configure el interruptor selector de arranque (SW3) en posición `SD` (modo tarjeta SD):  

   | Posición SW3 | Modo de Arranque |  
   |--------------|-------------------|  
   | `0`          | Tarjeta SD        |  
   | `1`          | Memoria eMMC      |  

3. **Inserción de la tarjeta microSD**: Introduzca la tarjeta preparada en la ranura **J28** de la placa Symphony.

4. **Conexión del terminal serial (recomendado)** : Conecte la placa a su PC mediante el puerto serial **antes** de encender el dispositivo.

5. **Encendido del dispositivo**  
   - Cambie el interruptor SW7 a la posición `ON`.  
   - Los mensajes de arranque se mostrarán en el terminal serial (si se está conectado).



### 2. Conexión Serial
```bash
# Verificar dispositivos conectados
sudo dmesg

# Conectar por puerto serial
sudo picocom -b 115200 /dev/ttyUSB0
```

nota: para salir de picocom, primero, presiona `Ctrl+A` y luego `Ctrl+X`.


### 3. Configuración de Red

#### En el PC Host:
```bash
# Habilitar interfaz de red
sudo ip link set enp2s0 up

# Asignar IP estática en subred /24 (máscara 255.255.255.0)
sudo ip addr add 172.20.3.1/24 dev enp2s0
```

#### En la Symphony Board:
```bash
# Habilitar interfaz Ethernet
ip link set eth0 up

# Asignar IP en la misma subred
ip addr add 172.20.3.2/24 dev eth0
```

Para acceder a red proctek
```bash
# Habilitar interfaz Ethernet
ip link set eth1 up

# Asignar IP en la misma subred
ip addr add 172.31.50.24/24 dev eth1

# Configurar gateway por defecto (asumiendo que el gateway es 172.20.3.1)
ip route add default via 172.31.50.24 dev eth1
```


## Proceso de Despliegue

### Paos 0: Preparación del Proyecto
```bash
# Navegar al directorio del proyecto
cd docker-ml-app-deploy
```

### Paso 1: Construcción de la Imagen Docker

El [dockerfile](/docker-ml-app-deploy/dockerfile) cuenta con un argumento que indica la plataforma de destino, lo cual permite construir la imagen docker según se necesite, despliegue en la tarjeta o pruebas en PC host.

```bash
# Argumento para la arquitectura
ARG TARGETPLATFORM=linux/arm64/v8
FROM --platform=$TARGETPLATFORM python:3.10-slim
```

A continuación se indica como se debe hacer el build de acuerdo a la plataforma.
```bash
# Construir imagen para arquitectura ARM64 -> Symphony Board
docker build --build-arg TARGETPLATFORM=linux/arm64/v8 -t ml-app:arm64 .

# Construir imagen Para PC local
docker build --build-arg TARGETPLATFORM=linux/amd64 -t ml-app:amd64 .
```

```bash
# Verificar que la imagen se creó correctamente
docker images
```

### Paso 2: Exportar Imagen para Transferencia

```bash
# Comprimir imagen en archivo tar
docker save -o proton-ml-app.tar ml-app:arm64
```

### Paso 3: Establecer Conexión SSH

```bash
# Probar conectividad desde el PC
ping -c2 172.20.3.2

# Conectarse por SSH (si responde)
ssh root@172.20.3.2
```

### Paso 4: Transferir Imagen Docker

```bash
# Copiar imagen a la Symphony Board
scp proton-ml-app.tar root@172.20.3.2:/home/root
```


### Paso 5: Cargar Imagen en la Board

```bash
# En la Symphony Board, cargar la imagen Docker
cd /home/root
docker load -i proton-ml-app.tar

# Verificar que se cargó correctamente
docker images
```

## Paso 6: run contenedor

```bash
docker run --network=host --privileged --name app-container -v $(pwd)/src:/app -it ml-app:arm64
```
