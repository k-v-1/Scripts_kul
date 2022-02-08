from tkinter import *
from tkinter.filedialog import askopenfilename
from PIL import Image, ImageFilter, ImageEnhance
from PIL import ImageTk
import numpy as np
import matplotlib.pyplot as plt
# from pathfinding.core.diagonal_movement import DiagonalMovement
# from pathfinding.core.grid import Grid
# from pathfinding.finder.a_star import AStarFinder


coords = []
axcrds = []


def get_points():
    global coords
    global axcrds
    root = Tk()

    # setting up a tkinter canvas with scrollbars
    frame = Frame(root, bd=2, relief=SUNKEN)
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    xscroll = Scrollbar(frame, orient=HORIZONTAL)
    xscroll.grid(row=1, column=0, sticky=E + W)
    yscroll = Scrollbar(frame)
    yscroll.grid(row=0, column=1, sticky=N + S)
    canvas = Canvas(frame, bd=0, xscrollcommand=xscroll.set, yscrollcommand=yscroll.set)
    canvas.grid(row=0, column=0, sticky=N + S + E + W)
    xscroll.config(command=canvas.xview)
    yscroll.config(command=canvas.yview)
    frame.pack(fill=BOTH, expand=1)
    root.attributes('-zoomed', True)

    # adding the image
    # File = askopenfilename(parent=root, initialdir="/home/u0133458/Documents/un_docs", title='Select File')
    imgfile = "/home/u0133458/Documents/un_docs/ant-berlman_cropped.png"
    # img = ImageTk.PhotoImage(Image.open(File).convert("L").filter(ImageFilter.FIND_EDGES).resize((1800, 1000)))
    # img1 = Image.open(imgfile).convert("L").filter(ImageFilter.SMOOTH_MORE) \
    #     .filter(ImageFilter.EDGE_ENHANCE_MORE).filter(ImageFilter.DETAIL).resize((1800, 1000))
    img1 = Image.open(imgfile).convert("L").resize((1800,1000))
    img1 = ImageEnhance.Sharpness(img1).enhance(0.1)
    img1 = ImageEnhance.Contrast(img1).enhance(10)
    img = ImageTk.PhotoImage(img1)
    canvas.create_image(0, 0, image=img, anchor="nw")
    canvas.config(scrollregion=canvas.bbox(ALL))

    # function to be called when mouse is clicked
    def printcoords(event):
        def sup(x, y, a=1):
            cm = []
            b_flag = 0
            for k in range(30000):
                if pixs[x + 1, y] != 255:
                    x += 1
                elif pixs[x, y + a] != 255 and [x, y + a] not in cm:
                    y += a
                elif pixs[x, y - a] != 255 and [x, y - a] not in cm:
                    y -= a
                else:
                    if b_flag == 2:
                        break
                    b_flag += 1
                    y += a
                    continue
                cm.append([x, y])
                canvas.create_rectangle(x, y, x + 1, y + 1, fill='red', outline='red')
                print("auto", x, y)
            return cm

        # outputting x and y coords to console
        x1, y1 = event.x, event.y
        pixs = img1.load()
        # temptemp = np.asarray(img1)  # for use with pthfinding :p
        if pixs[x1, y1] != 255:
            print(x1, y1)
            coords.append([x1, y1])
            # checking quadrants
            totc, totd = 0, 0
            for i in range(3):
                for j in range(15):
                    if pixs[x1 + i, y1 - j] != 255:
                        totc += 1
                    if pixs[x1 + i, y1 + j] != 255:
                        totd += 1
            # find the nearest non-black pixel to the right
            print(totc, totd)
            if totc < totd:
                cords = sup(x1, y1)
            else:
                cords = sup(x1, y1, a=-1)
            [coords.append([i[0], i[1]]) for i in cords]

    def delcoord(event):
        global coords
        xf, yf = coords[-1][0], coords[-1][1]
        img1.putpixel((xf, yf), 1)
        canvas.create_rectangle(xf, yf, xf + 1, yf + 1, fill='white', outline='white')
        coords = coords[:-1]
        print('removed %f %f' % (xf, yf))

    def getc(event):
        print(img1.load()[event.x, event.y])

    def toblack(event):
        canvas.create_rectangle(event.x, event.y, event.x + 1, event.y + 1, fill='black', outline='black')
        img1.putpixel((event.x, event.y), 0)

    def towhite(event):
        canvas.create_rectangle(event.x, event.y, event.x + 1, event.y + 1, fill='white', outline='white')
        img1.putpixel((event.x, event.y), 255)

    def getax(event):
        axcrds.append([event.x, event.y])
        print('xy:', len(axcrds), event.x, event.y)

    def delax(event):
        global axcrds
        axcrds = []
        print('axes resetted!')

    # mouseclick event
    canvas.bind("<ButtonRelease-1>", printcoords)
    canvas.bind("<B2-Motion>", toblack)
    canvas.bind("<B3-Motion>", towhite)
    # canvas.bind("<ButtonPress Control-1>", lambda event: toblack(True))
    # canvas.bind("<ButtonRelease Control-1>", lambda event: toblack(False))
    root.bind("c", getc)
    root.bind("a", getax)
    root.bind("A", delax)
    root.bind("x", delcoord)

    root.mainloop()
    return coords, axcrds


def main():
    ab_coords, ax = get_points()
    ymin = float(input('ymin'))
    ymax = float(input('ymax'))
    xmin = float(input('xmin'))
    xmax = float(input('xmax'))
    cy = (ymax - ymin) / (ax[1][1] - ax[0][1])
    dy = (ymin - ax[0][1] * cy)
    cx = (xmax - xmin) / (ax[3][0] - ax[2][0])
    dx = (xmin - ax[2][0] * cx)
    x_coords = np.asarray([i * cx + dx for i in [ab_coords[j][0] for j in range(len(ab_coords))]], dtype=np.float32)
    y_coords = np.asarray([i * cy + dy for i in [ab_coords[j][1] for j in range(len(ab_coords))]], dtype=np.float32)
    print(x_coords)
    print(y_coords)
    npc = np.vstack((x_coords, y_coords))
    npc.transpose()
    np.savetxt('/home/u0133458/Desktop/array.txt', npc, fmt='%10.5f')


def check_graph():
    mat = np.genfromtxt('/home/u0133458/Desktop/array.txt')
    plt.plot(*mat)
    plt.show()


if __name__ == "__main__":
    # main()
    check_graph()
