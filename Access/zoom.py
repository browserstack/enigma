from time import sleep

class Zoom:
  def __init__(self):
    self.name = "zoom"

  def grant(self, arg1):
    print("you are in zoom grant_access")
    sleep(5)
    return
  
  def revoke(self, arg1):
    print("you are in zoom revoke_access")
    sleep(5)
    return
  
  def on_success_grant(self):
    print("you are in zoom on_success_grant")
    sleep(5)
    return
  
  def on_fail_grant(self):
    print("you are in zoom on_fail_grant")
    sleep(5)
    return
  
  def on_success_revoke(self):
    print("you are in zoom on_success_revoke")
    sleep(5)
    return

  def on_fail_revoke(self):
    print("you are in zoom on_fail_revoke")
    sleep(5)
    return
