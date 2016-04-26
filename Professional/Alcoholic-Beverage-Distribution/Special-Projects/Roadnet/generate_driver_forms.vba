Option Explicit

Sub generate_driver_forms()
        Dim i               As Long
        Dim last_row        As Long
        Dim last_col        As Long
        Dim row             As Range
        Dim file_name       As String
        
        ' Variables to move
        Dim CustID As String
        Dim CustName As String
        Dim CustAddr As String
        Dim CustCity As String
        Dim CustZip As String
        Dim CustDays As String
        Dim CustRoute As String
        Dim CustStop As String
        Dim CustIsOP As String
        
                
        Application.ScreenUpdating = False
        Application.EnableEvents = False
    
        last_row = Cells(Rows.Count, "A").End(xlUp).row + 1
        last_col = Cells(1, Columns.Count).End(xlToLeft).Column
        
    
        For i = 2 To last_row
            CustID = Sheets("Locations").Cells(i, 1)
            CustName = Sheets("Locations").Cells(i, 2)
            CustAddr = Sheets("Locations").Cells(i, 3)
            CustCity = Sheets("Locations").Cells(i, 4)
            CustZip = Sheets("Locations").Cells(i, 6)
            CustDays = Sheets("Locations").Cells(i, 11)
            CustRoute = Sheets("Locations").Cells(i, 10)
            CustStop = Sheets("Locations").Cells(i, 39)
            CustIsOP = Sheets("Locations").Cells(i, 37)
        
            'Write out the second sheet using the variables
        
            Sheets("Driver Form").Cells(2, 1) = CustID
            Sheets("Driver Form").Cells(2, 2) = CustName
            Sheets("Driver Form").Cells(4, 1) = CustAddr
            Sheets("Driver Form").Cells(4, 2) = CustCity
            Sheets("Driver Form").Cells(6, 1) = CustZip
            Sheets("Driver Form").Cells(6, 2) = CustDays
            Sheets("Driver Form").Cells(8, 1) = CustRoute
            Sheets("Driver Form").Cells(8, 2) = CustStop
            Sheets("Driver Form").Cells(10, 1) = CustIsOP
    
            file_name = CustRoute & CustStop & CustName & ".pdf"
            
            ActiveWorkbook.ActiveSheet.ExportAsFixedFormat Type:=xlTypePDF, _
            Filename:="C:\Users\pmwash\Desktop\R_files\Data Output\" & file_name, _
            OpenAfterPublish:=False
    
    
        Next i
    
    
    
End Sub




