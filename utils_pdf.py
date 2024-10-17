import re
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "", 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

def sanitize_content(content):
    try:
        # Use 'utf-8' encoding to handle Unicode characters
        encoded_content = content.encode('utf-8', 'ignore').decode('utf-8')
        return encoded_content
    except UnicodeEncodeError as e:
        print(f"Encoding error: {e}")

        # Remove problematic characters using 'ascii' encoding
        sanitized_content = content.encode('ascii', 'ignore').decode('ascii')
        return sanitized_content

def replace_problematic_characters(content):
    # Replace or remove problematic characters
    replacements = {
        '\u2013': '-',  # en dash to hyphen
        '\u2014': '--',  # en dash to double hyphen
        '\u2018': "'",  # left single quotation mark to apostrophe
        '\u2019': "'",  # right single quotation mark to apostrophe
        '\u201c': '"',  # left double quotation mark to double quote
        '\u201d': '"',  # right double quotation mark to double quote
        '\u2026': '...',  # horizontal ellipsis
        '\u2010': '-',   # dash
        '\u2022': '*',   # bullet
        '\u2122': 'TM'  # TradeMark Symbol
    }

    for char, replacement in replacements.items():
        content = content.replace(char, replacement)

    return content

def generate_pdf_from_md(content, filename='output.pdf'):
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font('Arial', '', 12)

        sanitized_content = sanitize_content(content)
        sanitized_content = replace_problematic_characters(sanitized_content)

        lines = sanitized_content.split('\n')

        for line in lines:
            if line.startswith('#'):
                header_level = min(line.count('#'), 4)
                header_text = re.sub(r'\*{2,}', '', line.strip('# ').strip())
                pdf.set_font('Arial', 'B', 12 + (4 - header_level) * 2)
                pdf.multi_cell(0, 10, header_text)
                pdf.set_font('Arial', '', 12)
            else:
                parts = re.split(r'(\*\*\*.*?\*\*\*|\*\*.*?\*\*|\*.*?\*|\[.*?\]\(.*?\)|\([^ ]+?\))', line)
                for part in parts:
                    if re.match(r'\*\*\*.*?\*\*\*', part):  # Bold Italic
                        text = part.strip('*')
                        pdf.set_font('Arial', 'BI', 12)
                        pdf.write(10, text)
                    elif re.match(r'\*\*.*?\*\*', part):  # Bold
                        text = part.strip('*')
                        pdf.set_font('Arial', 'B', 12)
                        pdf.write(10, text)
                    elif re.match(r'\*.*?\*', part):  # Italic
                        text = part.strip('*')
                        pdf.set_font('Arial', 'I', 12)
                        pdf.write(10, text)
                    elif re.match(r'\[.*?\]\(.*?\)', part):  # Markdown-style link
                        display_text = re.search(r'\[(.*?)\]', part).group(1)
                        url = re.search(r'\((.*?)\)', part).group(1)
                        pdf.set_text_color(0, 0, 255)  # Set text color to blue
                        pdf.set_font('', 'U')
                        pdf.write(10, display_text, url)
                        pdf.set_text_color(0, 0, 0)  # Reset text color
                        pdf.set_font('Arial', '', 12)
                    # elif re.match(r'\([^ ]+?\)', part):  # Plain URL
                    #     url = part[1:-1]
                    #     pdf.set_text_color(0, 0, 255)  # Set text color to blue
                    #     pdf.set_font('', 'U')
                    #     pdf.write(10, url, url)
                    else:
                        pdf.write(10, part)
                    pdf.set_text_color(0, 0, 0)             # Reset text color
                    pdf.set_font('Arial', '', 12)   # Reset font

                pdf.ln(10)

        pdf.output(filename)
        return f"PDF generated: {filename}"

    except Exception as e:
        return f"Error generating PDF: {e}"