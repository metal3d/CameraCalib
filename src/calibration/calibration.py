#!/bin/env python
#-*- coding: utf-8 -*-

#Author: Patrice FERLET <metal3d@gmail.com>
#License: BSD

import sys
import cv
from PyQt4 import QtCore, QtGui

class Calibration:
    """Compute ChessBoard to calculate calibration
    """

    #static var that keep the number of points to compute
    NUMPOINT=40

    def __init__(self):
        self.prepare()

    def prepare(self):
        """Initialize vars
        """
        self.filename = None
        self.chessSize = (9,6)
        self.nframe = 0
        self.points = []
        self.framesize = ()

    def setFile(self, filename):
        """Keep filename to process and initialize class vars
        """
        self.prepare() #new call on each new file to process
        self.filename = "%s"  % filename

    def process(self, gui):
        """Process file, find corners on chessboard and keep points
        """
        gui.setMessage("Analyzing movie... get frame count")
        
        #open capture file
        capture = cv.CaptureFromFile(self.filename)
        frame = cv.QueryFrame(capture)
        
        #count... I know it sucks
        numframes=1
        while frame:
            frame = cv.QueryFrame(capture)
            numframes +=1

        step = int(numframes/Calibration.NUMPOINT)
        capture = cv.CaptureFromFile(self.filename)
        frame = cv.QueryFrame(capture) #grab a frame to get some information
        self.framesize = (frame.width, frame.height)
        gray = cv.CreateImage((frame.width,frame.height), 8, 1)

        points = []
        nframe = 0
        f=0
        cv.NamedWindow("ChessBoard",cv.CV_WINDOW_NORMAL)

        gui.setMessage("Analyzing movie... find chessCorner for %d frames" % Calibration.NUMPOINT)

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

            #skip frames to get only NUMPOINT of point to calculate
            while f%step != 0 and frame:
                f+=1
                frame = cv.QueryFrame(capture)

        self.points = points
        self.nframe = nframe

        gui.setMessage("Analyze end, %d points found" % len(self.points))

    def calcIntrasec(self, gui):
        """Calculate focal and distortion from computed points
        """
        count = len(self.points)
        numpoints = (self.chessSize[0]*self.chessSize[1])

        #create matrices that are needed to compute calibration
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

        #this compute points in row and cols...
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

        #and now, calibrate...
        cv.CalibrateCamera2(p3d, p2d, pointCounts, self.framesize, mat, distCoeffs, rvecs, tvecs, flags=0)
        gui.setMessage("Intrasinc camera parameters checked")

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
        self.fxlabel = QtGui.QLabel('focal x')
        self.fylabel = QtGui.QLabel('focal y')
        self.dist1label = QtGui.QLabel('K1')
        self.dist2label = QtGui.QLabel('K2')
        self.dist3label = QtGui.QLabel('P1')
        self.dist4label = QtGui.QLabel('P2')

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
        a(self.dist2label, 5,0)
        a(self.dist3label, 6,0)
        a(self.dist4label, 7,0)

        self.setLayout(self.grid)


        #connect signals to methods
        self.connect(browseButton, QtCore.SIGNAL('clicked()'), self.onOpenFileClicked)
        self.connect(analyzeButton, QtCore.SIGNAL('clicked()'), self.startAnalyze)

    def onOpenFileClicked(self):
        """Open the file selector and get selected movie
        """
        fname = QtGui.QFileDialog.getOpenFileName(self, "Open File")
        self.calibration.setFile(fname)
        self.filelabel.setText(fname)

    def startAnalyze(self):
        """Call analyze on Calibration object then set results on GUI
        """
        c = self.calibration
        c.process(self)
        (cam, dist) = c.calcIntrasec(self)

        self.fxlabel.setText("Focal x: " + str(cam[0,0]))
        self.fylabel.setText("Focal y: " + str(cam[1,1]))
        self.dist1label.setText("K1: " + str(dist[0,0]))
        self.dist2label.setText("K2: " + str(dist[1,0]))
        self.dist3label.setText("P1: " + str(dist[2,0]))
        self.dist4label.setText("P2: " + str(dist[3,0]))

    def setMessage(self, message):
        """Simply to display messages on GUI
        """
        self.message = str(message)
        self.app.processEvents()
        QtCore.QTimer(self).singleShot(5,self._messageDelayed)
        self.app.processEvents()

    def _messageDelayed(self):
        self.messageLabel.setText(self.message)
        self.app.processEvents()
        

if __name__ == "__main__":   
    app = QtGui.QApplication(sys.argv)
    calib = GUI()
    calib.app = app
    calib.show()
    sys.exit(app.exec_())
