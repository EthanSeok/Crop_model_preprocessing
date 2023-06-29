from datetime import datetime, timedelta
import json
import time
from urllib.parse import quote_plus, urlencode
import pandas as pd
import os
import requests
import tqdm
import numpy as np
import math
import csv
from datetime import datetime
import xlsxwriter as xlsxwriter
from openpyxl import load_workbook

times = datetime.today() - timedelta(days=1)
today = times.strftime("%m%d")

start = 2022
end = 2023

def load_data(stn_Ids, stn_Nm, output_dir_txt, site_info, latitude, longitude):
    cache_dir = "../output/cache_weather"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    url = 'http://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList'
    servicekey = 'HOhrXN4295f2VXKpOJc4gvpLkBPC/i97uWk8PfrUIONlI7vRB9ij088/F5RvIjZSz/PUFjJ4zkMjuBkbtMHqUg=='
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64)'
                             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132'
                             'Safari/537.36'}


    list_dfs = []
    for y in range(start, end+1):
        cache_filename = os.path.join(cache_dir, f"{stn_Ids}_{y}.csv")
        if not os.path.exists(cache_filename):
            params = f'?{quote_plus("ServiceKey")}={servicekey}&' + urlencode({
                quote_plus("pageNo"): "1",  # 페이지 번호 // default : 1
                quote_plus("numOfRows"): "720",  # 한 페이지 결과 수 // default : 10
                quote_plus("dataType"): "JSON",  # 응답자료형식 : XML, JSON
                quote_plus("dataCd"): "ASOS",
                quote_plus("dateCd"): "DAY",
                quote_plus("startDt"): f"{y}0101",
                quote_plus("endDt"): f"{y}1231" if y !=end else f"{y}{today}",
                quote_plus("stnIds"): f"{stn_Ids}"
            })
            try:
                result = requests.get(url + params, headers=headers)
            except:
                time.sleep(2)
                result = requests.get(url + params, headers=headers)

            try:
                js = json.loads(result.content)
            except:
                print('result contents', result.content)

            # print(result.content.decode('utf-8'))

            weather = pd.DataFrame(js['response']['body']['items']['item'])
            weather['year'] = pd.to_datetime(weather['tm']).dt.year
            weather['month'] = pd.to_datetime(weather['tm']).dt.month
            weather['day'] = pd.to_datetime(weather['tm']).dt.day

            weather['date'] = pd.to_datetime(weather[['year', 'month', 'day']])
            weather['day'] = weather['date'].dt.strftime('%j')

            '''
            sumRn: 일강수량, sumGsr: 합계 일사량, sumSmlEv: 합계 소형증발량, avgTa: 평균기온, minTa: 최저기온, maxTa: 최고기온
            avgTa: 평균기온, avgRhm: 평균상대습도, avgWs: 평균 풍속, sumSsHr: 합계 일조 시간

            평균기온, 평균습도, 일조시간, 북위, 해발고도, 풍속계 높이(10) | 일사량, 최고기온, 최저기온, 강수량, 증발산량
            '''


            # li = ['year', 'day', 'sumGsr', 'maxTa', 'minTa', 'sumRn', 'sumSmlEv', 'avgTa', 'avgRhm', 'avgWs', 'avgTca', 'month']
            li = ['year', 'month', 'day', 'sumGsr', 'maxTa', 'minTa', 'sumRn', 'sumSmlEv',
                  'avgTa', 'avgRhm', 'avgWs', 'sumSsHr']
            weather = weather.loc[:, li]
            weather = weather.apply(pd.to_numeric)
            weather.to_csv(cache_filename, index=False)
        else:
            weather = pd.read_csv(cache_filename)

        list_dfs.append(weather)

    df = pd.concat(list_dfs)
    df.columns = ['year', 'month', 'day', 'radn', 'maxt', 'mint', 'rain', 'evap',
              'tavg', 'humid', 'wind', 'sumradn']
    df['rain'] = df['rain'].fillna(0)

    '''일사량 & 증발산량 null 처리'''
    lati = latitude # 북위
    alti = 200 # 해발고도
    height = 10

    u_2 = df['wind'] * 4.87 / np.log(67.8 * height - 5.42)
    P = 101.3 * ((293 - 0.0065 * alti) / 293) ** 5.26
    delta = df['tavg'].apply(lambda x: 4098 * (0.6108 * np.exp((17.27 * x) / (x + 237.3))) / (x + 237.3) ** 2)
    gamma = 0.665 * 10 ** (-3) * P
    u_2_cal = 1 + 0.34 * u_2 # P
    Q = delta / (delta + gamma * u_2_cal) # Q
    R = gamma / (delta + gamma * u_2_cal) # R
    S = 900 / (df['tavg'] + 273) * u_2 # S
    e_s = df['tavg'].apply(lambda x: 0.6108 * np.exp((17.27 * x) / (x + 237.3)))
    e_a = df['humid'] / 100 * e_s
    e = e_s - e_a # e_s-e_a
    doi = df['day'] # day of year
    dr = doi.apply(lambda x: 1 + 0.033 * np.cos(2 * 3.141592 / 365 * x))
    small_delta = doi.apply(lambda x: 0.409 * np.sin(2 * 3.141592 / 365 * x - 1.39))
    theta = lati * math.pi / 180
    w_s = np.arccos(-np.tan(theta) * small_delta.apply(lambda x: np.tan(x)))

    Ra = 24 * 60 / math.pi * 0.082 * dr * \
               (w_s * small_delta.apply(lambda x: math.sin(x)) *
                np.sin(theta) +
                np.cos(theta) *
                small_delta.apply(lambda x: math.cos(x)) *
                w_s.apply(lambda x: math.sin(x)))
    N = 24 / math.pi * w_s
    Rs = (0.25 + 0.5 * df['sumradn'] / N) * Ra
    Rso = (0.75 + 2 * 10 ** (-5) * alti) * Ra
    Rs_Rso = Rs / Rso # Rs/Rso
    R_ns = 0.77 * Rs
    R_nl = 4.903 * 10 ** (-9) * (df['tavg'] + 273.16) ** 4 * (0.34 - 0.14 * e_a ** (0.5)) * (
                1.35 * Rs_Rso - 0.35)
    # df['Rn'] = R_ns - R_nl
    G = 0
    # df['ET'] = ((0.408) * (delta) * (df['Rn'] - G) + (gamma) * (900 / (df['tavg'] + 273)) * u_2 * (e)) / (
    #                 delta + gamma * (1 + 0.34 * u_2))
    ET = ((0.408) * (delta) * (R_ns - R_nl - G) + (gamma) * (900 / (df['tavg'] + 273)) * u_2 * (e)) / (
            delta + gamma * (1 + 0.34 * u_2))

    df['radn'] = df['radn'].fillna(round(R_ns, 3))
    # df['evap'] = df['evap'].fillna(round(ET, 3))
    #### end 일사량 & 증발산량  null 처리 ####


    filename = site_info[site_info['행정구역'] == stn_Nm]['영문 표기'].values[0]

    print(filename)

    df = df[['day', 'month', 'year', 'maxt', 'mint', 'rain', 'wind', 'humid', 'radn']]
    df['Et0(mm)'] = ET.round(1)
    df.rename(columns={'day': 'Doy',
                       'month': 'Month',
                       'year': 'Year',
                       'mint': 'Tmin(C)',
                       'maxt': 'Tmax(C)',
                       'rain': 'Prcp(mm)',
                       'wind': 'Wind at 10m',
                       'humid': 'RHmean',
                       'radn': 'Solar rad'}, inplace=True)

    df = df[['Doy', 'Month', 'Year', 'Tmin(C)', 'Tmax(C)', 'Prcp(mm)', 'Et0(mm)', 'Wind at 10m', 'RHmean', 'Solar rad']]

    for year in range(start, end+1):
        df_year  = df[df["Year"] == year]
        df_year = df_year[['Doy', 'Tmax(C)', 'Tmin(C)', 'Prcp(mm)', 'Wind at 10m', 'Solar rad', 'RHmean']].set_index('Doy')
        df_year.to_csv(os.path.join(f'{output_dir_txt}/{filename}_{year}.csv'))


    return filename


