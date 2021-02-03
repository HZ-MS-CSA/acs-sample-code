# MIT License
#
# Copyright (c) 2021 HZ-MS-CSA
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging

import azure.functions as func

import os
import cmd
import json
import time
from azure.communication.sms import PhoneNumber
from azure.communication.sms import SendSmsOptions
from azure.communication.sms import SmsClient
from datetime import datetime
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

def chunk_n_chunks(seq, size):
    return (seq[i::size] for i in range(size))

def main(acsBlob: func.InputStream):
    logging.info('Python Blob trigger function processed a request.')


    #----------------------Get connection strings and authenticate 2----------------------
    start_time = datetime.now().strftime("%H:%M:%S %d-%b-%Y")
    start = time.time()

    blobConnectionString = os.environ["stor_connection_string"]
    acsConnectionString = os.environ["acs_connection_string"]

    sms_client = SmsClient.from_connection_string(acsConnectionString)

    #----------------------Download input data----------------------
    blob_service_client = BlobServiceClient.from_connection_string(blobConnectionString)
    blob_client = blob_service_client.get_blob_client(container='acs-blob', blob='input_data.json')
    input_data_bytes = blob_client.download_blob().readall()
    input_data_str = input_data_bytes.decode('utf-8')
    input_data = json.loads(input_data_str)

    #---------------------Pre-process Data------------------------

    phone_numbers = input_data['dest_phone_numbers']

    for index in range(len(phone_numbers)):
        phone_numbers[index] = str(phone_numbers[index])
        if phone_numbers[index][:2] != '+1':
            phone_numbers[index] = '+1' + phone_numbers[index]
        phone_numbers[index] = phone_numbers[index].replace('-','')
        phone_numbers[index] = phone_numbers[index].replace(' ','')
        phone_numbers[index] = phone_numbers[index].replace('(','')
        phone_numbers[index] = phone_numbers[index].replace(')','')

    leased_numbers = input_data['origin_phone_numbers']
    for index in range(len(leased_numbers)):
        leased_numbers[index] = leased_numbers[index].lstrip().rstrip()
        if leased_numbers[index][:2] != '+1':
            leased_numbers[index] = '+1' + leased_numbers[index]
    
    leased_numbers_chunk_redistributed = list(chunk_n_chunks(phone_numbers, len(leased_numbers)))

    number_dict = {}
    index = 0
    for origin_number in leased_numbers:
        number_dict[origin_number] = leased_numbers_chunk_redistributed[index]
        index+=1
    
    message = input_data['message']

    #---------------------Send Message------------------------
    counter = 0
    master_counter = 0
    total_message_count = len(input_data['dest_phone_numbers'])
    problematic_numbers = []
    successful_numbers = []
    for origin_number in number_dict:
        for dest_number in number_dict[origin_number]:
            try:
                sms_response = sms_client.send(
                    from_phone_number=PhoneNumber(origin_number),
                    to_phone_numbers=[PhoneNumber(dest_number)],
                    message=message,
                    send_sms_options=SendSmsOptions(enable_delivery_report=True))
                successful_numbers.append(dest_number)
                counter += 1
                master_counter += 1
            except Exception:
                problematic_numbers.append(dest_number)
            if counter == 50:
                time.sleep(2)
                logging.info(f'{master_counter} out of {total_message_count} messages were sent successfully. {round(master_counter/total_message_count, 2)*100}% is completed.')
                counter = 0
    
    end_time = datetime.now().strftime("%H:%M:%S %d-%b-%Y")
    end = time.time()
    length = round((start - end) / 60,0)

    logging.info(f'{master_counter} out of {total_message_count} messages were sent successfully. {round(master_counter/total_message_count, 2)*100}% is completed. Took {length} minutes')
    

    summary = {
        'Message': message,
        'Successfully Sent Numbers': successful_numbers,
        'Failed Numbers': problematic_numbers,
        'Start Timestamp': start_time,
        'End Timestamp': end_time
    }

    #---------------------Clean up------------------------
    output_blob_client = blob_service_client.get_blob_client(container='acs-blob', blob='summary.txt')
    try:
        output_data_bytes = output_blob_client.download_blob().readall()
        output_data = output_data_bytes.decode('utf-8')
    except:
        output_data = ''
    output_data = output_data + json.dumps(summary)+'\n'

    output_blob_client.upload_blob(output_data, overwrite=True)

    archived_input = blob_service_client.get_blob_client(container='acs-blob', blob='input_data.json')

    archived_input.upload_blob(input_data_str, overwrite=True)

    blob_client.delete_blob()

    return None
