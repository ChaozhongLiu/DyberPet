"""
Buff System

Buff type by effect
    * Add: change status (cumulate value)
    (effective every n seconds for a certain time)
        - +/- HP
        - +/- FV
        - +/- Coins
    * Alt Alter status change (cumulate expiration)
    (effective for a certain time)
        - Stop HP decreasing
        - Stop FV increasing

Item config buff attribute
"buff":{
    "effect"
    "value"
    "interval"
    "expiration"
    "description"
}

"""
from PySide6.QtCore import Qt, Signal, QTimer, QObject, QThread

import DyberPet.settings as settings

########################################
#             Buff Class
########################################

class BuffAdd(QObject):
    takeEffect = Signal(str, int, name="takeEffect")
    removeBuff = Signal(str, int, name="removeBuff")
    terminateBuff = Signal(str, name="terminateBuff")

    def __init__(self, name, config):
        super().__init__()
        self.name = name
        self.effect = config['effect']
        self.value = config['value']
        self.interval = config['interval']
        self.timer = [(config['interval'], config.get('expiration', None))]
        self.expiration = config.get('expiration', None)
    
    def update(self):
        new_timer = []
        for i, (interval, expiration) in enumerate(self.timer):
            interval -= 1
            if interval == 0:
                self.trigger()
                interval = self.interval
            
            if self.expiration:
                expiration -= 1
                if expiration == 0:
                    self.endone(i)
                    continue
            
            new_timer.append((interval, expiration))
        
        if not new_timer:
            self.terminate()
        else:
            self.timer = new_timer
                
    def trigger(self):
        self.takeEffect.emit(self.effect, self.value)

    def addnew(self):
        self.timer.append((self.interval, self.expiration))
        return len(self.timer)-1
        
    def endone(self, idx=None):
        # ended by external signal
        if not idx:
            idx = len(self.timer)-1
            self.timer = self.timer[:-1]
        # else ended by timer

        self.removeBuff.emit(self.name, idx)
    
    def terminate(self):
        self.terminateBuff.emit(self.name)



class BuffAlt(QObject):
    takeEffect = Signal(str, name="takeEffect")
    removeBuff = Signal(str, int, name="removeBuff")
    terminateBuff = Signal(str, name="terminateBuff")

    def __init__(self, name, config):
        super().__init__()
        self.name = name
        self.effect = config['effect']
        self.timer = [config.get('expiration', None)]
        self.expiration = config.get('expiration', None)
    
    def update(self):
        new_timer = []
        for i, expiration in enumerate(self.timer):
            if self.expiration:
                expiration -= 1
                if expiration == 0:
                    self.endone(i)
                    continue
            new_timer.append(expiration)
        
        if not new_timer:
            self.terminate()
        else:
            self.timer = new_timer

    def addnew(self):
        self.timer.append(self.expiration)
        return len(self.timer)-1
        
    def endone(self, idx=None):

        # ended by external signal
        if not idx:
            idx = len(self.timer)-1
            self.timer = self.timer[:-1]
        # else ended by timer

        self.removeBuff.emit(self.name, idx)
    
    def terminate(self):
        self.terminateBuff.emit(self.name)



########################################
#          Buff System Thread
########################################

class BuffThread(QThread):
    addBuffUI = Signal(str, dict, int, name='addBuffUI')
    takeEffect = Signal(str, int, name="takeEffect")
    removeBuffUI = Signal(str, int, name="removeBuffUI")

    def __init__(self):
        super().__init__()

        self.buff_dict = {'add':{},
                          'alt':{}}
        self.effect_list = set(['hp','fv','coin','HP_stop','FV_stop'])
        self.add_list = set(['hp','fv','coin'])
        self.alt_list = set(['HP_stop','FV_stop'])
        self.HPstop = []
        self.FVstop = []

        self.timer = QTimer()
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

    def update(self):
        """ Run buff system every second """
        # Update count-down for each buff
        for buffName in list(self.buff_dict['add']):
            self.buff_dict['add'][buffName].update()
        
        for buffName in list(self.buff_dict['alt']):
            self.buff_dict['alt'][buffName].update()
    
    def _addBuff_fromItem(self, item_conf):
        buffInfo = item_conf.get('buff', {})
        if not buffInfo:
            return
        
        # get some basic information
        itemName = item_conf['name']
        buffEffect = buffInfo.get('effect', '')
        if buffEffect not in self.effect_list:
            return

        # add buff
        idx = self._addBuff(itemName, buffInfo)

        # send signal to StatusUI for buff display
        self.addBuffUI.emit(itemName, item_conf, idx)

    def _addBuff(self, buffName, buffInfo):
        buffType = self._getBuffType(buffName, buffInfo)

        # if no buff before
        if not self.buff_dict['add'] and not self.buff_dict['alt']:
            self.timer.start()

        # if buff already exists
        if buffName in self.buff_dict[buffType].keys():
            idx = self.buff_dict[buffType][buffName].addnew()
        else:
            idx = 0
            self.buff_dict[buffType][buffName] = self._getBuffClass(buffType)(buffName, buffInfo)
            self.buff_dict[buffType][buffName].takeEffect.connect(self._takeEffect)
            self.buff_dict[buffType][buffName].removeBuff.connect(self._removeBuff)
            self.buff_dict[buffType][buffName].terminateBuff.connect(self._terminateBuff)
        
            if buffType == 'alt':
                if buffInfo['effect'] == 'HP_stop':
                    self.HPstop.append(buffName)
                    settings.HP_stop = True
                elif buffInfo['effect'] == 'FV_stop':
                    self.FVstop.append(buffName)
                    settings.FV_stop = True
        
        return idx
    
    def _getBuffClass(self, buffType):
        clss = {'add': BuffAdd,
                'alt': BuffAlt}
        return clss[buffType]
    
    def _takeEffect(self, effect, value):
        self.takeEffect.emit(effect, value)

    def _removeBuff(self, buffName, idx):
        self.removeBuffUI.emit(buffName, idx)
    
    def _rmBuff(self, buffName):
        buffType = self._getBuffType(buffName)
        self.buff_dict[buffType][buffName].endone()
        if not len(self.buff_dict[buffType][buffName].timer):
            self.buff_dict[buffType][buffName].terminate()
    
    def _terminateBuff(self, buffName):
        buffType = self._getBuffType(buffName)
        self.buff_dict[buffType].pop(buffName)

        if buffName in self.HPstop:
            self.HPstop.remove(buffName)
        if buffName in self.FVstop:
            self.FVstop.remove(buffName)

        if not self.buff_dict['add'] and not self.buff_dict['alt']:
            self.timer.stop()

        if not self.HPstop:
            settings.HP_stop = False
        if not self.FVstop:
            settings.FV_stop = False
    
    def _getBuffType(self, buffName, buffInfo=None):
        if buffInfo:
            buffEffect = buffInfo.get('effect', '')
            buffType = 'add' if buffEffect in self.add_list else 'alt'
        else:
            if buffName in self.buff_dict['add'].keys():
                buffType = 'add'
            elif buffName in self.buff_dict['alt'].keys():
                buffType = 'alt'
            else:
                buffType = None

        return buffType

    def pause(self):
        self.timer.stop()

    def resume(self):
        self.timer.start()
            


        
        