import subprocess
import tempfile
import os
from PySide6.QtGui import QImage, QPainter, QFont, QColor, QBrush
from PySide6.QtCore import QRectF, Qt

class Printer:
    """
    Brother PT-P700 Logic.
    Uses 'ptouch-print' CLI tool (must be installed on system).
    """
    def print_label(self, text: str):
        """
        Generates an image of the label and sends it to the printer.
        """
        print(f"Generating label for: {text}")
        
        # 1. Create Image (24mm tape is approx 128px printable height at 180dpi)
        height = 128
        # Estimate width based on text length (approx 15px per char + padding)
        width = max(100, len(text) * 25) 
        
        image = QImage(width, height, QImage.Format_Mono)
        image.fill(Qt.white)
        
        # 2. Draw Text
        painter = QPainter(image)
        painter.setPen(Qt.black)
        font = QFont("Arial", 40, QFont.Bold) # Large font for readability
        painter.setFont(font)
        
        # Center text
        rect = QRectF(0, 0, width, height)
        painter.drawText(rect, Qt.AlignCenter, text)
        painter.end()
        
        # 3. Save to Temp File
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image_path = tmp.name
            image.save(image_path)
            
        # 4. Print via ptouch-print
        try:
            # Note: User must have ptouch-print installed
            # https://git.git.bka.li/ptouch-print/ptouch-print.git
            subprocess.run(["ptouch-print", "--image", image_path], check=True)
            print(f"✅ Sent to printer: {text}")
        except FileNotFoundError:
            print("❌ Error: 'ptouch-print' not found. Please install it.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Printing failed: {e}")
        finally:
            # Cleanup
            if os.path.exists(image_path):
                os.remove(image_path)

