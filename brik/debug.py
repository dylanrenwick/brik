class Debug:
    def __init__(self, debug=False):
        self.debug = debug
    def v_print(self, msg):
        if self.debug:
            print(msg)
