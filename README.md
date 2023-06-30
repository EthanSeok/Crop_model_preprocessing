# Crop model input data Preprocessing

작물 모형 입력자료를 통계청과 기상청 API를 기반으로 자동으로 다운받아 전처리 할 수 있도록 정리한 코드 

**다음 순서대로 실행할 것**

### 1. 밀 생산량(통계청) 자료
1. [preprocess/preprocess_kosis_01.py](preprocess/preprocess_kosis_01.py)
2. [preprocess/preprocess_kosis_02.py](preprocess/preprocess_kosis_02.py)

### 2. 기상자료
1. [preprocess/preprocess_APSIM.py](preprocess/preprocess_APSIM.py)
2. [preprocess/preprocess_AquaCrop.py](preprocess/preprocess_AquaCrop.py)
3. [preprocess/preprocess_DNDC.py](preprocess/preprocess_DNDC.py)
4. [preprocess/preprocess_DSSAT.py](preprocess/preprocess_DSSAT.py)

