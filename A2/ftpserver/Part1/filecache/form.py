
import json
from Tkinter import *
entrysize = 40

class Form:                                           # add non-modal form box
    def __init__(self, parent=None):          # pass field labels list
   
        box = Frame(parent) # box has rows, buttons
        box.pack(expand=YES, fill=BOTH)             

        self.content = {}

        Button(box, text='  Exit ', command = self.onExit).pack(side = BOTTOM)

        Lb1 = Listbox(box, selectmode = SINGLE)
        self.listbox = Lb1


        Lb1.pack(expand = YES, fill = BOTH)

        text = Text(box, height=2, width=30)
        self.text = text
        text.pack(expand = YES, fill = BOTH)


        Button_download = Button(box, text = "Show files", command = self.onListfiles)
        Button_download.pack()

        Button_download = Button(box, text = "Show log", command = self.onShowlog)
        Button_download.pack()

        Button_listfile = Button(box, text = "Delete files", command = self.onDeletefile)
        Button_listfile.pack()


    def onShowlog(self, data):
        
        print data
        self.text.insert(END, data)



    def onDeletefile(self):                                  # override this
        for key in self.content:                             # user inputs in
            print(key, '\t=>\t', self.content[key].get())    # self.content[k]


    def onExit(self):                                      # override if need
        Tk().quit()                                          # default is exit


    def onListfiles(self, files):
        num = 0
        for item in files:
            num += 1
            strings = item.split(' ')
            #print("string = %s" % strings)
            self.listbox.insert(num, strings[-1].rstrip('\r\n'))


class DynamicForm(Form):
    def __init__(self, labels=None):
        labels = input('Enter field names: ').split()
        Form.__init__(self, labels)
    
    def onSubmit(self):
        print('Field values...')
        Form.onSubmit(self)
        self.onCancel()

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        Form(['Server', 'Port', 'Filename'])     # precoded fields, stay after submit
    else:
        DynamicForm()                    # input fields, go away after submit
    mainloop()
