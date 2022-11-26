from DyberPet.DyberPet import PetWidget
from DyberPet.utils import read_json
from PyQt5.QtWidgets import QApplication
import sys


StyleSheet = '''
#PetHP {
    border: 2px solid grey;
    border-radius: 7px;
}
#PetHP::chunk {
    background-color: #f44357;
    border-radius: 5px;
}

#PetEM {
    border: 2px solid grey;
    border-radius: 7px;
}
#PetEM::chunk {
    background-color: #f6ce5f;
    border-radius: 5px;
}
'''
if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json('data/pets.json')
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())