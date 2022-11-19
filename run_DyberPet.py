from DyberPet.DyberPet import PetWidget
from DyberPet.utils import read_json
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    # 加载所有角色, 启动应用并展示第一个角色
    pets = read_json('res/pets.json')
    app = QApplication(sys.argv)
    p = PetWidget(pets=pets)
    sys.exit(app.exec_())