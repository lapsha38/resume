Для установки нужно сделать это:
# установить последнюю версию python отсюда:
https://www.python.org/

# перейти в директорию с программой
cd ../mfc_pads

# установить зависимости для проекта
pip3 install -r requirements.txt

# установить nmap
# для linux:
sudo dnf install nmap
# для windows:
https://nmap.org/download.html
# ищи строки
Latest stable release self-installer
Latest Npcap release self-installer
# добавить в path винды путь до nmap. смотри тут первый ответ:
https://stackoverflow.com/questions/15335753/nmap-not-found-class-nmap-nmap-portscannererror

# поменять логин и пароль для входа в cisco тут:
../mfc_pads/config/conf.ini

# запустить основной файл:
python main.py

# ввести имя МФЦ отсюда:
http://mfc.ps.local/view/

PROFIT