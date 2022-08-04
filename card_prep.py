from PIL import Image

def rotate_90_clock(img1):
    with Image.open(img1) as img:
        img.load()
        img = img.convert('L')
        img.rotate(-90, expand=1).save(img1[:-4]+'_rot90.jpg')# .show()

def crop(path):
    with Image.open(path) as img:
        img.load()
        w, h = img.size
        cr = 11
        img.crop((cr, cr, w-cr, h//2+16)).save(path[:-9]+'.jpg') #.show()


img = 'data/cards/Necromant_1_full.jpg'
crop(img)
rotate_90_clock(img[:-9]+'.jpg')