from Tkinter import *
import tkMessageBox
import Tkinter


root = Tk()

root.title("Client")
root.geometry("500x300")

Lb1 = Listbox(root, selectmode = SINGLE, width = 100)
Lb1.insert(1, "Python")
Lb1.insert(2, "Perl")
Lb1.insert(3, "C")
Lb1.insert(4, "PHP")
Lb1.insert(5, "JSP")
Lb1.insert(6, "Ruby")

Lb1.pack()


def check_list():
    try:
        s = Lb1.selection_get()
        print 'selected:', s
    except:
        print 'no selection'


def list_server_files():
    print 'File list:'



Button_download = Button(root, text="Download", command=check_list)
Button_download.pack()

Button_listfile = Button(root, text="ListFiles", command=list_server_files)
Button_listfile.pack()

root.mainloop()
