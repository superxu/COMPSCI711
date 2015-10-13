

from Tkinter import *
entrysize = 40

class Form:                                           # add non-modal form box
    def __init__(self, labels, parent=None):          # pass field labels list
        labelsize = max(len(x) for x in labels) + 8
        box = Frame(parent) # box has rows, buttons
        box.pack(expand=YES, fill=BOTH)             
        rows = Frame(box, bd=2, relief=GROOVE)        # go=button or return key
        rows.pack(side=TOP, expand=YES, fill=BOTH)       # runs onSubmit method
        self.content = {}
        for label in labels:
            row = Frame(rows)
            row.pack()
            Label(row, text=label, width=labelsize).pack(side=LEFT)
            entry = Entry(row, width=entrysize)
            entry.pack(side=RIGHT, expand=YES, fill=BOTH)
            self.content[label] = entry

        Button(box, text='  Exit ', command = self.onExit).pack(side = BOTTOM)
        Button(box, text='Connect', command = self.onConnect).pack(side = BOTTOM)
        #box.master.bind('<Return>', (lambda event: self.onSubmit()))


        Lb1 = Listbox(box, selectmode = SINGLE)
        self.listbox = Lb1
        Lb1.insert(1, "image.gif")
        Lb1.insert(2, "Perl")
        Lb1.insert(3, "C")


        Lb1.pack(expand = YES, fill = BOTH)

        Button_download = Button(box, text = "Download", command = self.onDownload)
        Button_download.pack()

        Button_listfile = Button(box, text = "ListFiles", command = self.onListfiles)
        Button_listfile.pack()

    def onDownload(self):
        try:
            s = self.listbox.selection_get()
            print 'selected:', s
        except:
            print 'no selection'


    def onConnect(self):                                      # override this
        for key in self.content:                             # user inputs in
            print(key, '\t=>\t', self.content[key].get())    # self.content[k]

    def onExit(self):                                      # override if need
        Tk().quit()                                          # default is exit


    def onListfiles(self):
        pass

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
