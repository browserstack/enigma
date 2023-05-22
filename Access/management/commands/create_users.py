from Access.models import user as duser
import random, string

def randomword(length):
  letters = string.ascii_lowercase
  return ''.join(random.choice(letters) for i in range(length))


user_count = 50

for i in range(50):
  first_name = randomword(6)
  last_name = randomword(6)
  username = first_name+'.'+last_name
  email = username +'@gmail.com'

  duser.objects.create(username=username, first_name=first_name, last_name=last_name, email=email)
