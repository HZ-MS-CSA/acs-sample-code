#!/usr/bin/env python
# coding: utf-8

# MIT License
# 
# Copyright (c) 2021 HZ-MS-CSA
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# 

# Note
# 
# For **target_phone_number** folder (to be created automatically), please upload any csv file into this directory. The first column will be used as target phone numbers
# 
# For **required_info** folder (to be created automatically), two text files are required:
# 
# - leased_numbers.txt (Each line contains **1** leased number from ACS)
# - message.txt (Messages can be on different lines. All lines in this text file will be collected and sent out as one message)

# The program will equally distribute all target numbers across available leased numbers. Message will be sent out one after another with random sleeping period of 1-3 seconds. 
# 
# Batch processing codes are commented out for future iterations.

# ### Set up

# In[ ]:


import os
import getpass 
import pandas as pd
import glob
import time
import random as rand
import json
from azure.communication.sms import PhoneNumber
from azure.communication.sms import SendSmsOptions
from azure.communication.sms import SmsClient
from tqdm import tqdm


# In[ ]:


target_phone_numbers_dir = './target_phone_numbers/'
os.makedirs(target_phone_numbers_dir, exist_ok=True)


# In[ ]:


required_info_dir = './required_info/'
os.makedirs(required_info_dir, exist_ok=True)


# In[ ]:


output_dir = './output/'
os.makedirs(output_dir, exist_ok=True)


# In[ ]:


archive_dir = './archive/'
os.makedirs(archive_dir, exist_ok=True)


# In[ ]:


def chunk_equal_size(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# In[ ]:


def chunk_n_chunks(seq, size):
    return (seq[i::size] for i in range(size))


# ### Authentication

# In[ ]:


key_name = 'COMMUNICATION_SERVICES_CONNECTION_STRING'
 
connection_string_os_value = getpass.getpass(prompt='Please enter COMMUNICATION_SERVICES_CONNECTION_STRING:\n')
 
os.environ[key_name] = connection_string_os_value
 
print(f'{key_name} environment variable has been set.')


# In[ ]:


# This code demonstrates how to fetch your connection string
# from an environment variable.
connection_string = os.getenv('COMMUNICATION_SERVICES_CONNECTION_STRING')

# Create the SmsClient object which will be used to send SMS messages
sms_client = SmsClient.from_connection_string(connection_string)


# ### Process input

# In[ ]:


for file in glob.glob(f'{target_phone_numbers_dir}*.csv'):
    input_filename = file


# In[ ]:


input_data = pd.read_csv(input_filename)


# In[ ]:


phone_numbers = list(input_data[list(input_data)[0]])


# In[ ]:


for index in range(len(phone_numbers)):
    phone_numbers[index] = str(phone_numbers[index])
    if phone_numbers[index][:2] != '+1':
        phone_numbers[index] = '+1' + phone_numbers[index]
    phone_numbers[index] = phone_numbers[index].replace('-','')
    phone_numbers[index] = phone_numbers[index].replace(' ','')


# In[ ]:


with open(f'{required_info_dir}leased_numbers.txt','r') as file:
    leased_numbers = file.readlines()
for index in range(len(leased_numbers)):
    leased_numbers[index] = leased_numbers[index].lstrip().rstrip()
    if leased_numbers[index][:2] != '+1':
        leased_numbers[index] = '+1' + leased_numbers[index]


# In[ ]:


with open(f'{required_info_dir}message.txt','r') as file:
    messagelines = file.readlines()
message = ' '.join(messagelines).replace('\n','')


# ### Send Message

# In[ ]:


# NOT TO BE EXECUTED. RESERVED FOR BATCH PROCESSING
# leased_numbers_chunk = list(chunk_equal_size(phone_numbers, 1))
# leased_numbers_chunk_redistributed = list(chunk_n_chunks(leased_numbers_chunk, len(leased_numbers)))


# In[ ]:


leased_numbers_chunk_redistributed = list(chunk_n_chunks(phone_numbers, len(leased_numbers)))


# In[ ]:


number_dict = {}
index = 0
for origin_number in leased_numbers:
    number_dict[origin_number] = leased_numbers_chunk_redistributed[index]
    index+=1


# In[ ]:


counter = 0
problematic_numbers = []
successful_numbers = []
for origin_number in tqdm(number_dict):
    for dest_number in tqdm(number_dict[origin_number]):
        try:
            sms_response = sms_client.send(
                from_phone_number=PhoneNumber(origin_number),
                to_phone_numbers=[PhoneNumber(dest_number)],
                message=message,
                send_sms_options=SendSmsOptions(enable_delivery_report=True))
            successful_numbers.append(dest_number)
            counter += 1
        except Exception:
            problematic_number.append(dest_number)
        if counter == 50:
            time.sleep(2)
            counter = 0


# In[ ]:


# NOT TO BE EXECUTED. RESERVED FOR BATCH PROCESSING
# for origin_number in number_dict:
#     for dest_number_chunks in number_dict[origin_number]:
#         dest_number_chunks_phone = []
#         for dest_number in dest_number_chunks:
#             dest_number_chunks_phone.append(PhoneNumber(dest_number))
#         sms_response = sms_client.send(
#                 from_phone_number=PhoneNumber(origin_number),
#                 to_phone_numbers=dest_number_chunks_phone,
#                 message=message,
#             send_sms_options=SendSmsOptions(enable_delivery_report=True))
#         time.sleep(rand.randint(1,3))


# ### Clean up

# In[ ]:


os.rename(input_filename,input_filename.replace('./target_phone_numbers/',archive_dir))
# os.rename(f'{required_info_dir}leased_numbers.txt',f'{archive_dir}leased_numbers.txt')
os.rename(f'{required_info_dir}message.txt',f'{archive_dir}message.txt')


# In[ ]:


# os.rename(input_filename.replace('./target_phone_numbers/',archive_dir), input_filename)
# # os.rename(f'{required_info_dir}leased_numbers.txt',f'{archive_dir}leased_numbers.txt')
# os.rename(f'{archive_dir}message.txt', f'{required_info_dir}message.txt')


# In[ ]:


summary = {
    'Message': message,
    'Successful Sent Numbers': successful_numbers,
    'Failed Numbers': problematic_numbers
}


# In[ ]:


with open(f"{output_dir}summary.txt",'a') as file:
    file.write(json.dumps(summary)+'\n')

