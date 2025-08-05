# Despliegue en Symphony Board - Guía de Instalación

Esta guía describe el proceso completo para desplegar la aplicación en una Symphony Board usando Docker.

## 📋 Prerrequisitos

### Hardware Requerido
- Symphony Board (ARM64) con imagen variscite previamente cargada con las características:
  - Soporte out-of-the-box para Symphony board
  - Servidor ssh
  - Docker
  - Kubernetes
  - Python3
- PC host con linux y docker
- Cable ethernet para conexión ssh
- Cable micro usb para conexión serial


Estas son las credenciales de acceso:
- IP: 172.20.3.2
- Usuario: root
- Password: proton-ml

## 🔧 Preparación Inicial

### 1. Conexión Serial
```bash
# Verificar dispositivos conectados
sudo dmesg

# Conectar por puerto serial
sudo picocom -b 115200 /dev/ttyUSB0
```

### 2. Preparación del Proyecto
```bash
# Navegar al directorio del proyecto
cd docker-ml-app-deploy
```


## 🚀 Proceso de Despliegue

### Paso 1: Construcción de la Imagen Docker

El [dockerfile](/docker-ml-app-deploy/dockerfile) cuenta con un argumento que indica la plataforma de destino, lo cual permite construir la imagen docker según se necesite, despliegue en la tarjeta o pruebas en PC host.

```bash
# Argumento para la arquitectura
ARG TARGETPLATFORM=linux/arm64/v8
FROM --platform=$TARGETPLATFORM python:3.10-slim
```

A continuación se indica como debe hacerse el build de acuerdo a la plataforma.
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

### Paso 3: Configuración de Red

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

### Paso 4: Establecer Conexión SSH

```bash
# Probar conectividad desde el PC
ping -c2 172.20.3.2

# Conectarse por SSH (si responde)
ssh root@172.20.3.2
```

### Paso 5: Transferir Imagen Docker

```bash
# Copiar imagen a la Symphony Board
scp proton-ml-app.tar root@172.20.3.2:/home/root
```

```bash
# Copiar imagen a la Symphony Board
scp proton-ml-app.tar root@172.20.3.2:/tmp
```
### Paso 6: Cargar Imagen en la Board

```bash
# En la Symphony Board, cargar la imagen Docker
cd /tmp
docker load -i proton-ml-app.tar

# Verificar que se cargó correctamente
docker images
```

## Paso 7: run contenedor

```bash
docker run --network=host --privileged --name test-container -v $(pwd)/src:/app -it ml-app:amd64
```