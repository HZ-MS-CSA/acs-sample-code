#!/usr/bin/env python
# coding: utf-8
# %%


import os


# %%


target_phone_numbers_dir = './target_phone_numbers/'
os.makedirs(target_phone_numbers_dir, exist_ok=True)
required_info_dir = './required_info/'
os.makedirs(required_info_dir, exist_ok=True)
output_dir = './output/'
os.makedirs(output_dir, exist_ok=True)
archive_dir = './archive/'
os.makedirs(archive_dir, exist_ok=True)
print(f"{target_phone_numbers_dir}, {required_info_dir}, {output_dir}, {archive_dir} are created")

