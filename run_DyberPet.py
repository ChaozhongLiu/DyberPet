from DyberPet.DyberPet import PetWidget
from DyberPet.utils import read_json
from PyQt5.QtWidgets import QApplication
import sys


StyleSheet = '''
#PetHP {
    border: 2px solid #535053;
    border-radius: 7px;
}
#PetHP::chunk {
    background-color: #f44357;
    border-radius: 5px;
}

#PetEM {
    border: 2px solid #535053;
    border-radius: 7px;
}
#PetEM::chunk {
    background-color: #f6ce5f;
    border-radius: 5px;
}

#PetFC {
    border: 2px solid #535053;
    border-radius: 7px;
}
#PetFC::chunk {
    background-color: #47c0d2;
    border-radius: 5px;
}

QPushButton#InvenButton {
    background-color: #f184ae;
    color: #000000;
    border-style: outset;
    padding: 10px;
    font: bold 15px;
    border-width: 2px;
    border-radius: 10px;
    border-color: #facccc;
}
QPushButton#InvenButton:hover:!pressed {
    background-color: #ea4d8a;
}
QPushButton#InvenButton:pressed {
    background-color: #e72871;
}
QPushButton#InvenButton:disabled {
    background-color: #bcbdbc;
}
'''
if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json('data/pets.json')
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())