def main():
    output_dir = "../output/kosis/"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_dir_txt = "../output/DNDC/out_csv"
    if not os.path.exists(output_dir_txt):
        os.makedirs(output_dir_txt)

    # output_dir_met = "../output/weather_met/"
    # if not os.path.exists(output_dir_met):
    #     os.makedirs(output_dir_met)
    #
    # output_dir_xlsx = "../output/weather_xlsx/"
    # if not os.path.exists(output_dir_xlsx):
    #     os.makedirs(output_dir_xlsx)

    output_dir_wheat = "../output/kosis_wheat/"
    if not os.path.exists(output_dir_wheat):
        os.makedirs(output_dir_wheat)

    site_info = pd.read_excel('../input/한국행정구역분류.xlsx', sheet_name='1. 총괄표(현행)')
    site_info = site_info.rename(columns=site_info.iloc[1])
    site_info = site_info.drop(site_info.index[:2])
    site_info['영문 표기'] = site_info['영문 표기'].str.split('-').str[0]
    site_info[['시도', '시군구', '읍면동']] = site_info[['시도', '시군구', '읍면동']].fillna(" ")
    site_info['행정구역'] = site_info['시도'] + "_" + site_info['시군구'] + "_" + site_info['읍면동']
    site_info['행정구역'] = site_info['행정구역'].str.split(' ').str[0]
    site_info['행정구역'] = site_info['행정구역'].apply(lambda x: x.rstrip("_") if x.endswith("_") else x)

    station_code = pd.read_excel('../input/지점코드.xlsx')

    filenames_wheat = [x.strip(".csv") for x in os.listdir("../output/kosis/") if x.endswith(".csv")]

    station = pd.DataFrame(filenames_wheat, columns=['지점명'])
    station['파일명'] = station['지점명']
    station['지점명'] = station['지점명'].str.split('_').str[1].str[0:2]
    s = station['지점명'].to_list()
    f = station['파일명'].to_list()
    n = []
    for i in tqdm.tqdm(range(len(s))):
        a = station_code[station_code['지점명'] == s[i]]
        if a.empty:
            n.append(f[i])
        else:
            # try:
            stn_Ids = a['지점코드'].values[0].item()
            stn_Nm = f[i]
            latitude = a['위도'].values[0].item()
            longitude = a['경도'].values[0].item()
            filename = load_data(stn_Ids, stn_Nm, output_dir_txt, site_info, latitude, longitude)
            wheat = pd.read_csv(f"../output/kosis/{filenames_wheat[i]}.csv")
            wheat.to_csv(os.path.join(output_dir_wheat, f"{filename}_weather.csv"), index=False, encoding="utf-8-sig")

    filenames = [x for x in os.listdir(output_dir_txt) if x.endswith(".csv")]

    # output_weather_filename = os.path.join(output_dir_dssat, f"{filename}_weather.wth")
    for filename in filenames:
        out_path = f'../output/DNDC/out_txt/{filename[:-9]}'
        if not os.path.exists(out_path):
            os.makedirs(out_path)

        meta_info = f"""{filename[:-9]}\n"""
        with open(os.path.join(out_path, f"{filename.strip('.csv')}.txt"), "w") as fout:
            fout.write(meta_info)
            df = pd.read_csv(f'{output_dir_txt}/{filename}')
            # print(df.dtypes)
            for idx, row in df.iterrows():
                fout.write(
                    f"{int(row['Doy'])}  {row['Tmax(C)']}  {row['Tmin(C)']:3.1f}  {row['Prcp(mm)']:3.1f}  {row['Wind at 10m']:3.1f}  {row['Solar rad']:3.1f}  {row['RHmean']:3.1f}\n")

            # except KeyError:
            # print("KeyError: ", f[i])
    print("기상데이터 없음: ", n)



if __name__ == '__main__':
    main()