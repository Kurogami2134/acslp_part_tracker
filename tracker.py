from ModIO import PspRamIO
from json import load
from tkinter import *
from tkinter.ttk import *
from struct import unpack


TOTAL_PART_COUNTS = {
    'HEADS': 21,
    'CORES': 12,
    'ARMS': 39,
    'LEGS': 61,
    'BOOSTER': 11,
    'FCS': 12,
    'GENERATOR': 9,
    'RADIATOR': 9,
    'INSIDE': 22,
    'EXTENSION': 28,
    'BACK_UNIT': 80,
    'ARM_UNIT_R': 82,
    'ARM_UNIT_L': 43,
    'OPTIONAL': 20
}
PART_IDX = {list(TOTAL_PART_COUNTS.keys())[x]: x for x in range(len(TOTAL_PART_COUNTS))}

with open('sl_parts.json', 'r', encoding='utf-8') as file:
    PARTS = load(file)


class ArmoredCoreInventory:
    def __init__(self, ram: PspRamIO) -> None:
        self.ram = ram
    
    @property
    def inventory_start(self) -> int:
        self.ram.seek(0x9044c30)
        return unpack("I", self.ram.read(4))[0]+0x3AA4
    
    def owned_parts(self, type: str) -> list[int]:
        cnt: int
        parts: list[int] = []
        self.ram.seek(self.inventory_start + PART_IDX[type] * 0x204 + 0x200)
        cnt = self.ram.read(1)[0]
        self.ram.seek(self.inventory_start + PART_IDX[type] * 0x204)
        for _ in range(cnt):
            parts.append(self.ram.read(4)[0])
        
        return parts


def get_part_names(type: str, parts: list[int]) -> list[str]:
    return [PARTS[type][part]['NAME'] for part in parts]


def get_part_details(type: str, parts: list[int]) -> list[str]:
    return [PARTS[type][part]['UNLOCK'] for part in parts]


class CollapsableFrame(Frame):
    def __init__(self, master = None, name: str = '', collapsed: bool = False, width: int = 20):
        super().__init__(master, borderwidth=0, width=width)
        self.collapsed: bool = collapsed
        self.name = name
        self.collapse_button: Button = Button(self, command=self.toggle, text=f'{name + " " if name else ""}{"▼" if collapsed else "▲"}', width=25, padding=0)
        self.frame = Frame(self)
        
        self.collapse_button.grid(row=0, column=0, sticky='WE')
        if not collapsed:
            self.frame.grid(row=1, column=0, sticky='NSWE')

    
    def toggle(self):
        self.collapsed = not self.collapsed
        self.collapse_button.config(text=f'{self.name + " " if self.name else ""}{"▼" if self.collapsed else "▲"}')
        if self.collapsed:
            self.frame.grid_forget()
        else:
            self.frame.grid(row=1, column=0, sticky='NSWE')


class Tracker(Tk):
    def __init__(self):
        super().__init__()
        self.title('Silent Line Part Tracker')
        self.wm_attributes('-transparentcolor', 'purple')
        self.wm_attributes('-fullscreen', 'true')
        self.wm_attributes('-topmost', 'true')
        self.config(bg='purple')

        self.inventory: ArmoredCoreInventory
        
        self.frame = CollapsableFrame(self, 'Silent Line Part Tracker')
        self.frame.pack(side=TOP, anchor=NE)

        self.mainframe = self.frame.frame

        self.tree = Treeview(self.mainframe, show="tree", height=14)
        self.tree.tag_configure(background='#CCCCCC', tagname='even')
        self.tree.tag_configure(background='#BBBBBB', tagname='odd')
        self.tree.bind('<ButtonRelease-1>', self.set_item)
        self.bind('<Return>', self.set_item)

        self.text = Text(self.mainframe, width=20, height=15, wrap='word')        

        self.show_all = BooleanVar()

        self.tree.pack()
        
        Checkbutton(self.mainframe, variable=self.show_all, text='Show all').pack()
        Button(self.mainframe, command=self.load_parts, text='reload').pack()

        self.text.pack()
    
    def set_text(self, text: str) -> None:
        self.text.config(state=NORMAL)
        self.text.delete(1.0, END)
        self.text.insert(END, text)
        self.text.config(state=DISABLED)
    
    def set_item(self, e) -> None:
        self.set_text(self.tree.item(self.tree.focus())['text'])
    
    def load_parts(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for part_type in TOTAL_PART_COUNTS.keys():
            category = self.tree.insert('', END, text=part_type)
            even: bool = False
            owned_parts: list[int] = self.inventory.owned_parts(part_type)
            for part_idx in range(len(PARTS[part_type])):
                part = PARTS[part_type][part_idx]
                if isinstance(part, str):
                    continue
                owned = '✅' if part_idx in owned_parts else '❌'
                
                if not self.show_all.get() and part_idx in owned_parts:
                    continue

                part_item = self.tree.insert(category, END, text=owned + part['NAME'], tags=('even' if even else 'odd'))
                self.tree.insert(part_item, END, text=part['UNLOCK'])
                even = not even
            if len(PARTS[part_type]) == 0:
                self.tree.delete(category)

    def run(self):
        self.inventory = ArmoredCoreInventory(PspRamIO())
        self.load_parts()
        self.mainloop()


if __name__ == '__main__':
    t = Tracker()
    t.run()
