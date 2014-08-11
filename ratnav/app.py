#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# RatNav
# ======================================
# Copyright (C) 2014 RatNav Contributors
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import time
import pygame

import cv2.cv as cv
import numpy as np

try:
    import picamera
    import io

    PICAM = True
except ImportError:
    PICAM = False


# Audio files
MOVE = './audio/move.wav'  # A call to drive
MOVING = './audio/moving.wav'  # When we're really driving again
STANDING = './audio/standing.wav'  # When we had to stop (this one might annoy)


def log(*what):
    """Simple unfancy logging"""

    msg = ""
    for item in what:
        msg += str(item)

    print(msg)


class RatNavApp():
    """
    The RatNav Application object

    Just instantiate and run, e.g. like this:
    > RatNav = RatNavApp(do_audio=False, show_windows=False)
    > RatNav.run()

    This would give you a ratnav without display and audio output.
    Which is still useful for debugging purposes, sometimes.

    RatNav will observe your first installed camera for movement
    changes. If it detects that the camera is standing still (no
    detectable movement happens), it switches into waiting mode
    and observes only the center of your viewport.
    If it detects a movement here while waiting, it will alert
    you to this change.
    Once it detects that you're driving again, it will play a
    cheering alert and wait until movement stops, which will
    be alerted, too.
    """

    def on_threshold_change(self, val):
        """Called when threshold slider is changed"""

        self.threshold = val

    def capture_frame(self):

        if PICAM:
            with picamera.PiCamera() as camera:
                camera.capture('snapshot.jpg')
                image = cv.LoadImage('snapshot.jpg')
        else:
            image = cv.QueryFrame(self.capture)  # Take a frame to init recorder

        return image


    def __init__(self, threshold=25, show_windows=True, do_audio=True):
        """Set up cv buffers, audiofiles and states"""

        self.font = None
        self.mode = 'contours'
        self.show = show_windows  # Either or not show the 2 windows
        self.frame = None

        if PICAM:
            log("Using RPi camera")
            #self.capture = picamera.PiCamera()
            #self.capture.start_preview()
            #self.stream = io.BytesIO()
        else:
            log("Using normal cv camera")
            self.capture = cv.CaptureFromCAM(0)
        log("Camera opened")
        self.frame = self.capture_frame()  # Take a frame to init buffer sizes
        log("First frame taken: ", type(self.frame), self.frame)

        self.gray_frame = cv.CreateImage(cv.GetSize(self.frame), cv.IPL_DEPTH_8U, 1)
        self.average_frame = cv.CreateImage(cv.GetSize(self.frame), cv.IPL_DEPTH_32F, 3)
        self.absdiff_frame = None
        self.previous_frame = None

        # Will hold the thresholded result
        self.res = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)

        self.frame1gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)  # Gray frame at t-1
        cv.CvtColor(self.frame, self.frame1gray, cv.CV_RGB2GRAY)

        self.frame2gray = cv.CreateMat(self.frame.height, self.frame.width, cv.CV_8U)  # Gray frame at t

        self.width = self.frame.width
        self.height = self.frame.height
        self.nb_pixels = self.width * self.height

        self.inner = (self.width / 4, self.height / 4, (self.width / 2), (self.height / 2))
        log("Input format: ", self.width, 'x', self.height)
        log("Scanning for car movement in: ", self.inner)

        self.surface = self.width * self.height
        self.currentsurface = 0
        self.currentcontours = None
        self.threshold = threshold
        #self.trigger_time = 0   # Hold timestamp of the last detection
        self.move_time = 0
        self.alert_time = 0

        self.standing = True
        self.moving = False

        self.do_audio = do_audio

        self.sounds = {}

        if do_audio:
            pygame.init()

            self.sounds[MOVING] = pygame.mixer.Sound(MOVING)
            self.sounds[MOVE] = pygame.mixer.Sound(MOVE)
            self.sounds[STANDING] = pygame.mixer.Sound(STANDING)

        if show_windows:
            cv.NamedWindow("Image")
            cv.CreateTrackbar("Detection treshold: ", "Image", self.threshold, 100, self.on_threshold_change)

    def run(self):
        """The actual main loop.
        * Queries a new camera picture
        * Processes the image
        * Checks for movement

        """

        started = time.time()

        while True:

            currentframe = self.capture_frame()
            instant = time.time()  # Get timestamp o the frame

            self.process_image(currentframe)  # Process the image

            if self.has_movement():
                if self.standing:  # we _we're_ standing
                    log("We detected a first movement.")
                    self.standing = False
                    self.move_time = instant
                if not self.moving and instant > self.move_time + 3:  # once we're sure, alert
                    log("We are moving.")
                    self.alert(MOVING)
                    self.moving = True

                    #if instant > started + 10:   # Wait 5 second after the webcam start for luminosity adjusting etc..
            else:
                if self.moving:  # seems like we're standing again
                    log("We stand still.")
                    self.alert(STANDING)
                    self.moving = False  # because we didn't see movement for at least a frame
                self.standing = True
                if self.has_movement_in_rect(self.currentcontours, self.inner):
                    log("We should move.")
                    self.alert(MOVE)

            if self.mode == 'contours':
                cv.DrawContours(currentframe, self.currentcontours, (0, 0, 255), (0, 255, 0), 1, 2, cv.CV_FILLED)

            if self.show:
                cv.ShowImage("Image", currentframe)

            c = cv.WaitKey(1) % 0x100
            if c == 27 or c == 10:  # Break if user enters 'Esc'.
                break

    def process_image(self, frame):
        """Decides which processing to use. No, not exactly a factory."""

        if self.mode == 'contours':
            self.process_for_contours(frame)
        else:
            self.process_for_threshold(frame)

    def process_for_contours(self, curframe):
        """Do cv contour processing."""

        cv.Smooth(curframe, curframe)  # Remove false positives

        if not self.absdiff_frame:  # For the first time put values in difference, temp and moving_average
            self.absdiff_frame = cv.CloneImage(curframe)
            self.previous_frame = cv.CloneImage(curframe)
            cv.Convert(curframe, self.average_frame)  # Should convert because after runningavg take 32F pictures
        else:
            cv.RunningAvg(curframe, self.average_frame, 0.05)  # Compute the average

        cv.Convert(self.average_frame, self.previous_frame)  # Convert back to 8U frame

        cv.AbsDiff(curframe, self.previous_frame, self.absdiff_frame)  # moving_average - curframe

        cv.CvtColor(self.absdiff_frame, self.gray_frame, cv.CV_RGB2GRAY)  # Convert to gray otherwise can't do threshold
        cv.Threshold(self.gray_frame, self.gray_frame, 50, 255, cv.CV_THRESH_BINARY)

        cv.Dilate(self.gray_frame, self.gray_frame, None, 15)  # to get object blobs
        cv.Erode(self.gray_frame, self.gray_frame, None, 10)

    def process_for_threshold(self, frame):
        """Do cv threshold processing."""

        cv.CvtColor(frame, self.frame2gray, cv.CV_RGB2GRAY)

        #Absdiff to get the difference between to the frames
        cv.AbsDiff(self.frame1gray, self.frame2gray, self.res)

        #Remove the noise and do the threshold
        cv.Smooth(self.res, self.res, cv.CV_BLUR, 5, 5)
        cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_OPEN)
        cv.MorphologyEx(self.res, self.res, None, None, cv.CV_MOP_CLOSE)
        cv.Threshold(self.res, self.res, 10, 255, cv.CV_THRESH_BINARY_INV)

    def has_movement_in_rect(self, contours, rect):
        """Checks for movement only in the given rectangle."""

        result = False

        for contour in contours:
            if type(contour) == tuple:
                crect = cv.BoundingRect([contour])
            else:
                crect = cv.BoundingRect(contour)
            cx, cy, cw, ch = crect
            x, y, w, h = rect
            if (cx > x) and (cx < x + w):
                if (cy > y) and (cy < y + h):
                    result = True

        return result

    def has_movement(self):
        """
        Tests for movement in the image.
        Currently also tests for movement in the inner rectangle.
        """

        result = False
        if self.mode == 'contours':
            #  Find contours

            storage = cv.CreateMemStorage(0)
            contours = cv.FindContours(self.gray_frame, storage, cv.CV_RETR_EXTERNAL, cv.CV_CHAIN_APPROX_SIMPLE)

            self.currentcontours = contours  # Save contours

            while contours:  # For all contours compute the area
                self.currentsurface += cv.ContourArea(contours)
                contours = contours.h_next()

            avg = (self.currentsurface * 100) / self.surface  # Calculate the average of contour area on the total size
            self.currentsurface = 0  # Put back the current surface to 0

            if avg > self.threshold:
                result = True
        else:
            nb = 0  # Will hold the number of black pixels

            for x in range(self.height):  # Iterate the hole image
                for y in range(self.width):
                    if self.res[x, y] == 0.0:  # If the pixel is black keep it
                        nb += 1
            avg = (nb * 100.0) / self.nb_pixels  # Calculate the average of black pixel in the image

            if avg > self.threshold:  # If over the ceiling trigger the alarm
                result = True

        return result

    def alert(self, soundname):
        """
        Should play the audio file upon traffic movement alert.
        """

        if self.alert_time + 5 < time.time():
            if self.do_audio:
                log("Playing audio '%s'" % soundname)
                self.sounds[soundname].play()

            self.alert_time = time.time()
        else:
            log("Not alerting.")
