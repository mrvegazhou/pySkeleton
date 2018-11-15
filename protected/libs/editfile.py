#!/usr/bin/python
# -*- coding: utf8 -*-
import vcf
import os.path
class FileManage(object):
    file_dir = ''
    file_name = ''
    file_suffix = ''
    def get_suffix(self):
        return os.path.splitext(self.file_name)[-1]
    def __init__(self, file_dir):
        self.file_dir = file_dir
        self.file_name = os.path.basename(file_dir)
        self.file_suffix = self.get_suffix(self.file_name)

class FileFactory(object):
    def saveFile(self):
        pass

class VcfManage(FileManage):
    def read(self):
        pass
