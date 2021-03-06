from werkzeug.wrappers import Request, Response
import json,datetime,re
from commands import getstatusoutput as gso

payloads = json.loads(open('payloads.json','r').read())
reposkeys = json.loads(open('repos_keys.json','r').read())
mapre = re.compile('/([^\/]+)\/([^\/]+)$')

def actonpayload(repo,payload,append,runcmd=True,executemod=True):
    if runcmd and 'cmd' in reposkeys[repo]:
        cmd = 'chdir %s ; %s'%(reposkeys[repo]['dir'],reposkeys[repo]['cmd'])
        st,op = gso(cmd)
        print 'command "%s" returned %s - %s'%(cmd,st,op)
    else:
        if runcmd:
            print 'no command set to run for this hook'
        st=-1 ; op = None
    if executemod and repo in reposkeys and 'execute' in reposkeys[repo]:
        if (type(reposkeys[repo]['execute'])!=list):
            execs = [reposkeys[repo]['execute']]
        else:
            execs = reposkeys[repo]['execute']
        for execitem in execs:
            mod,func = execitem.split('::')
            modi = __import__(mod)
            exec_func = getattr(getattr(modi,mod.split('.')[-1]),func)
            exec_func(repo,payload)
                
        
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
        print 'authentication failed of %s'%request.url
        r = Response('Auth failed',403)
        r.status_code = 403
        return r
    disregard,key = mapres.groups()

    if 'payload' in request.form:
        try:
            payload = json.loads(request.form['payload'])

            repo = payload['repository']['name']

            if repo not in reposkeys or reposkeys[repo]['key']!=key:
                print 'authentication for %s failed - %s<>%s'%(repo,key,reposkeys[repo]['key'])
                r = Response('Auth failed',403)
                r.status_code = 403
                return r


            actonpayload(repo,payload,append=True)
            return Response('payload saved & acted upon.')
        except ValueError:
            print 'likely decoding failed. not doing a thing.'
    

    return Response('noop')


if __name__ == '__main__':
    import sys
    from werkzeug.serving import run_simple
    if len(sys.argv)>1 and sys.argv[1]=='testrun':
        if len(sys.argv)>2:
            reposkeys = json.loads(open(sys.argv[2],'r').read())
            print 'read repos off %s'%sys.argv[2] 
        cnt=0
        for pl in payloads:
            repo = pl['payload']['repository']['name']
            actonpayload(repo,pl,append=False,runcmd=False)
            cnt+=1
        print '%s payloads processed'%(cnt)
    else:
        run_simple('0.0.0.0',8081, application)
