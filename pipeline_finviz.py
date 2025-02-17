from finvizfinance.quote import finvizfinance
import pandas as pd
import numpy as np
import os
import time
from dotenv import load_dotenv
from datetime import datetime

from utils import upload_to_hf_dataset, download_from_hf_dataset, load_hf_dataset

# Get current date and time
# current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
current_datetime = datetime.now().strftime("%Y-%m-%d")

# Create the gurufocus folder if it doesn't exist
if not os.path.exists('finviz'):
    os.makedirs('finviz')



# Load environment variables from .env file
# load_dotenv()

# Get the name of the HuggingFace dataset for TradingView to read from
dataset_name_TradingView_input = os.getenv('dataset_name_TradingView_input')

# Get the name of the HuggingFace dataset for FinViz to export
dataset_name_FinViz_output = os.getenv('dataset_name_FinViz_output')

# Get the Hugging Face API token from the environment; either set in .env file or in the environment directly in GitHub
HF_TOKEN_FINVIZ = os.getenv('HF_TOKEN_FINVIZ')

#Load lastest TradingView DataSet from HuggingFace Dataset which is always america.csv
# download_from_hf_dataset("america.csv", "AmirTrader/TradingViewData", HF_TOKEN_FINVIZ)
DF = load_hf_dataset("america.csv", HF_TOKEN_FINVIZ, dataset_name_TradingView_input)

# get ticker list by filtering only above 1 billion dollar company
# DF = pd.read_csv(f'america_2024-03-01.csv')
tickerlst  = list(DF.query('`Market Capitalization`>1e8').Ticker)

##################################################################################################################
#main loop; wait 15 second for every 20 ticker
dfs = []
counter=0
maxiter = len(tickerlst )
for ticker in tickerlst :
  if not '/' in ticker:
    counter+=1
    print(f"{counter} out of {maxiter}  -  {ticker}")
    if counter % 20 ==0:
      time.sleep(15)
    try:
      stock = finvizfinance(ticker)
      mydict = stock.ticker_fundament()
      mydict['Ticker'] =ticker
      dfs.append(mydict)
    except:
      print('***ERROR')
      pass

# Concatenate the DataFrames in the list to create a single DataFrame    
DFtotal = pd.DataFrame(dfs)

file_path = fr'finviz/FinViz_{current_datetime}.csv'
latest_file_path = fr'finviz/FinViz.csv'

DFtotal.to_csv(file_path,index=False)
DFtotal.to_csv(latest_file_path,index=False)

# Upload each file to the dataset
upload_to_hf_dataset(file_path, dataset_name_FinViz_output, HF_TOKEN_FINVIZ, repo_type="dataset")
upload_to_hf_dataset(latest_file_path, dataset_name_FinViz_output, HF_TOKEN_FINVIZ, repo_type="dataset")