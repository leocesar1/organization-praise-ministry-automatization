import re

def convert_google_sheet_url(url):
    # Regular expression to match and capture the necessary part of the URL
    pattern = r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)(/edit#gid=(\d+)|/edit.*)?'

    # Replace function to construct the new URL for CSV export
    # If gid is present in the URL, it includes it in the export URL, otherwise, it's omitted
    replacement = lambda m: f'https://docs.google.com/spreadsheets/d/{m.group(1)}/export?' + (f'gid={m.group(3)}&' if m.group(3) else '') + 'format=csv'

    # Replace using regex
    new_url = re.sub(pattern, replacement, url)

    return new_url

import pandas as pd
import numpy as np
from datetime import date, datetime

# Replace with your modified URL

def isHoliday():
    url = 'https://docs.google.com/spreadsheets/d/1OKD8RmkIqZvezzMurGF32gRYoU4DcHNEBRwZkJzwzjw/edit#gid=1896094214'
    new_url = convert_google_sheet_url(url)
    df = pd.read_csv(new_url)

    df['Fim']   = np.where(df['Fim'].isnull(), df['Inicio'], df['Fim'])

    df['start'] = pd.to_datetime(df['Inicio']+" 00:00:00", format="%d/%m/%Y %H:%M:%S")
    df['end']   = pd.to_datetime(df['Fim']+" 23:59:59", format="%d/%m/%Y %H:%M:%S")

    df['holiday'] = df.apply(lambda x: verifyHoliday(x['start'], x['end']), axis=1)

    print(df.head())
    holidayDataframe = df[df['holiday'] == True]['Motivo']
    return( holidayDataframe.size > 0, holidayDataframe.iloc[0] if holidayDataframe.size > 0 else 'Dia normal')

def verifyHoliday(start,end,target = datetime.now()):
    return True if start <= target <= end else False
# trata fim vazio

print(isHoliday())