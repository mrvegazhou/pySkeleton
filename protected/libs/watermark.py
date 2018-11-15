# -*- coding: utf-8 -*-
try:
    import PIL.Image
    import PIL.ImageChops
    import PIL.ImageOps
    import PIL.ImageDraw
    import PIL.ImageFont
    import PIL.ImageEnhance

except ImportError:
    import sys
    sys.exit("PIL is not installed.\n")

import os
import shutil
import argparse

class Watermark(object):

    def __init__(self, image_path, pos, ext, watermarkimage, renamedFilesNames, watermarkeddir, verbose):

        if self.checkPath(image_path):
            self.path = os.path.abspath(image_path)

        else:
            print("Incorrect path.")

        self.wmi = watermarkimage
        self.wdr = watermarkeddir
        self.ext = ext
        self.rfn = renamedFilesNames
        self.ver = verbose

        # Functions calls.
        self.checkWdr(self.path, self.wdr)
        self.imgs = self.grabImages(self.path, self.ext)

    @staticmethod
    def checkWdr(cwd, wdr):
        os.chdir(cwd)
        if not os.path.isdir(wdr):
            os.mkdir(wdr)

    @staticmethod
    def checkPath(path):
        if os.path.isdir(path):
            return True

        return False

    @staticmethod
    def grabImages(path, ext):
        images = []

        for folder, subfolder, files in os.walk(path):

            for sb in subfolder:
                for file in sb:
                    if file.endswith(ext):
                        images.append(os.path.join(folder, sb, file))

            for file in files:
                if file.endswith(ext):
                    images.append(os.path.join(folder, file))

        return images

    def watermark(self, pos):
        # TODO: Add more positions support.
        # TODO: Multithreading

        os.chdir(self.path)
        watermarkImage = PIL.Image.open(self.wmi).convert("RGBA")

        if pos == "RD":
            counter = 0

            for image in self.imgs:
                if self.ver:
                    print("Watermarking: {}".format(image))

                img = PIL.Image.open(image)
                img.paste(watermarkImage, (img.size[0] - watermarkImage.size[0], img.size[1] - watermarkImage.size[1]), watermarkImage)

                counter += 1
                name = "{}{}.{}".format(self.rfn, counter, self.ext)
                img.save(name)

                shutil.move(os.path.join(self.path, name), self.wdr)

        elif pos == "MIDDLE":
            counter = 0

            for image in self.imgs:
                if self.ver:
                    print("Watermarking: {}".format(image))

                img = PIL.Image.open(image)
                img.paste(watermarkImage, (img.size[0] // 2, img.size[1] // 2), watermarkImage)

                counter += 1
                name = "{}{}.{}".format(self.rfn, counter, self.ext)
                img.save(name)

                shutil.move(os.path.join(self.path, name), self.wdr)

    def textWatermark(self, text, fill = None, font = None, size = 20):
        # TODO: Add custom font support.
        # TODO: Add custom position support.
        # TODO: Multithreading

        counter = 0

        for image in self.imgs:
            if self.ver:
                print("Watermarking: {}".format(image))

            img = PIL.Image.open(image)
            PIL.ImageDraw.Draw(img).text((img.size[0] / 2, img.size[1] / 2), text, fill, font)

            counter += 1
            name = "{}{}.{}".format(self.rfn, counter, self.ext)
            img.save(name)

            shutil.move(os.path.join(self.path, name), self.wdr)

class CLI(object):

    def arguments(self):
        arg = argparse.ArgumentParser(description = "Basic watermake creator")
        arg.add_argument("-l", help = "Images location.", type = str)
        arg.add_argument("-w", help = "Watermark image location", type = str)
        arg.add_argument("-d", help = "The name of the directory in witch the watermaked images will be moved.", type = str)
        arg.add_argument("-e", help = "The extension that the watermarked images will be saved with.", type = str)
        arg.add_argument("-r", help = "The name of watermarked images.", type = str)
        arg.add_argument("-p", help = "Position.\nSupported: MIDDLE, RD(Right Down).", type = str)
        arg.add_argument("-t", help = "Add text to images.", type = str)
        arg.add_argument("-i", help = "Add a watermark image.", default = True, action = "store_true")
        arg.add_argument("-v", help = "Be verbose.", default = True, action = "store_true")

        return arg.parse_args()

    @classmethod
    def cli(cls):
        args = cls.arguments(cls)

        wm = Watermark(args.l, args.p, args.e, args.w, args.r, args.d, args.v)

        try:
            if args.t:
                wm.textWatermark(args.t)

            if args.i:
                wm.watermark(args.p)

        except Exception as e:
            print("Error -> {}".format(e))

        finally:
            print("Done.")

CLI.cli()