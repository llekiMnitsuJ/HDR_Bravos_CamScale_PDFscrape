# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 17:54:04 2023

@author: Justin Mikell, justin.mikell@gmail.com; mikell@wustl.edu 

This file may be useful for going through a directory containing pdfs generated by 
the Bravos Afterloader during daily QA (camscale position verification test) or
position calibration tests. 

Will return a pandas dataframe containing several pieces of information including 
dummy and source position measurement deviations during verification, pre-calibration, and post-calibration.

This allows one to then plot trends of the data, while keeping an eye on calibration events. 
Does assume access to the pdfs and you save them. 

The current implementation is hardcoded to the current pdf structure, but does some simple checks. 


    Camscale daily results are saved in a filename format: e.g. "PVT*.pdf"
    I copy the pdfs to a local directory. 


    Example usage:
        #set directory
        myDir = r'your/directory/topdfs'
        #find PVT*.pdf
        df = Generate_dataframe_for_CamScale_analysis(myDir)
        df.to_excel("camscale.xlsx")
        

"""

import openpyxl
import os
import re
import glob
import pandas as pd
import numpy as np
import datetime

import pdftotext


def convertPDFtoText(filename, verbose=0):
    """

    Parameters
    ----------
    filename : string
        

    Returns
    -------
    pdftotext object
    
    EXAMPLE USAGE:
        file = r'H:/src/Bravos_camscale/PVT-2023-10-23-06-23-15.PDF'
        pdf = convertPDFtoText(file)
        print(pdf[0])
        
    """
    if(verbose>0):
        print(filename)
    
    with open(filename, "rb") as f:
        pdf = pdftotext.PDF(f)
    
    return(pdf)


def verification_or_calibration(s, verbose=0):
    
    vS = 'BRAVOS : Position Verification Report'
    cS = 'BRAVOS : Position Calibration Report'
    
    if(verbose > 0):
        print(s)
    
    verification = False;
    calibration = False;
    if(s.strip() == vS):
        verification = True
    if(s.strip() == cS):
        calibration = True
        
    myMap = {}
    myMap["verification"]=verification
    myMap["calibration"]=calibration        
    if(verbose > 0):
        print(myMap)
    return(myMap)
    
def user_room_datetime(s, verbose=0):
    if(verbose > 0):
        print(s)
    q = s.strip().split("/")
    myMap={}
    myMap["User"] = q[0].strip()
    myMap["Room"] = q[1].strip()
    myMap["SerialNumber"] = q[2].strip()
    myMap["datetime"] = q[3].strip()
    
    if(verbose > 0):
        print(myMap)
    return(myMap)
    
def parse_channel_number(s, verbose=0):
    if(verbose > 0):
        print(s)
    q = s.strip()
    myMap = {}
    myMap["Channel"] = int(q.split()[-1])
    assert(q.split()[-2].strip() == "Channel")
    return(myMap)

def parse_camscaleSN(s, verbose=0):
    if(verbose > 0):
        print(s)
    q = s.strip()
    myMap = {}
    myMap["CamScaleSN"] = q.split()[-1].strip()
    assert(q.split()[-2].strip() == "SN")
    assert(q.split()[-3].strip() == "CamScale")
    return(myMap)

def parse_dummyCableLine(s, verbose=0):
    if(verbose >0):
        print(s)
    q = s.strip().split()
    assert(q[0] == 'Dummy')
    assert(q[1] == 'Cable')
    assert(len(q) == 6)
    
    myMap={}
    myMap["DummySN"] = q[2].strip()
    myMap["DummyDriveCycles"] = q[3].strip()
    myMap["DummyWheelCycles"] = q[4].strip()
    myMap["DummyCableCycles"] = q[5].strip()
    
    if(verbose > 0):
        print(myMap)
    return(myMap)
    
def parse_sourceCableLine(s, verbose=0):
    if(verbose >0):
        print(s)
    q = s.strip().split()
    assert(q[0] == 'Source')
    assert(q[1] == 'Cable')
    assert(len(q) == 6)
    
    myMap={}
    myMap["SourceSN"] = q[2].strip()
    myMap["SourceDriveCycles"] = q[3].strip()
    myMap["SourceWheelCycles"] = q[4].strip()
    myMap["SourceCableCycles"] = q[5].strip()
    
    if(verbose > 0):
        print(myMap)
    return(myMap)

def parse_measuredDeviationFromTargetPositions(s, verbose=0):
    if(verbose >0):
        print(s)
    q = s.strip().split()
    assert(q[0] == 'Measured')
    
    assert(len(q) == 7)
    
    myMap={}
    myMap["DummyDeviationAt90cm_cm"] = float(q[1].strip())
    myMap["DummyDeviationAt120cm_cm"] = float(q[2].strip())
    myMap["DummyDeviationAt150cm_cm"] = float(q[3].strip())
    myMap["SourceDeviationAt90cm_cm"] = float(q[4].strip())
    myMap["SourceDeviationAt120cm_cm"] = float(q[5].strip())
    myMap["SourceDeviationAt150cm_cm"] = float(q[6].strip())
    myMap["MeasureType"] = "Verification"
    
    
    if(verbose > 0):
        print(myMap)
    return(myMap)


def parse_PreCalibrationDeviationFromTargetPositions(s, verbose=0):
    if(verbose >0):
        print(s)
    q = s.strip().split()
    assert(q[0] == 'Pre-Calibration')
    assert(len(q) == 7)
    
    myMap ={}
    myMap = parse_measuredDeviationFromTargetPositions("Measured "+" ".join(q[1:]))
    myMap["MeasureType"]="PreCalibration"

    
    if(verbose > 0):
        print(myMap)
    return(myMap)

def parse_PostCalibrationDeviationFromTargetPositions(s, verbose=0):
    if(verbose >0):
        print(s)
    q = s.strip().split()
    assert(q[0] == 'Post-Calibration')
    assert(len(q) == 7)
    
    myMap ={}
    myMap = parse_measuredDeviationFromTargetPositions("Measured "+" ".join(q[1:]))
    myMap["MeasureType"]="PostCalibration"

    
    if(verbose > 0):
        print(myMap)
    return(myMap)

def parse_ConsoleVersion(sArr, verbose=0):

    q = sArr[-2].strip().split()
    if(verbose >0):
        print(q)
        
    assert(q[0] == 'Console')
    assert(q[1] == 'Version')
    assert(len(q) == 4)
    
    myMap ={}
    myMap["ConsoleVersion"]=" ".join(q[2:])

    if(verbose > 0):
        print(myMap)
    return(myMap)

def parse_header_PVT(sArr, verbose=0):
    myMap = verification_or_calibration(sArr[0], verbose=verbose)
    myMap = myMap | user_room_datetime(sArr[1], verbose=verbose)
    return(myMap)

def parse_user_SN_cycles(sArr, verbose=0):
    myMap = parse_channel_number(sArr[5], verbose=verbose)
    myMap = myMap | parse_camscaleSN(sArr[6], verbose=verbose)
    myMap = myMap | parse_dummyCableLine(sArr[11], verbose=verbose)
    myMap = myMap | parse_sourceCableLine(sArr[12], verbose=verbose)
    return(myMap)



def parse_PVT_report(oPDF, verbose=0):
    """
    This is somewhat hardcoded and depends on the PDF structure. 
    If Varian changes the structure of the pdf in between versions then this may need 
    to be reworked or a more sophisticated method implemented. 
    
    """
    
    
    sArr = oPDF[0].strip().split("\r\n")
    
    myList = []
    myMap ={}
    myMap = parse_header_PVT(sArr, verbose=verbose)
    myMap = myMap | parse_user_SN_cycles(sArr, verbose=verbose)
    myMap = myMap | parse_ConsoleVersion(sArr, verbose=verbose)
    
    if ((myMap["verification"] == True) and (myMap["calibration"]==False)):
        myMap = myMap | parse_measuredDeviationFromTargetPositions(sArr[17], verbose)
        myList.append(myMap)
    if ((myMap["calibration"] == True) and (myMap["verification"]==False)):
        myMap = myMap | parse_PreCalibrationDeviationFromTargetPositions(sArr[17], verbose)
        myList.append(myMap)
        extraMap = parse_PostCalibrationDeviationFromTargetPositions(sArr[18], verbose)
        myList.append(myMap|extraMap)
    

    
    return(myList)


def process_calibration_intervals(df, verbose=0):
    """
    
    

    Parameters
    ----------
    df : pandas dataframe
        Output from Generate_dataframe_for_CamScale_analysis
    verbose : TYPE, optional
        DESCRIPTION. The default is 0.

    Returns
    -------
    a dataframe with an additional column labeled calibration reference. 
    All position verification tests will then be associated with the last
    calibration datetime. 

    """
    calEvents = df.MeasureType == 'PostCalibration'
    cal_list = df[calEvents].datetime.to_list()
    cal_list.sort()
    assert len(cal_list) >= 1, "no calibration events found!"
    
    #put in bounds on datetime
    lowerBoundDate = '1900-01-01 00:00:00'
    upperBoundDate = '3000-12-31 23:59:59'
    cal_list.insert(0,lowerBoundDate)
    cal_list.append(upperBoundDate)
    
    df = df.assign(currentCalDateTime = cal_list[0])
    for i in np.arange(1,(len(cal_list)-1)):
        startdate = cal_list[i]
        enddate = cal_list[i+1]
        index = (df.datetime > startdate)*(df.datetime <= enddate)
        if(np.sum(index) > 0):
            df.currentCalDateTime[index] = startdate
        
    #now set the postcalibration currentCalDateTime to themselves.
    for i in cal_list:
        index = (df.MeasureType == 'PostCalibration')*(df.currentCalDateTime == i)
        df.currentCalDateTime[index] = df.datetime[index]
    
    
    #now add a column showing the difference in time between current measurement and calibration date
    df['days_from_cal'] = pd.to_datetime(df['datetime']) - pd.to_datetime(df['currentCalDateTime'])
    df['days_from_cal'] = df['days_from_cal'].dt.total_seconds()/(60.*60.*24.)
    
    return(df)
    
    


def Generate_dataframe_for_CamScale_analysis(directory, verbose=0):
    """Example usage:
        myDir = r'H:/src/Bravos_camscale'
        df = Generate_dataframe_for_CamScale_analysis(directory)
        df.to_excel("camscale.xlsx")
        
        
    """
    
    #myDir = r'H:/src/Bravos_camscale'
    myDir = os.path.normpath(directory)
    fileList = glob.glob("{0}\\PVT*.pdf".format(myDir))
    myList = []
    for i in fileList:
        pdf = convertPDFtoText(i, verbose=verbose)
        m = parse_PVT_report(pdf, verbose)
        myList.extend(m)
    
    df = pd.DataFrame(myList)
    #just in case the dataframe was not chronological
    df = df.sort_values(by='datetime', ascending=True)
    
    df = process_calibration_intervals(df)
    return(df)
    


