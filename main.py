import sys
import sympy
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPlainTextEdit, QSplitter,
    QVBoxLayout, QWidget, QLabel, QDockWidget, QToolBar,
    QAction, QFileDialog, QMessageBox, QColorDialog,
    QScrollArea, QShortcut
)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QImage, QKeySequence

##############################
# Canvas for Drawing
##############################
class CanvasWidget(QWidget):
    """
    A QWidget that manages a QImage for drawing (Pen, Highlighter, Eraser).
    White background by default. We also demonstrate a placeholder method
    to attempt handwriting recognition (not fully implemented).
    """
    def __init__(self, width=2000, height=2000, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)

        # QImage for drawing
        self.image = QImage(width, height, QImage.Format_ARGB32)
        self.image.fill(Qt.white)

        # Tools
        self.current_tool = 'pen'
        self.pen_color = QColor(0, 0, 0)
        self.highlight_color = QColor(255, 255, 0, 128)
        self.eraser_color = QColor(255, 255, 255)

        # Widths
        self.pen_width = 3
        self.highlighter_width = 20
        self.eraser_width = 20

        # Drawing state
        self.drawing = False
        self.last_point = QPoint()

    def setTool(self, tool_name):
        self.current_tool = tool_name

    def setPenColor(self, color: QColor):
        self.pen_color = color
        # Highlighter is semi‐transparent version of the chosen color
        self.highlight_color = QColor(color.red(), color.green(), color.blue(), 128)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            if self.current_tool == 'pen':
                pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            elif self.current_tool == 'highlighter':
                pen = QPen(self.highlight_color, self.highlighter_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            else:  # 'eraser'
                pen = QPen(self.eraser_color, self.eraser_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)

            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            painter.end()

            self.last_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False
            # Optionally, we could attempt to recognize if the user "wrote" a math expression
            # self.recognizeHandwritingExpression()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)

    def clearCanvas(self):
        self.image.fill(Qt.white)
        self.update()

    def saveCanvasAsImage(self, filename):
        self.image.save(filename)

    def recognizeHandwritingExpression(self):
        """
        Placeholder for a real OCR/ML approach that would interpret
        drawn strokes as a text expression like '2+2=', then parse with sympy.
        """
        # For real usage, you’d implement or call an OCR library here,
        # possibly Tesseract or a specialized handwriting model, to convert
        # the drawn region into text. Then parse with sympy to get a result.
        pass


##############################
# Scrollable Canvas
##############################
class InfiniteCanvas(QScrollArea):
    """A scrollable container for the CanvasWidget."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas_widget = CanvasWidget()
        self.setWidget(self.canvas_widget)
        self.setWidgetResizable(False)


##############################
# Main Window
##############################
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Notes + Drawing (Dark Notes, White Canvas)")

        # Splitter: left is notes (dark), right is a white drawing canvas
        self.splitter = QSplitter(Qt.Horizontal, self)

        # Left: dark-themed notes area
        self.notes_editor = QPlainTextEdit()
        # Force a dark style for the notes area
        self.notes_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b2b; 
                color: #ffffff;
                font-size: 14px;
            }
        """)
        self.notes_editor.setPlaceholderText("Type your notes here... (ends with '=' to auto-calc)")

        # Auto-eval typed math in the notes
        self.notes_editor.textChanged.connect(self.autoEvaluateTypedMath)

        notes_container = QWidget()
        notes_layout = QVBoxLayout()
        notes_layout.addWidget(QLabel("NOTES (dark theme):", parent=notes_container))
        notes_layout.addWidget(self.notes_editor)
        notes_container.setLayout(notes_layout)

        # Right: drawing canvas (white background)
        self.infinite_canvas = InfiniteCanvas()
        self.canvas = self.infinite_canvas.canvas_widget

        self.splitter.addWidget(notes_container)
        self.splitter.addWidget(self.infinite_canvas)
        self.setCentralWidget(self.splitter)

        # Tools dock
        self.tools_dock = QDockWidget("Tools", self)
        self.tools_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.tools_panel = self.createToolsPanel()
        self.tools_dock.setWidget(self.tools_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.tools_dock)

        # A "hamburger" menu to show/hide the dock
        self.hamburger_action = QAction("\u2630", self)  # "≋"
        self.hamburger_action.triggered.connect(self.toggleToolsDock)

        # Main toolbar (only the hamburger)
        self.main_toolbar = QToolBar("Main")
        self.main_toolbar.addAction(self.hamburger_action)
        self.addToolBar(self.main_toolbar)

        # Set initial geometry
        self.resize(1200, 800)

        # ---- Zoom shortcuts ----
        zoom_in_shortcut = QShortcut(QKeySequence("Ctrl++"), self)
        zoom_in_shortcut.activated.connect(self.handleZoomIn)

        zoom_out_shortcut = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_out_shortcut.activated.connect(self.handleZoomOut)

    ##########################
    # Tools Panel
    ##########################
    def createToolsPanel(self) -> QWidget:
        panel = QToolBar("Tools Panel")
        panel.setOrientation(Qt.Vertical)

        # Pen, Highlighter, Eraser
        pen_action = QAction("Pen", self)
        pen_action.triggered.connect(lambda: self.canvas.setTool("pen"))
        panel.addAction(pen_action)

        highlight_action = QAction("Highlighter", self)
        highlight_action.triggered.connect(lambda: self.canvas.setTool("highlighter"))
        panel.addAction(highlight_action)

        eraser_action = QAction("Eraser", self)
        eraser_action.triggered.connect(lambda: self.canvas.setTool("eraser"))
        panel.addAction(eraser_action)

        panel.addSeparator()

        # Color Picker
        color_action = QAction("Color Picker", self)
        color_action.triggered.connect(self.pickColor)
        panel.addAction(color_action)

        # Clear Canvas
        clear_action = QAction("Clear Canvas", self)
        clear_action.triggered.connect(self.canvas.clearCanvas)
        panel.addAction(clear_action)

        # Save to PDF
        save_pdf_action = QAction("Save as PDF", self)
        save_pdf_action.triggered.connect(self.saveAsPDF)
        panel.addAction(save_pdf_action)

        # Save Canvas (image)
        save_canvas_action = QAction("Save Canvas Img", self)
        save_canvas_action.triggered.connect(self.saveCanvasAsImage)
        panel.addAction(save_canvas_action)

        # Save Notes (text)
        save_notes_action = QAction("Save Notes Txt", self)
        save_notes_action.triggered.connect(self.saveNotesAsText)
        panel.addAction(save_notes_action)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(panel)
        w.setLayout(layout)
        return w

    def toggleToolsDock(self):
        visible = self.tools_dock.isVisible()
        self.tools_dock.setVisible(not visible)

    ##########################
    # Math in Notes (Typed)
    ##########################
    def autoEvaluateTypedMath(self):
        """
        If the last line in the notes ends with '=', attempt to parse the expression
        before '=' with sympy, and replace it with "expr=result".
        Example: "2+2=" becomes "2+2=4".
        """
        self.notes_editor.blockSignals(True)  # avoid recursion
        text = self.notes_editor.toPlainText()
        lines = text.split('\n')
        if lines:
            last_line = lines[-1]
            if last_line.endswith('='):
                expr = last_line[:-1].strip()
                if expr:
                    try:
                        result = sympy.sympify(expr)
                        lines[-1] = f"{expr}={result}"
                        updated_text = '\n'.join(lines)
                        self.notes_editor.setPlainText(updated_text)
                        # Move cursor to end
                        self.notes_editor.moveCursor(self.notes_editor.textCursor().End)
                    except Exception:
                        pass
        self.notes_editor.blockSignals(False)

    ##########################
    # Zoom
    ##########################
    def handleZoomIn(self):
        """
        Zoom in the notes text or, if desired, we could do
        a separate approach for the canvas. For now, let's just zoom the notes.
        (If you want canvas zoom, you'd implement scaling logic in CanvasWidget,
         similar to the previous examples.)
        """
        # We'll just zoom the notes. If you want to also zoom the canvas,
        # call self.canvas_zoomIn() or implement a scale factor.
        self.notes_editor.zoomIn(1)

    def handleZoomOut(self):
        self.notes_editor.zoomOut(1)

    ##########################
    # Color Picker
    ##########################
    def pickColor(self):
        from PyQt5.QtWidgets import QColorDialog
        color = QColorDialog.getColor(
            initial=self.canvas.pen_color,
            parent=self,
            title="Select Pen/Highlight Color"
        )
        if color.isValid():
            self.canvas.setPenColor(color)

    ##########################
    # Save PDF (notes + drawing)
    ##########################
    def saveAsPDF(self):
        """
        Export both notes + drawing to a single PDF page.
        We'll:
          1) Render the notes text to a QImage (or directly to QPainter),
          2) Render the canvas QImage,
          3) Paint them onto a single page with QPdfWriter.
        """
        filename, _ = QFileDialog.getSaveFileName(self, "Save as PDF", "", "PDF Files (*.pdf)")
        if not filename:
            return

        from PyQt5.QtGui import QPdfWriter
        from PyQt5.QtCore import QMarginsF

        pdf_writer = QPdfWriter(filename)
        pdf_writer.setPageSizeMM(pdf_writer.pageLayout().pageSize().size())  # default A4
        pdf_writer.setPageMargins(QMarginsF(10,10,10,10))

        painter = QPainter(pdf_writer)

        # Let’s define positions:
        # We'll put the NOTES text at the top half of the page,
        # and the drawing below it. Or side-by-side. Let's do top/bottom for simplicity.

        # 1) Render notes into an image
        #    We'll create a QPlainTextEdit "snapshot".
        notes_img = self.grabWidgetAsImage(self.notes_editor, bgColor=QColor("#2b2b2b"))
        # 2) Render canvas
        canvas_img = self.canvas.image  # The raw QImage of the drawing

        # We'll define how big each section is on the PDF page
        page_width = pdf_writer.width()  # in pixels, based on DPI
        page_height = pdf_writer.height()
        half_page_height = page_height // 2

        # Draw notes_img at top
        scaled_notes = notes_img.scaled(page_width, half_page_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawImage(0, 0, scaled_notes)

        # Draw canvas_img at bottom
        # We'll place it below the scaled_notes
        canvas_target_rect = QRect(0, half_page_height, page_width, half_page_height)
        scaled_canvas = canvas_img.scaled(canvas_target_rect.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawImage(canvas_target_rect.topLeft(), scaled_canvas)

        painter.end()
        QMessageBox.information(self, "PDF Saved", f"Successfully saved PDF to:\n{filename}")

    def grabWidgetAsImage(self, widget, bgColor=Qt.white):
        """
        Renders a given widget (like the notes editor) into a QImage, so we can
        combine it in the PDF. We can set a background color if needed.
        """
        # Create an offscreen image matching the widget size
        # We'll forcibly layout & render it.
        w = widget.width()
        h = widget.height()
        if w < 2: w = 400
        if h < 2: h = 300

        image = QImage(w, h, QImage.Format_ARGB32)
        image.fill(bgColor)

        painter = QPainter(image)
        widget.render(painter)
        painter.end()

        return image

    ##########################
    # Save Canvas as Image
    ##########################
    def saveCanvasAsImage(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Canvas Image", "",
                                                  "PNG Files (*.png);;All Files (*)")
        if filename:
            self.canvas.saveCanvasAsImage(filename)

    ##########################
    # Save Notes as Text
    ##########################
    def saveNotesAsText(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Notes", "",
                                                  "Text Files (*.txt);;All Files (*)")
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.notes_editor.toPlainText())


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
