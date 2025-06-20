import PySimpleGUI as sg
from build_languages_library import build_languages_library
from parser import parser_repo

def main():
    sg.theme('LightBlue')

    layout = [
        [sg.Text('Путь до репозитория:'), sg.InputText(key='-PATH-'), sg.FolderBrowse()],
        [sg.Button('Старт', key='-START-'), sg.Button('Exit')],
        [sg.Button('Создать so файл', key='-CREATE_SO-')]
    ]

    window = sg.Window('AutoDoc Generator', layout, size=(500, 120))

    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Exit'):
            break

        if event == '-START-':
            repo_path = values['-PATH-']
            if repo_path:
                parser_repo(repo_path, out_md="test/report.md")
                sg.popup(f'Запуск генерации документации для:\n{repo_path}')
                
            else:
                sg.popup('Пожалуйста, укажите путь до репозитория.')
                
        if event == '-CREATE_SO-':
            build_languages_library()
            sg.popup('Файл so успешно создан!')

    window.close()


if __name__ == '__main__':
    main()
