import re,json,dateutil
import pyfire
def publish_commit(repo,payload):
    print 'in campfire.publish_commit'
    args = json.loads(open('campfire.json','r').read())
    campfire = pyfire.Campfire(args['subdomain']+".campfirenow.com", args['login'], args['pass'], ssl=True)
    room = campfire.get_room_by_name(args['room'])
    room.join()
    print 'joined %s/#%s'%(args['subdomain'],args['room'])
    if 'payload' in payload:
        loopover = payload['payload']
    else:
        loopover = payload
    for commit in loopover['commits']:
        message = '%s commited to github: %s :\n %s'%(commit['author']['email'],commit['url'],commit['message'])
        print 'saying: %s'%message
        room.speak(message)

