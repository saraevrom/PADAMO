import tkinter as tk

class ButtonPanel(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.command_rows = []
        self.columnconfigure(0, weight=1)
        self._row_pointer = 0

    def _allocate_rows(self, rows):
        while rows > len(self.command_rows):
            index = len(self.command_rows)
            new_row = tk.Frame(self)
            new_row.grid(row=index, column=0, sticky="nsew")
            self.rowconfigure(index, weight=1)
            self.command_rows.append([new_row, 0])

    def advance(self):
        '''
        Advance row pointer by 1
        :return:
        '''
        self._row_pointer += 1

    def add_button(self, text, command, row=None):
        '''
        Add new button
        :param text: Button text
        :param command: Button action
        :param row: Row for button. If not supplied it will use internal number that can be increased by advance()
        :return:
        '''
        if row is None:
            row = self._row_pointer
        else:
            self._row_pointer = max(row, self._row_pointer)

        self._allocate_rows(row+1)
        frame, btn_count = self.command_rows[row]
        button = tk.Button(frame, text=text, command=command)
        button.grid(row=0, column=btn_count, sticky="ew")
        frame.columnconfigure(btn_count, weight=1)
        self.command_rows[row][1] += 1
