from docx import Document
from docx.shared import Inches
document = Document()
document.add_heading('Document Title', 0)
p = document.add_paragraph('A plain paragraph having some ')
p.add_run('bold').bold = True
p.add_run(' and some ')
p.add_run('italic.').italic = True
document.add_heading('Heading, level 1',level=1)
document.add_paragraph('Intense quote',style='Intense Quote')
document.add_paragraph('first item in unordered list',style='List Bullet')
document.add_paragraph('first item in ordered list', style='List Number')
records = ((3, '101', 'Spam'),(7, '422', 'Eggs'), (4, '631', 'Spam, spam, eggs, and rice'))
document.save('test.docx')