#!/bin/env python
#-*- coding: utf-8 -*-

import sys
from PyQt4 import QtCore, QtGui

import cv, numpy, Image


NUMPOINT=15

class Calibration:
    def __init__(self):
        self.filename = None
        self.chessSize = (9,6)
        self.nframe = 0
        self.points = []
        self.framesize = ()

    def setFile(self, filename):
        self.filename = "%s"  % filename

    def process(self, gui):
        
        #open capture file
        capture = cv.CaptureFromFile(self.filename)

        #count... I know it sucks
        gui.messageLabel.setText("Analyzing movie... get frame count")
        frame = cv.QueryFrame(capture)
        numframes=1
        while frame:
            frame = cv.QueryFrame(capture)
            numframes +=1

        step = int(numframes/NUMPOINT)
        print "will take each %d on %d frales" % (step, numframes)
        capture = cv.CaptureFromFile(self.filename)
        frame = cv.QueryFrame(capture) #grab a frame to get some information
        self.framesize = (frame.width, frame.height)
        gray = cv.CreateImage((frame.width,frame.height), 8, 1)

        points = []
        nframe = 0
        f=0
        cv.NamedWindow("ChessBoard",cv.CV_WINDOW_NORMAL)

        gui.messageLabel.setText("Analyzing movie... find chessCorner for %d frames" % NUMPOINT)

        while frame:
            f+=1    
            #find corners
            state,found = cv.FindChessboardCorners(frame, self.chessSize, flags=cv.CV_CALIB_CB_FILTER_QUADS)
            if state==1:
                #affine search
                cv.CvtColor( frame, gray, cv.CV_BGR2GRAY )
                found = cv.FindCornerSubPix(gray, found, (11,11), (-1,-1), (cv.CV_TERMCRIT_ITER | cv.CV_TERMCRIT_EPS, 30, 0.1))

                #draw corners on image
                cv.DrawChessboardCorners(frame, self.chessSize, found, state)
                #compute points 
                for x,y in found:
                    points.append((x,y))
                nframe+=1

            cv.ResizeWindow("ChessBoard",640,480)
            cv.ShowImage("ChessBoard",frame)

            cv.WaitKey(4)
            frame = cv.QueryFrame(capture) #grab a frame to get some information
            while f%step != 0 and frame:
                f+=1
                frame = cv.QueryFrame(capture)

        self.points = points
        self.nframe = nframe

        gui.messageLabel.setText("Analyze end, %d points found" % len(self.points))

    def calcIntrasec(self, gui):
        count = len(self.points)
        numpoints = (self.chessSize[0]*self.chessSize[1])

        mat = cv.CreateMat(3,3,cv.CV_32FC1)
        distCoeffs = cv.CreateMat(4,1,cv.CV_32FC1)
        p3d = cv.CreateMat(count,3,cv.CV_32FC1) #compute 3D points
        p2d = cv.CreateMat(count,2,cv.CV_32FC1) #compute 2D points
        pointCounts = cv.CreateMat( self.nframe ,1,cv.CV_32SC1) #give numpoints per images
        cv.Set(pointCounts,numpoints)
        rvecs = cv.CreateMat(self.nframe,3,cv.CV_32FC1)
        tvecs = cv.CreateMat(self.nframe,3,cv.CV_32FC1)

        i = 0
        row = 0
        col = 0
        cv.Set(p3d,0.0) #to set every values to 0.0... and not set Z value

        for p in self.points:
            p2d[i,0] = p[0]
            p2d[i,1] = p[1]
            
            p3d[i,0] = col
            p3d[i,1] = row
            col+=1
            if col >= self.chessSize[0]: 
                row+=1
                col=0
                if row >= self.chessSize[1]:
                    row = 0
            i+=1

        cv.CalibrateCamera2(p3d, p2d, pointCounts, self.framesize, mat, distCoeffs, rvecs, tvecs, flags=0)
        gui.messageLabel.setText("Intrasinc camera parameters checked")
        return (mat, distCoeffs)


class GUI(QtGui.QWidget):
    def __init__(self):
        """Constructor"""
        super(GUI,self).__init__()
        self.setWindowTitle("Calibration Tool")
        self.setUI()

        #instanciate Calibration class
        self.calibration = Calibration()


    def setUI(self):
        """Init UI of calibration tool"""
        
        l = QtGui.QLabel("Open file:")
        browseButton = QtGui.QPushButton("Browse")
        analyzeButton = QtGui.QPushButton("Analyse")
        self.filelabel = QtGui.QLabel("")
        self.messageLabel = QtGui.QLabel("")
 
        #camera intrasec values
        self.fxlabel = QtGui.QLabel('fx')
        self.fylabel = QtGui.QLabel('fy')
        self.dist1label = QtGui.QLabel('d1')
        self.dist2label = QtGui.QLabel('d2')
        self.dist3label = QtGui.QLabel('d3')
        self.dist4label = QtGui.QLabel('d4')

        #set layout
        self.grid = QtGui.QGridLayout()
        a = self.grid.addWidget
        a(l, 0,0)
        a(browseButton, 0,2)
        a(self.filelabel,0,1)
        a(self.messageLabel, 1,0,1,4)
        a(analyzeButton, 2,0,1,4)

        a(self.fxlabel, 3,0)
        a(self.fylabel, 3,1)
        a(self.dist1label, 4,0)
        a(self.dist2label, 4,1)
        a(self.dist3label, 4,2)
        a(self.dist4label, 4,3)

        self.setLayout(self.grid)


        #connect signals to methods
        self.connect(browseButton, QtCore.SIGNAL('clicked()'), self.onOpenFileClicked)
        self.connect(analyzeButton, QtCore.SIGNAL('clicked()'), self.startAnalyze)

    def onOpenFileClicked(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, "Open File")
        self.calibration.setFile(fname)
        self.filelabel.setText(fname)

    def startAnalyze(self):
        c = self.calibration
        c.process(self)
        (cam, dist) = c.calcIntrasec(self)

        self.fxlabel.setText("fx:" + str(cam[0,0]))
        self.fylabel.setText("fy:" + str(cam[1,1]))
        self.dist1label.setText(str(dist[0,0]))
        self.dist2label.setText(str(dist[0,1]))
        self.dist3label.setText(str(dist[0,2]))
        self.dist4label.setText(str(dist[0,3]))

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    calib = GUI()
    calib.show()
    sys.exit(app.exec_())
