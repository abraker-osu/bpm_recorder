if __name__ == '__main__':
    import sys
    import PyQt5

    from app import App

    app = PyQt5.QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(open('stylesheet.css').read())
    
    ex = App()
    sys.exit(app.exec_())
