import PySimpleGUI as sg
import subprocess

# 각 파일에 대한 정보
files = [
    {
        'name': 'Kosis 생산량 다운로드',
        'path': './preprocess_kosis_dy.py'
    },
    {
        'name': 'APSIM 입력자료 정리',
        'path': './preprocess_APSIM.py'
    },
    {
        'name': 'AquaCrop 입력자료 정리',
        'path': './preprocess_AquaCrop.py'
    },
    {
        'name': 'DNDC 입력자료 정리',
        'path': './preprocess_DNDC.py'
    },
    {
        'name': 'DSSAT 입력자료 정리',
        'path': './preprocess_DSSAT.py'
    }
]

sg.theme('DarkBlue')

layout = [
    [sg.Text('옵션을 선택하세요', font=('Arial', 13))],
    [sg.Listbox(values=[file['name'] for file in files], size=(30, len(files)), key='-FILES-', font=('Arial', 12))],
    [sg.Output(size=(50, 10), font=('Arial', 12))],  # 결과를 출력할 Output 컨트롤 추가
    [sg.Button('실행', font=('Arial', 10)), sg.Button('종료', font=('Arial', 10))]
]

window = sg.Window('model preprocessing', layout)

while True:
    event, values = window.read()

    if event == sg.WINDOW_CLOSED or event == '종료':
        break

    if event == '실행':
        selected_files = [file for file in files if file['name'] in values['-FILES-']]
        for file in selected_files:
            command = ['python', file['path']]
            output = subprocess.check_output(command, shell=True, encoding='utf-8')  # 명령 실행 결과 받기
            print(f'--- {file["name"]} 실행 결과 ---')
            print(output)
            print('---' + '-' * len(file['name']) + ' 실행 완료 ---\n')

window.close()
