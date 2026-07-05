#!/usr/bin/env python3
"""
Generate synthetic W-2 and 1040 PDFs with FAKE data for testing.
No real personal information. Used to validate the extraction pipeline.
"""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def make_w2(path="sample_w2.pdf"):
    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(72, 720, "Form W-2  Wage and Tax Statement  2024")
    c.setFont("Helvetica", 9)

    def lbl_val(x, y, label, value):
        c.setFont("Helvetica", 7)
        c.drawString(x, y, label)
        c.setFont("Helvetica", 10)
        c.drawString(x, y - 14, value)

    lbl_val(72, 690, "a Employee's social security number", "123-45-6789")
    lbl_val(320, 690, "b Employer identification number", "12-3456789")
    lbl_val(72, 655, "c Employer's name, address, and ZIP code",
            "Acme Robotics LLC")
    lbl_val(72, 615, "e Employee's first name and initial  Last name",
            "Jordan T Rivera")

    lbl_val(320, 655, "1 Wages, tips, other comp.", "84,500.00")
    lbl_val(470, 655, "2 Federal income tax withheld", "11,230.00")
    lbl_val(320, 615, "3 Social security wages", "88,000.00")
    lbl_val(470, 615, "4 Social security tax withheld", "5,456.00")
    lbl_val(320, 575, "5 Medicare wages and tips", "88,000.00")
    lbl_val(470, 575, "6 Medicare tax withheld", "1,276.00")
    lbl_val(320, 535, "7 Social security tips", "0.00")
    lbl_val(470, 535, "8 Allocated tips", "0.00")
    lbl_val(320, 495, "10 Dependent care benefits", "0.00")
    lbl_val(470, 495, "11 Nonqualified plans", "0.00")
    lbl_val(72, 495, "12a See instructions for box 12", "D 5,400.00")

    lbl_val(72, 455, "15 State  Employer's state ID", "CA  123-4567")
    lbl_val(320, 455, "16 State wages, tips, etc.", "84,500.00")
    lbl_val(470, 455, "17 State income tax", "4,980.00")
    lbl_val(320, 415, "18 Local wages, tips, etc.", "0.00")
    lbl_val(470, 415, "19 Local income tax", "0.00")
    lbl_val(72, 415, "20 Locality name", "")
    c.save()
    return path


def make_1040(path="sample_1040.pdf"):
    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(72, 730, "Form 1040  U.S. Individual Income Tax Return  2024")
    c.setFont("Helvetica", 9)

    def line(y, desc, value):
        c.setFont("Helvetica", 9)
        c.drawString(72, y, desc)
        c.setFont("Helvetica", 10)
        c.drawRightString(540, y, value)

    line(695, "1a Total amount from Form(s) W-2, box 1", "84,500.00")
    line(675, "2b Taxable interest", "320.00")
    line(655, "3b Ordinary dividends", "1,150.00")
    line(635, "7 Capital gain or (loss)", "2,000.00")
    line(615, "9 This is your total income. Add lines", "87,970.00")
    line(595, "10 Adjustments to income from Schedule 1", "1,500.00")
    line(575, "11 Adjusted gross income", "86,470.00")
    line(555, "12 Standard deduction or itemized deductions", "14,600.00")
    line(535, "15 This is your taxable income", "71,870.00")
    line(515, "16 Tax (see instructions)", "11,200.00")
    line(495, "24 This is your total tax", "11,200.00")
    line(475, "25 Federal income tax withheld", "11,230.00")
    line(455, "33 These are your total payments", "11,230.00")
    line(435, "34 This is the amount you overpaid", "30.00")
    line(415, "37 Amount you owe", "0.00")
    c.save()
    return path


if __name__ == "__main__":
    print("wrote", make_w2())
    print("wrote", make_1040())
