# Proyecto de Paralelismo y Concurrencia

## Propósito del Proyecto

Optimizar el procesamiento de imágenes de Pokémon mediante la aplicación de técnicas de paralelismo y concurrencia, reduciendo los tiempos de ejecución, cumpliendo los siguientes constraints:

- Máximo 8 cores en procesamiento
- Imágenes procesadas individualmente, es decir, no secuencialmente

## Resultados Obtenidos

### Comparativa de Tiempos de Ejecución

| Versión | Descarga | Procesamiento | Total |
|---------|----------|---------------|-------|
| **Baseline o secuencial** | 59.56 seg | 14.37 seg | **73.92 seg** |
| **Optimizado 1** | 6.34 seg | 3.10 seg | **9.44 seg** | 
| **Optimizado 2** | 6.05 seg | 7.82 seg | **13.87 seg** | 

**Nota:** Cabe mencionar que se utilizaron los mejores tiempos obtenidos para cada versión. De esta forma, primera optimización demostró ser la más eficiente.

## Versiones Optimizadas 

### Optimización #1 (Mejor Resultado)

#### **Cambios en Descargas:**

**Problema Original:**
```python
# 59.56 segundos
for i in tqdm(range(1, n + 1)):
    file_name = f'{i:03d}.png'
    url = f'{base_url}/{file_name}'
    response = requests.get(url)  # Una por una
```

**Solución:**
```python
# 6.34 segundos 
def download_single_pokemon(args):
    i, dir_name, base_url = args
    file_name = f'{i:03d}.png'
    url = f'{base_url}/{file_name}'
    response = requests.get(url)  # Individual pero concurrente

def download_pokemon(n=150, max_workers=40):
    download_args = [(i, dir_name, base_url) for i in range(1, n + 1)]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_single_pokemon, args) for args in download_args]
        
        for future in tqdm(as_completed(futures), total=len(futures)):
            future.result()
```

**Cambios Clave:**
- ThreadPoolExecutor con 40 workers para operaciones I/O
- Cada imagen se descarga individualmente pero concurrentemente
- Progreso en tiempo real con as_completed()

#### **Cambios en Procesamiento:**

**Problema Original:**
```python
# 14.37 segundos
for image in tqdm(images):
    img = Image.open(path_origin)
    # Transformaciones PIL una por una...
    img.filter(ImageFilter.GaussianBlur(radius=10))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
```

**Solución Optimizada:**
```python
# 3.10 segundos (4.6x más rápido)
def process_single_image(args):
    image, dir_origin, dir_name = args
    img = Image.open(path_origin)
    # Transformaciones PIL individuales
    img.filter(ImageFilter.GaussianBlur(radius=10))
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

def process_pokemon(max_workers=8):
    process_args = [(image, dir_origin, dir_name) for image in images]
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_single_image, args) for args in process_args]
        
        for future in tqdm(as_completed(futures), total=len(futures)):
            future.result()
```

**Cambios Clave:**
- ProcessPoolExecutor con 8 workers debido al constraint
- Cada imagen se procesa individualmente, pero en este caso en procesos separados
- Uso máximo de 8 cores para operaciones "CPU-intensive"

---

### Optimización #2 

**1. Mecanismo de Reintentos para Descargas:**
```python
def download_single_pokemon(args):
    i, dir_name, base_url, retry_count = args
    file_name = f'{i:03d}.png'
    url = f'{base_url}/{file_name}'
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, timeout=10)  # Timeout agregado
            response.raise_for_status()
            # Guardar imagen...
            return (True, file_name)
        except requests.exceptions.RequestException as e:
            if attempt == retry_count - 1:  # Último intento
                print(f'  Error descargando {file_name}: {e}')
                return (False, file_name)
            time.sleep(1)  # Espera antes de reintentar
```

**Cambios:**
- 2 reintentos automáticos para descargas fallidas
- Timeout de 10 segundos para evitar bloqueos

**2. Optimizaciones de Memoria en Procesamiento:**
```python
def process_single_image(args):
    image, dir_origin, dir_name = args
    
    try:
        # Context manager para gestión explícita de memoria
        with Image.open(path_origin) as img:
            img = img.convert('RGB')
            
            # Transformaciones combinadas más eficientemente
            img = img.filter(ImageFilter.GaussianBlur(radius=10))
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            
            img_inv = ImageOps.invert(img)
            img_inv = img_inv.filter(ImageFilter.GaussianBlur(radius=5))
            
            width, height = img_inv.size
            img_inv = img_inv.resize((width * 2, height * 2), Image.LANCZOS)
            img_inv = img_inv.resize((width, height), Image.LANCZOS)
        
        # Optimización al guardar imagen
        saving_path = os.path.join(dir_name, image)
        img_inv.save(saving_path, quality=95, optimize=True)
        
        return (True, image)
    except Exception as e:
        return (False, image, str(e))
```

**Cambios:**
- Context managers para liberación automática de memoria. En otras palabras, se asegura la correcta ejecución
  de tareas de configuración antes de entrar al bloque y tareas de limpieza al salir.
- Optimización al guardar con optimize=True.

**3. Métricas y Tracking Mejorado:**
```python
def download_pokemon(max_workers=32):  # Workers reducidos a 32
    successful_downloads = 0
    failed_downloads = []  # Tracking de fallos
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_single_pokemon, args): args for args in download_args}
        
        with tqdm(total=len(futures), desc='Descargando', unit='img') as pbar:
            for future in as_completed(futures):
                success, filename = future.result()
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads.append(filename)  # Registrar fallos
                pbar.update(1)
    
    # Nueva métrica de velocidad
    print(f'Velocidad: {n/total_time:.2f} img/s')
```

**Cambios:**
- Workers reducidos a 32, lo que mejora el balance del I/0
- Manejo de operaciones fallidas
- Métrica de velocidad en imágenes/segundo

## Conclusión

La implementación de paralelismo y concurrencia demostró ser efectiva, logrando una mejora significativa en el tiempo total de ejecución. El uso de ThreadPoolExecutor para operaciones I/O bound redujo las descargas de 59.56s a 6.34s, mientras que ProcessPoolExecutor para CPU bound disminuyó el procesamiento de 14.37s a 3.10s. La versión más simple superó a la más compleja, demostrando que un código con mayor desarrollo no necesariamente resulta eficiente y puede contrarrestar las ganancias de optimizaciones avanzadas. Este proyecto verifica que la correcta aplicación de paralelismo y concurrencia, respetando los constraints de 8 cores y procesamiento individual, puede transformar el rendimiento de aplicaciones con componentes I/O y CPU.

---

**Desarrollado por:** Victor Saravia Carné no. 20240060
```
