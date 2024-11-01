import os
import requests
from bs4 import BeautifulSoup
import threading
import random
from PIL import Image, ImageEnhance, ImageFilter
import tkinter as tk
from tkinter import messagebox, filedialog

# Глобальная переменная для корневой папки
root_folder = ""
# Флаг для остановки потоков
stop_threads = False

# Функция для создания папки для сохранения изображений
def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

# Функция для загрузки изображения по URL
def download_image(url, folder_name):
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        filename = os.path.join(folder_name, url.split("/")[-1].split("?")[0])

        if not filename:
            print(f"Не удалось извлечь имя файла из URL: {url}")
            return False

        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        
        return filename  # Возвращаем путь к сохранённому изображению
    except Exception as e:
        print(f"Не удалось загрузить изображение {url}: {e}")
        return None

# Функция уникализации изображения
def uniquify_image(image_path):
    try:
        with Image.open(image_path) as img:
            # Изменение размера
            scale = random.uniform(0.9, 1.1)
            new_size = (int(img.width * scale), int(img.height * scale))
            img = img.resize(new_size, Image.LANCZOS)
            
            # Поворот
            rotation_angle = random.uniform(-5, 5)
            img = img.rotate(rotation_angle)

            # Обрезка
            crop_percent = random.uniform(0.95, 1)
            crop_x = int(img.width * (1 - crop_percent))
            crop_y = int(img.height * (1 - crop_percent))
            img = img.crop((crop_x, crop_y, img.width - crop_x, img.height - crop_y))

            # Яркость и контраст
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(random.uniform(0.9, 1.1))
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(random.uniform(0.9, 1.1))
            
            # Насыщенность
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(random.uniform(0.9, 1.1))
            
            # Добавление шума
            img = img.filter(ImageFilter.GaussianBlur(random.uniform(0.5, 1.5)))
            
            # Сохранение
            img.save(image_path)
            print(f"Изображение {image_path} уникализировано.")
    except Exception as e:
        print(f"Ошибка при уникализации изображения {image_path}: {e}")

# Функция для поиска и загрузки изображений
def search_bing_images(query, num_images, uniquify=False):
    global stop_threads
    url = "https://www.bing.com/images/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    }

    folder_name = create_folder(os.path.join(root_folder, query))
    successful_downloads = 0
    offset = 0

    while successful_downloads < num_images and not stop_threads:
        params = {
            "q": query,
            "first": offset,
            "qft": "+filterui:imagesize-large"
        }

        response = requests.get(url, headers=headers, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        image_elements = soup.find_all("a", class_="iusc")

        if not image_elements:
            break

        for img in image_elements:
            if successful_downloads >= num_images or stop_threads:
                break

            m = img.get("m")
            if m:
                image_url = m.split('"murl":"')[1].split('"')[0]
                image_path = download_image(image_url, folder_name)
                
                if image_path:
                    if uniquify:  # Если флажок уникализации установлен
                        uniquify_image(image_path)
                    successful_downloads += 1

    print(f"Итог: загружено {successful_downloads} изображений из {num_images} для запроса '{query}'.")

# Функция для выбора корневой папки
def choose_root_folder():
    global root_folder
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        root_folder = selected_folder
        folder_label.config(text=f"Корневая папка: {root_folder}")

# Функция для запуска многопоточной загрузки
def start_downloads():
    global stop_threads
    stop_threads = False
    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)

    threads = []
    queries = query_text.get("1.0", tk.END).strip().splitlines()
    try:
        num_images = int(count_entry.get())
        if num_images <= 0:
            messagebox.showwarning("Внимание", "Пожалуйста, укажите положительное количество изображений.")
            start_button.config(state=tk.NORMAL)
            stop_button.config(state=tk.DISABLED)
            return
    except ValueError:
        messagebox.showwarning("Внимание", "Пожалуйста, введите корректное число.")
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)
        return

    for query in queries:
        if query:
            thread = threading.Thread(target=search_bing_images, args=(query, num_images, uniquify_var.get()))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    if not stop_threads:
        messagebox.showinfo("Завершено", "Загрузка изображений завершена.")
    else:
        messagebox.showinfo("Прервано", "Загрузка изображений была прервана.")

# Функция для остановки загрузки
def stop_downloads():
    global stop_threads
    stop_threads = True
    stop_button.config(state=tk.DISABLED)

# GUI
root = tk.Tk()
root.title("Загрузчик изображений")

# Метка для отображения корневой папки
folder_label = tk.Label(root, text="Корневая папка не выбрана.")
folder_label.grid(row=0, column=0, columnspan=3, padx=5, pady=5)

# Кнопка для выбора корневой папки
choose_folder_button = tk.Button(root, text="Выбрать корневую папку", command=choose_root_folder)
choose_folder_button.grid(row=1, column=0, padx=5, pady=5)

# Поле для ввода запросов построчно
tk.Label(root, text="Введите запросы (каждый с новой строки):").grid(row=2, column=0, padx=5, pady=5)
query_text = tk.Text(root, width=30, height=10)
query_text.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

# Поле для ввода количества изображений
tk.Label(root, text="Количество изображений:").grid(row=4, column=0, padx=5, pady=5)
count_entry = tk.Entry(root, width=5)
count_entry.grid(row=4, column=1, padx=5, pady=5)

# Флажок для уникализации
uniquify_var = tk.BooleanVar()
uniquify_check = tk.Checkbutton(root, text="Уникализировать изображения", variable=uniquify_var)
uniquify_check.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

# Кнопка для запуска загрузки
start_button = tk.Button(root, text="Запустить загрузку", command=start_downloads)
start_button.grid(row=6, column=0, padx=5, pady=5)

# Кнопка для остановки загрузки
stop_button = tk.Button(root, text="Прервать загрузку", command=stop_downloads, state=tk.DISABLED)
stop_button.grid(row=6, column=1, padx=5, pady=5)

root.mainloop()
