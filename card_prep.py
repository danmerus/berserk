from PIL import Image

if __name__ == '__main__':
    with Image.open('data/cards/Draks.jpg') as img:
        img.load()
        w, h = img.size
        img.crop((2, 2, w-2, h//2+10)).save('data/cards/Draks_1.jpg')