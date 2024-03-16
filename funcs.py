import asyncio
import concurrent.futures
import os
import re

import aiohttp
from bs4 import BeautifulSoup
from tqdm import tqdm


def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('(\d+)', key)]
    return sorted(data, key=alphanum_key)


def rename_files(input_folder='./input', extension=".html"):
    for folder_name in os.listdir(input_folder):
        folder_path = os.path.join(input_folder, folder_name)
        if os.path.isdir(folder_path):
            files = sorted_alphanumeric(os.listdir(folder_path))
            if not files:
                print(f"В папке {folder_name} нет файлов")
                continue

            for i, file in enumerate(reversed(files), start=1):
                old_path = os.path.join(folder_path, file)
                if os.path.isfile(old_path):
                    new_filename = str(i) + extension
                    new_path = os.path.join(folder_path, new_filename)
                    try:
                        os.rename(old_path, new_path)
                    except FileExistsError:
                        pass
    return folder_name


async def download_image(session, url, path, cnt, progress_bar):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            file_path = os.path.join(path, f"{cnt}.jpg")
            with open(file_path, 'wb') as fd:
                content = await response.read()
                fd.write(content)
                progress_bar.update(1)
    except aiohttp.ClientError as e:
        print(f"Ошибка при загрузке изображения {url}: {e}")


async def download_images_from_file_async(session, file_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    with open(file_path, 'r') as file:
        lines = file.readlines()

    total_images = len(lines)

    with tqdm(total=total_images, desc="Загрузка изображений", unit="image") as progress_bar:
        tasks = []
        for cnt, line in enumerate(lines, start=1):
            url = line.strip()
            tasks.append(download_image(session, url, output_folder, cnt, progress_bar))

        await asyncio.gather(*tasks)


async def downloader_async(path='./photo', links='links.txt'):
    if not os.path.exists(path):
        os.makedirs(path)
    async with aiohttp.ClientSession() as session:
        await download_images_from_file_async(session, links, path)


def grabber(folder_name):
    path = f"./input/{folder_name}"
    count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])

    try:
        with open('links.txt', 'w') as y:
            soup = BeautifulSoup("", 'lxml')
            for idx in range(1, count + 1):
                file_path = f'{path}/{idx}.html'
                if os.path.exists(file_path):
                    with open(file_path, 'r') as x:
                        soup.clear()
                        soup = BeautifulSoup(x, 'lxml')
                        links = soup.select('a[href^="https://sun"]')
                        for link in links:
                            href = link.get('href')
                            y.write(f'{href}\n')
        summary = sum(1 for _ in open('links.txt', 'r'))
        return summary
    except FileNotFoundError:
        print('Фото не найдены.')
        return 0
