from datetime import datetime
import os


class K4Section:
    def __init__(self, lines, sums):
        self.lines = lines
        self.sums = sums


class K4Page:
    def __init__(self, year, personal_details, page_number,
                 section_a, section_c, section_d):
        self._year = year
        self._personal_details = personal_details
        self._page_number = page_number
        self._section_a = section_a
        self._section_c = section_c
        self._section_d = section_d

    def generate_sru_lines(self):
        k4_page_number_field = 7014

        blankettkod = f"K4-{self._year}P4"
        now = datetime.now()
        generated_date = now.strftime("%Y%m%d")
        generated_time = now.strftime("%H%M%S")

        lines = []
        lines.append(f"#BLANKETT {blankettkod}")
        lines.append(
            f"#IDENTITET {self._personal_details.personnummer.replace('-', '')} {generated_date} {generated_time}")
        lines.append(f"#NAMN {self._personal_details.namn}")
        lines.append(f"#UPPGIFT {k4_page_number_field} {self._page_number}")

        def generate_section(section, k4_base_field_code, k4_field_code_line_offset, k4_sum_field_codes):
            for (line_index, fields) in enumerate(section.lines):
                for (field_index, field) in enumerate(fields):
                    if field:
                        field_code = k4_base_field_code + k4_field_code_line_offset * line_index + field_index
                        lines.append(f"#UPPGIFT {field_code} {field}")
            for (index, field) in enumerate(section.sums):
                if field:
                    field_code = k4_sum_field_codes[index]
                    lines.append(f"#UPPGIFT {field_code} {field}")

        if self._section_a and self._section_a.lines:
            generate_section(self._section_a, 3100, 10, [3300, 3301, 3304, 3305])
        if self._section_c and self._section_c.lines:
            generate_section(self._section_c, 3310, 10, [3400, 3401, 3403, 3404])
        if self._section_d and self._section_d.lines:
            generate_section(self._section_d, 3410, 10, [3500, 3501, 3503, 3504])

        lines.append("#BLANKETTSLUT")

        return lines

    def generate_pdf(self, destination_folder):
        import io
        import pdfrw
        from reportlab.pdfgen import canvas

        field_x_positions = [58, 122, 217, 302, 388, 475]
        field_char_widths = [10, 14, 12, 12, 12, 12]
        field_yoffset = 24
        sumfield_addition_yoffset = 10

        def generate_section(pdf, section, maxlines, ystart):
            for (y, fields) in enumerate(section.lines):
                for (x, field) in enumerate(fields):
                    ys = ystart - field_yoffset * y
                    if field:
                        pdf.drawString(
                            x=field_x_positions[x],
                            y=ys,
                            text=field[:field_char_widths[x]]
                        )
            for (x, field) in enumerate(section.sums):
                if field:
                    pdf.drawString(
                        x=field_x_positions[x + 2],
                        y=ystart - field_yoffset * maxlines - sumfield_addition_yoffset,
                        text=field[:field_char_widths[x]]
                    )

        def generate_page_1_overlay():
            data = io.BytesIO()
            pdf = canvas.Canvas(data)
            pdf.setFont("Helvetica", 10)
            now = datetime.now()
            pdf.drawString(x=434, y=744, text=now.strftime("%Y-%m-%d"))
            pdf.drawString(x=434, y=708, text=str(self._page_number))
            pdf.drawString(x=46, y=660, text=self._personal_details.namn)
            pdf.drawString(x=434, y=660, text=self._personal_details.personnummer)
            if self._section_a and self._section_a.lines:
                generate_section(pdf, self._section_a, 9, 588)
            pdf.save()
            data.seek(0)
            return data

        def generate_page_2_overlay():
            data = io.BytesIO()
            pdf = canvas.Canvas(data)
            pdf.setFont("Helvetica", 10)
            pdf.drawString(x=434, y=792, text=self._personal_details.personnummer)
            if self._section_c and self._section_c.lines:
                generate_section(pdf, self._section_c, 7, 720)
            if self._section_d and self._section_d.lines:
                generate_section(pdf, self._section_d, 7, 360)
            pdf.save()
            data.seek(0)
            return data

        def merge(overlay_canvases, template_path):
            template_pdf = pdfrw.PdfReader(template_path)
            overlay_pdfs = [pdfrw.PdfReader(x) for x in overlay_canvases]
            for page, data in zip(template_pdf.pages, overlay_pdfs):
                overlay = pdfrw.PageMerge().add(data.pages[0])[0]
                pdfrw.PageMerge(page).add(overlay).render()
            form = io.BytesIO()
            pdfrw.PdfWriter().write(form, template_pdf)
            form.seek(0)
            return form

        def save(form, filename):
            with open(filename, 'wb') as f:
                f.write(form.read())

        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        pagestr = "%02d" % self._page_number

        template_filename = f"docs/K4-template-{self._year}.pdf"
        if not os.path.exists(template_filename):
            raise Exception(f"K4 template pdf for {self._year} not available at {template_filename}")
        form = merge([generate_page_1_overlay(), generate_page_2_overlay()], template_path=template_filename)
        save(form, filename=f"{destination_folder}/k4_no{pagestr}.pdf")
