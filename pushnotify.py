from werkzeug.wrappers import Request, Response
import json,datetime,re
from commands import getstatusoutput as gso

payloads = json.loads(open('payloads.json','r').read())
mapre = re.compile('/([^\/]+)\/([^\/]+)$')

def actonpayload(payload,append):
    cmd = 'chdir %s ; %s'%(reposkeys[repo]['dir'],reposkeys[repo]['cmd'])
    st,op = gso(cmd)
    print 'command "%s" returned %s - %s'%(cmd,st,op)
    nwr = {'stamp':datetime.datetime.now().isoformat(),'payload':payload,'cmd_st':st,'cmd_op':op}
    if append:
        payloads.append(nwr) ; 
        fp = open('payloads.json','w') ; 
        fp.write(json.dumps(payloads)) ; 
        fp.close()
    print json.dumps(payload)
    print 'written payload to payloads.json'

@Request.application
def application(request):
    mapres = mapre.search(request.url)
    if not request.method=='POST' or not mapres:
        print 'authentication for %s failed'%repo
        r = Response('Auth failed',403)
        r.status_code = 403
    repo,key = mapres.groups()

    reposkeys = json.loads(open('repos_keys.json','r').read())
    if repo not in reposkeys or reposkeys[repo]['key']!=key:
        print 'authentication for %s failed'%repo
        r = Response('Auth failed',403)
        r.status_code = 403
        return r

    if 'payload' in request.form:
        try:
            payload = json.loads(request.form['payload'])
            actonpayload(payload,append=True)
            return Response('payload saved & acted upon.')
        except ValueError:
            print 'likely decoding failed. not doing a thing.'
    

    return Response('noop')

if __name__ == '__main__':
    import sys
    from werkzeug.serving import run_simple
    if len(sys.argv)>1 and sys.argv[1]=='testrun':
        for pl in payloads:
            raise Exception(pl)
    else:
        run_simple('85.17.122.213', 8081, application)
