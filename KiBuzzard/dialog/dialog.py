"""Subclass of dialog_base, which is generated by wxFormBuilder."""
import os
import re
import copy

import wx

from . import dialog_text_base

class Dialog(dialog_text_base.DIALOG_TEXT_BASE):
    def __init__(self, parent, config, buzzard, func):
        dialog_text_base.DIALOG_TEXT_BASE.__init__(self, parent)
        
        typeface_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'buzzard', 'typeface')
        for entry in os.listdir(typeface_path):
            entry_path = os.path.join(typeface_path, entry)
            
            if not entry_path.endswith('.ttf'):
                continue
            
            self.m_FontComboBox.Append(os.path.splitext(entry)[0])
        
        self.m_FontComboBox.SetSelection(0)


        self.m_SizeYUnits.SetLabel("mm")
        self.m_ThicknessUnits.SetLabel("mm")

        best_size = self.BestSize
        # hack for some gtk themes that incorrectly calculate best size
        best_size.IncBy(dx=0, dy=30)
        self.SetClientSize(best_size)
        self.config = config
        self.func = func
        
        self.loadConfig()


        self.buzzard = buzzard
        self.sourceText = ""
        self.polys = []
        
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self.Bind(wx.EVT_TIMER, self.labelEditOnText)
        self.m_sdbSizerCancel.Bind(wx.EVT_BUTTON, self.Cancel)

        self.timer = wx.Timer(self, 0)
        self.timer.Start(milliseconds=250, oneShot=True)

    def Cancel(self, e):
        self.timer.Stop()

        self.saveConfig()
        e.Skip()


    def loadConfig(self):
        try:
            self.config.SetPath('/')
            self.m_FontComboBox.SetStringSelection(self.config.Read('font', 'FredokaOne'))
            self.m_MultiLineText.SetValue(self.config.Read('text', ''))
            self.m_SizeYCtrl.SetValue(str(self.config.ReadFloat('scale', 1.0)))
            self.m_JustifyChoice1.SetStringSelection(self.config.Read('l-cap', ''))
            self.m_JustifyChoice.SetStringSelection(self.config.Read('r-cap', ''))
        except:
            import traceback
            wx.LogError(traceback.format_exc())
        
    def saveConfig(self):
        try:
            self.config.SetPath('/')
            self.config.Write('font', self.m_FontComboBox.GetStringSelection())
            self.config.Write('text', self.m_MultiLineText.GetValue())
            self.config.WriteFloat('scale', float(self.m_SizeYCtrl.GetValue()))
            self.config.Write('l-cap', self.m_JustifyChoice1.GetStringSelection())
            self.config.Write('r-cap', self.m_JustifyChoice.GetStringSelection())
        except:
            import traceback
            wx.LogError(traceback.format_exc())
            

    def CurrentSettings(self):
        return str(self.m_MultiLineText.GetValue()) + str(self.m_SizeYCtrl.GetValue()) + str(self.m_FontComboBox.GetStringSelection()) + \
            self.m_JustifyChoice1.GetStringSelection() + self.m_JustifyChoice.GetStringSelection()

    def labelEditOnText( self, event ):

        while self.sourceText != self.CurrentSettings():
            self.sourceText = self.CurrentSettings()
            self.ReGeneratePreview()

        self.timer.Start(milliseconds=250, oneShot=True)
        event.Skip()

    def ReGenerateFlag(self, e):
        self.sourceText = ""

    def ReGeneratePreview(self, e=None):
        self.polys = []
        self.buzzard.fontName = self.m_FontComboBox.GetStringSelection()

        # Validate scale factor
        scale = 0.04
        if self.m_SizeYCtrl.GetValue() != "":
            try:
                scale = float(self.m_SizeYCtrl.GetValue()) * 0.04
            except ValueError:
                print("Scale not valid")
        self.buzzard.scaleFactor = scale
        

        styles = {'':'', '(':'round', '[':'square', '<':'pointer', '/':'fslash', '\\':'bslash', '>':'flagtail'}
        self.buzzard.leftCap = styles[self.m_JustifyChoice1.GetStringSelection()]

        styles = {'':'', ')':'round', ']':'square', '>':'pointer', '/':'fslash', '\\':'bslash', '<':'flagtail'}
        self.buzzard.rightCap = styles[self.m_JustifyChoice.GetStringSelection()]


        try:

            self.polys = self.buzzard.generate(self.m_MultiLineText.GetValue())
        except Exception as e:
            import traceback
            wx.LogError(traceback.format_exc())

        self.RePaint()

    def RePaint(self, e=None):
        self.Layout()
        self.Refresh()
        self.Update()


    def OnPaint(self, e):

        dc = wx.PaintDC(self)
        dc.SetPen(wx.Pen('#000000', width=1))

        size_x, size_y = self.m_PreviewPanel.GetSize()
        position_x, position_y = self.m_PreviewPanel.GetPosition()

        dc.SetDeviceOrigin(int(position_x + size_x/2), int((position_y + size_y/2)))
        dc.SetBrush(wx.Brush('#000000'))

        if len(self.polys):
            # Create copy of poly list for scaling preview
            polys = copy.deepcopy(self.polys)

            min_x = 0
            max_x = 0

            for i in range(len(self.polys)):
                for j in range(len(self.polys[i])):
                    min_x = min(self.polys[i][j][0], min_x)
                    max_x = max(self.polys[i][j][0], max_x)

            scale = (size_x * 0.95) / (max_x - min_x)

            scale = min(50.0, scale)
            for i in range(len(polys)):
                for j in range(len(polys[i])):
                    polys[i][j] = (scale*polys[i][j][0],scale*polys[i][j][1])



            dc.DrawPolygonList(polys)
        
    def OnOkClick(self, event):
        self.timer.Stop()

        self.saveConfig()
        self.func(self, self.buzzard)