# main.py
import tkinter as tk
from gui import ImageComparisonApp

def main():
    root = tk.Tk()
    app = ImageComparisonApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
