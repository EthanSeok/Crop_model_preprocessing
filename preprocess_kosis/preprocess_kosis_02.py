import pandas as pd
import os

def main():
    # 밀 생산량 데이터 지역 - 밀 생산량 파일명
    filenames_wheat = [x.strip(".csv") for x in os.listdir("../output/kosis/") if x.endswith(".csv")]

    # 측구소 번호 - 지점코드.xlsx
    wheat_filename = pd.DataFrame(filenames_wheat, columns=['지점명'])
    wheat_filename['파일명'] = wheat_filename['지점명']
    wheat_filename['지점명'] = wheat_filename['지점명'].str.split('_').str[1].str[0:2]
    site_code = pd.read_excel('../input/지점코드.xlsx')
    site_code = pd.merge(site_code, wheat_filename, on='지점명', how='inner')

    # 지역명 - 한국행정구역분류.xlsx
    site_class = pd.read_excel('../input/한국행정구역분류.xlsx', sheet_name='1. 총괄표(현행)')
    site_class = site_class.rename(columns=site_class.iloc[1])
    site_class = site_class.drop(site_class.index[:2])
    site_class['영문 표기'] = site_class['영문 표기'].str.split('-').str[0]
    site_class[['시도', '시군구', '읍면동']] = site_class[['시도', '시군구', '읍면동']].fillna(" ")
    site_class['행정구역'] = site_class['시도'] + "_" + site_class['시군구'] + "_" + site_class['읍면동']
    site_class['행정구역'] = site_class['행정구역'].str.split(' ').str[0]
    site_class['행정구역'] = site_class['행정구역'].apply(lambda x: x.rstrip("_") if x.endswith("_") else x)
    site_class = site_class[['영문 표기', '행정구역']]

    # 지역별 정보 병합
    site_info = pd.merge(site_code, site_class, left_on='파일명', right_on='행정구역', how='inner')
    site_info = site_info[['파일명', '영문 표기', '지점코드', '위도', '경도', '고도']]

    site_info.to_csv("../output/통계청_정보.csv", index=False)


if __name__ == '__main__':
    main()