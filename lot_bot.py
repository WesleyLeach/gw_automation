#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Author  : Wleach
Date    : May 2023
Purpose : Collection of Invoices and metadata from Builder site

# TODO:  <20-05-23, wleach> #
Add Export function to json file for later hosting
Add notification channel for changes to invoice data

'''

import argparse
import hashlib
import logging
import json
import os
from pprint import pprint
import re
from typing import Text
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
import time


version = "0.3"

class Invoice_Collector(object):
    '''
    An object to represent the invoice collector bot itself
    '''


    def __init__(self) -> None:
        '''
        Initializes the Invoice Collector Object with pre-populated
        values
        '''
        super().__init__()
        self.builder_site = "https://mch.ihmsweb.com/"
        self.options = Options()
        self.driver = webdriver.Firefox(options=self.options)
        self.username = "dick01"
        self.password = "trade123"
        self.output_file = "/home/wonk/builders_state_file.json"
        # Checks if the state file exists. Otherwise it uses an empty dictionary
        if os.path.isfile(self.output_file):
            self.invoices = self._load_state_file()
        else:
            self.invoices = {}
        logging.debug("Collection BOT Initialized")

    def _load_state_file(self):
        '''
        Loads the saved state file to minimize redo'ing work
        '''
        with open(self.output_file, 'r') as input_file:
            # Loads the state file and returns it to caller
            return json.load(input_file)

    def collect_invoices(self):
        '''
        Instructs the invoice collector bot to collect invoices
        '''
        # Instucts the bot to login to the website
        self._login()
        # Instructs the bot to begin fetching invoices
        self._navigate_to_invoice_table()
        self._collect_invoices()

    def print_invoices(self):
        '''
        prints the invoices to the terminal
        '''
        pprint(self.invoices)

    def _write_state_file(self):
        '''
        Writes the state of bot to an output file
        '''
        # Opens a file handler with write permissions
        with open(self.output_file, 'w') as output_file:
            # Dumps the invoices list we've collected to a file
            json.dump(self.invoices, output_file)

    def _dict_hash(self) -> str:
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        # We need to sort arguments so {'a': 1, 'b': 2} is
        # the same as {'b': 2, 'a': 1}
        encoded = json.dumps(self.invoices, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    def _login(self):
        '''
        Logs into the builder's site with pre-set credentials
        '''
        time.sleep(2)
        logging.debug(f"Attemping to connect to {self.builder_site}")
        self.driver.get(self.builder_site)
        # This will search for the HTML form with the id "userid" in its field name
        time.sleep(2)
        logging.debug("Sending credential material")
        self.driver.find_element(By.XPATH, '//*[@id="userid"]').send_keys(
            self.username
        )
        password_field = self.driver.find_element(By.XPATH, '//*[@id="password"]')
        password_field.send_keys(
            self.password
        )
        time.sleep(1)
        password_field.send_keys(Keys.ENTER)
        time.sleep(2)
        logging.debug(f"Login Successful: {self.builder_site}, user: {self.username}")

    def _navigate_to_invoice_table(self):
        '''
        navigates to the invoices table
        '''
        logging.debug("Navigating to Invoice Table")
        self.driver.get('https://mch.ihmsweb.com/cgi-bin/ihmsweb.exe?pgm=marwjobs')
        time.sleep(2)
        # Navigates to the table that contains the Invoice data
        logging.debug("Selecting Job Invoices section")
        self.driver.find_element(
            By.XPATH,
            '/html/body/div[2]/div[1]/div[3]/table/tbody/tr[2]/td[1]/span/a'
        ).click()
        time.sleep(2)
        # Clicks the "All Developments" button on the invoices page
        logging.debug("Clicking 'All Developments button'")
        self.driver.find_element(
            By.XPATH,
            '/html/body/div[2]/div[1]/div[3]/div[3]/div/div/form/div/div[3]/div/label'
        ).click()
        time.sleep(2)

    def _collect_invoices(self):
        '''
        Manages the collection of invoices from the invoices page
        '''
        while True:
            logging.info("Grabbing Job Invoice List")
            development_list = self.driver.find_element(By.XPATH,'//*[@id="jobstart_filterableul"]')
            time.sleep(2)
            # A loop that will iterate over each item in the list tagged with 'li'
            # li stands for list item in HTML
            development_list_items = development_list.find_elements(By.TAG_NAME, "li")
            # If we have added all the list items to our invoice list return
            if len(development_list_items) == len(self.invoices.keys()):
                return
            # Navigates back to the start to collect the next invoice
            self.driver.back()
            # Clicks the "All Developments" button on the invoices page
            self.driver.find_element(
                By.XPATH,
                '/html/body/div[2]/div[1]/div[3]/div[3]/div/div/form/div/div[3]/div/label'
            ).click()
            time.sleep(2)
            self._fetch_invoice_data()
            self._write_state_file()

    def _fetch_invoice_data(self):
        '''
        Fetches an invoice number and associated data from Builders site
        '''
        # A list of invoices from the Invoices table
        logging.info("Itterating over Invoice list")
        development_list = self.driver.find_element(By.XPATH,'//*[@id="jobstart_filterableul"]')
        for invoice in development_list.find_elements(By.TAG_NAME, "li"):
            # Grabs the 10 digit invoice id
            invoice_id = re.findall(r'\d{10}', invoice.text)[0]
            # Slices the first two letters off. Slice notation
            # Basically get the second element (1) and then grab all remaining (empty)
            # NOTE computers count from 0
            invoice_id = str(invoice_id[1:])
            # Checks if we have already added this invoice
#            if invoice_id in self.invoices.keys():
#               continue
            time.sleep(2)
            # Clicks on the invoice
            invoice.click()
            time.sleep(4)
            logging.info("Selecting Table Row data")
            table_data = self.driver.find_elements(
                By.XPATH,
                '/html/body/div[2]/div[1]/div[3]/div[4]/div/table/tbody/tr'
            )
            for row in table_data:
                logging.info("Gathering data from each cell in table row")
                cells = row.find_elements(By.TAG_NAME, "td")
                self.invoices[invoice_id] = {
                    "address": cells[0].text,
                    "buyers_name": cells[1].text,
                    "home_phone": cells[2].text,
                    "work_phone": cells[3].text,
                    "email": cells[4].text,
                    "block_lot": cells[5].text,
                    "start_date": cells[6].text,
                    "model_elevation": cells[7].text,
                    "sales_person": cells[8].text,
                    "orientation": cells[9].text,
                    "solar_options": "unset",
                    "invoice_hash": "unset"
                }
            # Collecting Solar options information to addition to invoice table_data
            # This will crawl through the options table looking for solar
            options_details_table = self.driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[3]/div[9]/div/table/tbody')
            # Runner variable to control if the bot should read in options data
            read_in_options_data = False
            for row in options_details_table.find_elements(By.TAG_NAME, 'tr'):
                row_cells = row.find_elements(By.TAG_NAME, 'td')
                #pprint([x.text for x in row_cells])
                # Determines if this is a header row
                if len(row_cells) == 1:
                    # Checks if we've found the solar header
                    if row_cells[0].text == "SOLAR":
                        logging.info("Found Solar Header in Options Table")
                        read_in_options_data = True
                        # Initializes an empty list to eventually add solar options too
                        self.invoices[invoice_id]['solar_options'] = []
                        # Continue moves us to the next interation of the loop
                        continue
                    # Checks if we've found the next header after solar
                    elif read_in_options_data and row_cells[0].text != "Solar":
                        logging.info("End of Solar Options")
                        return
                cells = row.find_elements(By.TAG_NAME, 'td')
                if read_in_options_data:
                    self.invoices[invoice_id]['solar_options'].append(
                        f"{cells[1].text} : {cells[2].text}"
                    )
            # Creates a unique number based on invoice content at this moment
            invoice_hash = self._dict_hash()
            # If the invoice has has not been set i.e first time its seen set hash
            if self.invoices[invoice_id][invoice_hash] == "unset":
                self.invoices[invoice_id]['invoice_hash'] = invoice_hash
            if invoice_hash != self.invoices[invoice_id]['invoice_hash']:
                print("CHANGE HAS OCCURED. SEND TO NOTIFICATION CHANNEL")
            self.invoices[invoice_id]['invoice_hash'] = invoice_hash
            print(invoice_id)
            pprint(self.invoices[invoice_id])
            return

def main(args):
    '''
    Main Driver if called alone.
    :param args: an argparse object containing command line arguements.
    '''
    logging.basicConfig(level=args.logging)
    #Instantiates (Creates) an object of type Invoice Collector
    invoice_collector = Invoice_Collector()
    # Telling our new invoice collector object to run a function
    # in this case its collect_invoices()
    invoice_collector.collect_invoices()
    invoice_collector.print_invoices()
    exit(0)



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        add_help=False,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '-l',
        '--logging',
        action='store',
        required=False,
        default="INFO",
        choices= [
            "DEBUG",
            "WARN",
            "INFO",
            "CRITICAL",
            "ERROR"
        ]
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=args.logging,
        datefmt='%H:%M:%S'
    )
    main(args)

