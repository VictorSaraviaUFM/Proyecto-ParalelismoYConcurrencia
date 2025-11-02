import multiprocessing as mp
import random
import time
import os

# # Use 'fork' in interactive environments (notebooks) to avoid spawn-related issues on macOS
# # If the start method is already set this will raise RuntimeError, so ignore it
try:
    mp.set_start_method('fork')
except RuntimeError:
    pass


# 1 - Definir función que ejecutará cada proceso

def search_in_chunk(chunk, target, chunk_id):
    
    for value in chunk:
        if value == target:
            return (True, chunk_id)
        
    return (False, chunk_id)

# 2 - Crear y ejecutar procesos


def worker(chunk_tuple, resultado_queue):
    chunk, target, chunk_id = chunk_tuple
    resultado = search_in_chunk(chunk, target, chunk_id)
    resultado_queue.put(resultado)


def parallel_search(data, target, n_cores):
   
    # Dividir datos en chunks
    chunk_size = len(data) // n_cores
    chunks = []
    

    for i in range(n_cores):
        start = i * chunk_size
        end = start + chunk_size if i < n_cores - 1 else len(data)
        # each chunk is (chunk_data, target, chunk_id)
        chunks.append((data[start:end], target, i))
    
    # Crear procesos manualmente
    processes = []
    queue = mp.Queue()
    
    # [worker]
    # def worker(chunk_tuple, resultado_queue):
    #     chunk, target, chunk_id = chunk_tuple
    #     resultado = search_in_chunk(chunk, target, chunk_id)
    #     resultado_queue.put(resultado)

    start_time = time.time()
    
    # Iniciar procesos
    for chunk_data in chunks:
        p = mp.Process(target=worker, args=(chunk_data, queue))
        p.start()
        processes.append(p)
    
    # Esperar a que terminen
    for p in processes:
        p.join()
    
    # Recolectar resultados
    results = []
    while not queue.empty():
        results.append(queue.get())
    
    total_time = time.time() - start_time
    
    # Mostrar resultados
    for found, chunk_id in results:
        if found:
            print(f'Valor {target} encontrado en chunk {chunk_id}')
            break
    else:
        print(f'Valor {target} no encontrado')
    
    print(f'Tiempo: {total_time:.4f}s')
    print(f'Cores utilizados: {n_cores}')


# Testing

SIZE = 10000000 # 10M
TARGET = 8888888
CORES = mp.cpu_count() # Usar todos los cores disponibles


print(f'\nTamaño de la lista: {SIZE:,}')
print(f'Valor a buscar: {TARGET:,}')
print(f'Cores disponibles: {CORES}')

# Generar datos
datos = list(range(SIZE))

# Ejecutar función general
parallel_search(datos, TARGET, CORES)
