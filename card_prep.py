from PIL import Image

def rotate_90_clock(img):
    with Image.open(img) as img:
        img.load()
        img = img.convert('L')
        img.rotate(-90, expand=1).save('data/cards/PovelitelMolniy_1_rot90.jpg') # .show()

def crop(path):
    with Image.open(path) as img:
        img.load()
        w, h = img.size
        cr = 10
        img.crop((cr, cr, w-cr, h//2+13)).save('data/cards/PovelitelMolniy_1.jpg') #.show()

rotate_90_clock('data/cards/PovelitelMolniy_1.jpg')
#crop('data/cards/PV.jpg')