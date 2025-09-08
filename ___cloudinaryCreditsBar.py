# This module is needed for PyQt5 to find the CloudinaryCreditsBar class
# when it's used as a promoted widget in Qt Designer

from ui.cloudinaryCreditsBar import CloudinaryCreditsBar

# Export the class so PyQt5 can find it
__all__ = ['CloudinaryCreditsBar']
