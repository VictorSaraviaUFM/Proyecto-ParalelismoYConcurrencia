'''
@tortolala
Pokemon image processing pipeline (Optimizado).
'''

from PIL import Image, ImageOps, ImageFilter, ImageEnhance
from pika_banner import print_pikachu
from tqdm import tqdm
import requests
import time
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

#--------------------
# Funciones de descarga
#--------------------

def download_single_pokemon(args):
    '''
    Descarga una única imagen de pokémon.
    '''
    i, dir_name, base_url = args
    file_name = f'{i:03d}.png'
    url = f'{base_url}/{file_name}'
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        img_path = os.path.join(dir_name, file_name)
        with open(img_path, 'wb') as f:
            f.write(response.content)
        return True
    except requests.exceptions.RequestException as e:
        print(f'  Error descargando {file_name}: {e}')
        return False

def download_pokemon(n=150, dir_name='pokemon_dataset', max_workers=40):
    '''
    Usando "ThreadPoolExecutor descarga de forma concurrente. 
    '''
    os.makedirs(dir_name, exist_ok=True)
    base_url = 'https://raw.githubusercontent.com/HybridShivam/Pokemon/master/assets/imagesHQ'

    print(f'\nDescargando {n} pokemones con {max_workers} workers...\n')
    start_time = time.time()
    
    # Esta lista contendrá los argumentos para cada descarga
    download_args = [(i, dir_name, base_url) for i in range(1, n + 1)]
    
    successful_downloads = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Envía todas las tareas
        futures = [executor.submit(download_single_pokemon, args) for args in download_args]
        
        #  Usa tqdm para mostrar progreso
        for future in tqdm(as_completed(futures), total=len(futures), desc='Descargando', unit='img'):
            if future.result():
                successful_downloads += 1
    
    total_time = time.time() - start_time
    print(f'  Descarga completada en {total_time:.2f} segundos')
    print(f'  Descargas exitosas: {successful_downloads}/{n}')
    print(f'  Promedio: {total_time/n:.2f} s/img')
    
    return total_time


#--------------------
# Funciones de procesamiento
#--------------------

def process_single_image(args):
    '''
    Procesa una única imagen.
    '''
    image, dir_origin, dir_name = args
    
    try:
        path_origin = os.path.join(dir_origin, image)
        img = Image.open(path_origin).convert('RGB')
        
        # Transformaciones a imagen 
        img = img.filter(ImageFilter.GaussianBlur(radius=10))
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
        img_inv = ImageOps.invert(img)
        img_inv = img_inv.filter(ImageFilter.GaussianBlur(radius=5))
        width, height = img_inv.size
        img_inv = img_inv.resize((width * 2, height * 2), Image.LANCZOS)
        img_inv = img_inv.resize((width, height), Image.LANCZOS)
    
        saving_path = os.path.join(dir_name, image)
        img_inv.save(saving_path, quality=95)
        return True
    
    except Exception as e:
        print(f'  Error procesando {image}: {e}')
        return False

def process_pokemon(dir_origin='pokemon_dataset', dir_name='pokemon_processed', max_workers=8):
    '''
    Aplica múltiple transformaciones para procesar cada imagen y usamos multiprocessing con máximo 8 cores
    '''
    os.makedirs(dir_name, exist_ok=True)
    images = sorted([f for f in os.listdir(dir_origin) if f.endswith('.png')])
    total = len(images)
    
    print(f'\nProcesando {total} imágenes con {max_workers} workers...\n')
    start_time = time.time()
    
    # Preparar argumentos para cada imagen
    process_args = [(image, dir_origin, dir_name) for image in images]
    
    successful_processing = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Enviar todas las tareas
        futures = [executor.submit(process_single_image, args) for args in process_args]
        
        # Usar tqdm para mostrar progreso
        for future in tqdm(as_completed(futures), total=len(futures), desc='Procesando', unit='img'):
            if future.result():
                successful_processing += 1
    
    total_time = time.time() - start_time
    print(f'  Procesamiento completado en {total_time:.2f} segundos')
    print(f'  Procesamientos exitosos: {successful_processing}/{total}')
    print(f'  Promedio: {total_time/total:.2f} s/img\n')
    
    return total_time


#--------------------
# Función main
#--------------------

if __name__ == '__main__':
    print('='*60)
    print_pikachu()
    print('   POKEMON IMAGE PROCESSING PIPELINE (Optimizado)')
    print('='*60)
    
    # Descarga concurrente con threading
    download_time = download_pokemon(max_workers=40)
    
    # Procesamiento paralelo con multiprocessing de 8 cores
    processing_time = process_pokemon(max_workers=8)
    
    # Tiempo total
    total_time = download_time + processing_time

    # Prints
    print('='*60)
    print('RESUMEN DE TIEMPOS\n')
    print(f'  Descarga:        {download_time:.2f} seg')
    print(f'  Procesamiento:   {processing_time:.2f} seg\n')
    print(f'  Total:           {total_time:.2f} seg')
    print('='*60)