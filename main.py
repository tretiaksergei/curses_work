import requests
import json
from tqdm import tqdm


VK_URL = 'https://api.vk.com/method/photos.get'
with open('vk.txt') as VK:
    VK_TOKEN = VK.readline()
with open('ya.txt') as YA:
    ya_disk_api_token = YA.readline()


class User:
    def __init__(self, vk_token, ya_token):
        self.vk_token = vk_token
        self.ya_token = ya_token

    def ya_headers(self):
        return {'Content-Type': 'application/json',
                'Authorization': 'OAuth {}'.format(self.ya_token)}

    def vk_params(self, owner_id, album_id=input('Введите ID альбома:'), rev=0, extended=1, photo_sizes=0, count=5):
        return {'owner_id': owner_id,
                'album_id': album_id,
                'rev': rev,
                'extended': extended,
                'photo_sizes': photo_sizes,
                'count': count,
                'access_token': self.vk_token,
                'v': '5.131'}

    def photos_get(self, vk_user_id, count=5):
        try:
            response = requests.get(VK_URL, params=self.vk_params(vk_user_id, count=count))
            return response.json()['response']['items']
        except KeyError:
            print('Такого альбома нет, загружаем фото профиля')
            response = requests.get(VK_URL, params=self.vk_params(vk_user_id, album_id='profile', count=count))
            return response.json()['response']['items']

    def files_dict(self, vk_user_id, count=5):
        files = []
        size_types = ('w', 'z', 'y', 'x', 'r', 'q', 'p', 'o', 'm', 's')
        for item in self.photos_get(vk_user_id, count=count):
            file_data = {}
            file_name = str(item['likes']['count'])
            extension_str = item['sizes'][0]['url'].split('?')[0]
            extension = extension_str.split('.')[-1]
            if file_name+'.'+extension in [file['file_name'] for file in files]:
                file_data['file_name'] = file_name + '_' + str(item['date']) + '.' + extension
            else:
                file_data['file_name'] = file_name + '.' + extension
            for size_type in reversed(size_types):
                if size_type in [size['type'] for size in item['sizes']]:
                    file_data['file_size'] = size_type
            for size in item['sizes']:
                if size['type'] == file_data['file_size']:
                    file_data['file_url'] = size['url']
            files.append(file_data)
        with open('files_data.json', 'w') as write_file:
            json.dump(files, write_file)
        return files
       

    def ya_upload(self, file_path='/VK_profile_photos'):
        url_ya_upload = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        headers = self.ya_headers()
        status_codes = []
        for file in tqdm(files_data):
            params = {'url': file['file_url'],
                      'path': f"{file_path}/{file['file_name']}"}
            res = requests.post(url_ya_upload, headers=headers, params=params)
            status_codes.append(res.status_code)
        params = {'path': '/VK_profile_photos/files_data.json', 'overwrite': True}
        url_upload = requests.get(url_ya_upload, headers=headers, params=params).json().get('href', '')
        requests.put(url_upload, data=open('files_data.json', 'rb'))
        return status_codes

    def folder_creation(self, folder_path='/VK_profile_photos'):
        url_folder_creation = 'https://cloud-api.yandex.net/v1/disk/resources'
        headers = self.ya_headers()
        res = requests.put(url_folder_creation, headers=headers, params={'path': folder_path})
        if res.status_code == 409:
            answer = input('Такая папка уже существует, добавить в нее файлы?(y/n)')
            if answer == 'y':
                return True
        else:
            return True


if __name__ == '__main__':
    some_user = User(vk_token=VK_TOKEN, ya_token=ya_disk_api_token)
    files_data = some_user.files_dict(416299472, count=6)
    folder = some_user.folder_creation()
    if folder:
        print(f"\n{some_user.ya_upload()}")