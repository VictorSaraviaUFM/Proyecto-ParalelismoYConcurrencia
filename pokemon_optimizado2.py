'''
@tortolala
Pokemon image processing pipeline.
Optimized with parallelism and concurrency - Version 2
'''

from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from pika_banner import print_pikachu
from tqdm import tqdm
import requests
import time
import os
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# Configuración más óptima
MAX_CPU_WORKERS = 8  # Constraint de 8 cores
IO_WORKERS = 32      # Ajustado basado en resultados anteriores
CHUNK_SIZE = 10      # Procesamiento en chunks


#--------------------
# Funciones de descarga
#--------------------

def download_single_pokemon(args):
    '''
    Descarga una única imagen de pokémon con mecanismo de reintentos
    '''
    i, dir_name, base_url, retry_count = args
    file_name = f'{i:03d}.png'
    url = f'{base_url}/{file_name}'
    
    for attempt in range(retry_count):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            img_path = os.path.join(dir_name, file_name)
            with open(img_path, 'wb') as f:
                f.write(response.content)
            return (True, file_name)
        except requests.exceptions.RequestException as e:
            if attempt == retry_count - 1:  # Último intento
                print(f'  Error descargando {file_name}: {e}')
                return (False, file_name)
            time.sleep(1)  # Espera antes de reintentar
    
    return (False, file_name)

def download_pokemon(n=150, dir_name='pokemon_dataset', max_workers=IO_WORKERS):
    '''
    Descarga las imágenes de los primeros n Pokemones usando threading optimizado
    '''
    os.makedirs(dir_name, exist_ok=True)
    base_url = 'https://raw.githubusercontent.com/HybridShivam/Pokemon/master/assets/imagesHQ'

    print(f'\nDescargando {n} pokemones con {max_workers} workers...\n')
    start_time = time.time()
    
    # Preparar argumentos con el mecanismo de reintentos
    download_args = [(i, dir_name, base_url, 2) for i in range(1, n + 1)]  # 2 reintentos
    
    successful_downloads = 0
    failed_downloads = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(download_single_pokemon, args): args for args in download_args}
        
        with tqdm(total=len(futures), desc='Descargando', unit='img') as pbar:
            for future in as_completed(futures):
                success, filename = future.result()
                if success:
                    successful_downloads += 1
                else:
                    failed_downloads.append(filename)
                pbar.update(1)
    
    total_time = time.time() - start_time
    print(f' Descarga completada en {total_time:.2f} segundos')
    print(f' Descargas exitosas: {successful_downloads}/{n}')
    if failed_downloads:
        print(f' Fallidas: {len(failed_downloads)} imágenes')
    print(f' Velocidad: {n/total_time:.2f} img/s')
    
    return total_time


#--------------------
# Funciones de procesamiento
#--------------------

def process_single_image(args):
    '''
    Procesa una única imagen con optimizaciones de memoria
    '''
    image, dir_origin, dir_name = args
    
    try:
        path_origin = os.path.join(dir_origin, image)
        
        # Abre y procesa con gestión explícita de memoria
        with Image.open(path_origin) as img:
            img = img.convert('RGB')
            
            # Aplica transformaciones más eficientez
            # Combina operaciones similares
            img = img.filter(ImageFilter.GaussianBlur(radius=10))
            img = ImageEnhance.Contrast(img).enhance(1.5)
            img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
            
            
            img_inv = ImageOps.invert(img)
            img_inv = img_inv.filter(ImageFilter.GaussianBlur(radius=5))
            
            width, height = img_inv.size
            # Redimensiona directamente al tamaño final (más eficiente)
            img_inv = img_inv.resize((width * 2, height * 2), Image.LANCZOS)
            img_inv = img_inv.resize((width, height), Image.LANCZOS)
        
        saving_path = os.path.join(dir_name, image)
        img_inv.save(saving_path, quality=95, optimize=True)  # Optimiza al guardar
        
        return (True, image)
    except Exception as e:
        return (False, image, str(e))

def process_pokemon_chunk(args):
    '''
    Procesa un chunk de imágenes
    '''
    chunk, dir_origin, dir_name = args
    results = []
    
    for image in chunk:
        result = process_single_image((image, dir_origin, dir_name))
        results.append(result)
    
    return results

def process_pokemon(dir_origin='pokemon_dataset', dir_name='pokemon_processed', max_workers=MAX_CPU_WORKERS):
    '''
    Procesa las imágenes aplicando múltiples transformaciones en paralelo
    '''
    os.makedirs(dir_name, exist_ok=True)
    images = sorted([f for f in os.listdir(dir_origin) if f.endswith('.png')])
    total = len(images)
    
    print(f'\nProcesando {total} imágenes con {max_workers} workers...\n')
    start_time = time.time()
    
    # Estrategia: procesamiento individual para mejor balance de carga
    process_args = [(image, dir_origin, dir_name) for image in images]
    
    successful_processing = 0
    failed_processing = []
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_image, args): args for args in process_args}
        
        with tqdm(total=len(futures), desc='Procesando', unit='img') as pbar:
            for future in as_completed(futures):
                result = future.result()
                if result[0]:  # Success
                    successful_processing += 1
                else:
                    failed_processing.append((result[1], result[2]))
                pbar.update(1)
    
    total_time = time.time() - start_time
    print(f'Procesamiento completado en {total_time:.2f} segundos')
    print(f'Procesamientos exitosos: {successful_processing}/{total}')
    if failed_processing:
        print(f'Fallidas: {len(failed_processing)} imágenes')
    print(f'Velocidad: {total/total_time:.2f} img/s\n')
    
    return total_time


#--------------------
# Función main
#--------------------

def main():

    print('='*60)
    print_pikachu()
    print('   POKEMON IMAGE PROCESSING PIPELINE (Optimizado #2)')
    print('='*60)
    
    total_start_time = time.time()
    
    # Descarga concurrente con threading
    download_time = download_pokemon(max_workers=IO_WORKERS)
    
    # Procesamiento paralelo con multiprocessing de 8 cores
    processing_time = process_pokemon(max_workers=MAX_CPU_WORKERS)
    
    total_time = time.time() - total_start_time

    # Prints
    print('='*60)
    print('RESUMEN DE TIEMPOS\n')
    print(f'  Descarga:  {download_time:.2f} seg')
    print(f'  Procesamiento: {processing_time:.2f} seg\n')
    print(f'  Total: {total_time:.2f} seg')
    print('='*60)

    return total_time

if __name__ == '__main__':
    # Configurar multiprocessing para mejor compatibilidad
    try:
        mp.set_start_method('spawn', force=True)
    except RuntimeError:
        pass
    
    main()