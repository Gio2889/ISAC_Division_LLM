# data_collector.py
import os
import json
from tqdm import tqdm
from CustomWikiScapper import CustomWikiScraper
from utils.data_collection_functions import (
    get_video_transcripts,
    get_wikipedia_data,
    get_webpage_data
    )

class DataCollector:
    def __init__(self, topic, custom_wiki_url= None,url_list =[]):
        self.topic = topic
        self.raw_data = []
        self.custom_wiki_url = custom_wiki_url
        self.url_list = url_list
        
    def collect(self):
        # YouTube transcript
        yt_transcripts = get_video_transcripts(self.topic)
        for document in yt_transcripts:
                self.raw_data.append(document)
                
        # Wikipedia data
        # wikipedia_page =  get_wikipedia_data(self.topic)
        # self.raw_data.append(wikipedia_page)
        
        # Custom wikis
        if self.custom_wiki_url:
            custom_wiki_scrapper = CustomWikiScraper(self.custom_wiki_url)
            documents = custom_wiki_scrapper.scrape_entire_wiki()
            for document in documents:
                self.raw_data.append(document)
        
        # # Spreadsheets/CSVs
        # for file in os.listdir("data/csv"):
        #     self.raw_data += load_csv_data(f"data/csv/{file}")
        
        if self.url_list:
            for url in self.url_list:
                documents = get_webpage_data(url)
                for document in documents:
                    self.raw_data.append(document)

        # Additional sources (PDFs, docs, etc.)
        # Implement using PyMuPDF or similar
        print(f"--- Collected a total of {len(self.raw_data)} sources ---")
    def save_raw(self, path):
        with open(path, 'w') as f:
            json.dump(self.raw_data, f)
            
    def load_raw(self, path):
        with open(path) as f:
            self.raw_data = json.load(f)

if __name__ == "__main__":
    test_url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTJEX5DerCvOj3a_m36TRy1gPBAUvrduOIdmXI9j1Y0MpQk1wIXaZ9KOcPa7HzXzp_N5qGmjDj6yEfL/pubhtml#'
    data_collector = DataCollector("The Division 2",r"https://thedivision.fandom.com/wiki/Tom_Clancy%27s_The_Division_2",[test_url])
    data_collector.collect()
    data_collector.save_raw("./data/scraped_data_v02.json")