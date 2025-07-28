dmesg
picocom -b 115200 /dev/ttyUSB0

### 1. Navegar al directorio del proyecto

```bash
cd docker-ml-app
```

### 2. Construir la imagen Docker

```bash
# Construcción con nombre más descriptivo
docker build -t ml-app:arm54 .
```

### 3. Verificar que la imagen se creó correctamente

```bash
# Listar todas las imágenes Docker
docker images
```

# 4. Comprimir imagen en archivo tar para luego transferir a la tarejta
```bash
docker save -o proton-ml-app.tar ml-app:arm64
```

# 5. Configurar red

# En el PC:
sudo ip link set enp2s0 up                   # habilitar la interfaz de red 
sudo ip addr add 192.168.7.1/24 dev enp2s0  # asignar IP estática en la subred /24

# En la tarjeta:
ip link set eth0 up                               # habilitar eth0
ip addr add 192.168.7.2/24 dev eth0               # asignar su IP en la misma subred

nota: la subred /24 tiene mascara 255.255.255.0.

# 6. Iniciar comunicación ssh

```bash
# Desde el PC, probar la conectividad:
ping -c2 192.168.7.2

# Si responde, conectarse por SSH:
ssh root@192.168.7.2
```

# 7. Copiar imagen docker en la tarjeta

scp proton-basic-api.tar root@172.20.3.2:/home/root

scp proton-ml-app.tar root@192.168.7.2:/tmp/   

# 8. Cargar imagen

cd /home/root
docker load -i proton-basic-api.tar


docker exec -it NOMBRE_O_ID_DEL_CONTENEDOR bash

---

 docker build -t ml-app:test .

 docker run --network=host --privileged -it ml-app:test

 docker run --network=host --privileged  --name test-container \
  -v $(pwd)/src:/app \
  -p 8080:8080 \
  -it ml-app:test


curl http://localhost:8080/api/wifi/status

curl http://localhost:8080/api/wifi/scan

# Ejecutar con permisos específicos (producción)
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW --device=/dev/rfkill wifi-app

## Gestión del Contenedor

### Detener el contenedor

```bash
docker stop ml-app-container
```

### Reiniciar el contenedor

```bash
docker restart ml-app-container
```

### Eliminar el contenedor

```bash
# Detener y eliminar
docker stop ml-app-container
docker rm ml-app-container
```

### Eliminar la imagen

```bash
docker rmi ml-app
```

