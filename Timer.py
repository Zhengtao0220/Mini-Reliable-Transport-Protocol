#
# Timer Utility
#

import time


class Timer:
    def __init__(self):
        """
        initialize the timer

        set the running state to False
        set the start time to 0
        """
        self.running = False
        self.start_time = 0

    def reset_timer(self):
        """
        reset the timer
        setting timer to running state, and start timer
        """
        self.running = True
        self.start_time = time.time()

    def stop_timer(self):
        """
        stop the timer
        setting the timer to stopping state
        """
        self.running = False

    def is_timeout(self):
        """
        check if timer is timeout
        return True if 0.5s after a timer reset, false otherwise
        """
        if not self.running:
            return False
        return (time.time() - self.start_time) >= 0.5

    def is_timeout_2s(self):
        """
        check if timer is timeout
        return True if 2.0s after a timer reset, false otherwise
        """
        if not self.running:
            return False
        return (time.time() - self.start_time) >= 2.0
