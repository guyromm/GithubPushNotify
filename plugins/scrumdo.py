import re,json,dateutil
import MySQLdb as my
args = json.loads(open('mysql.json','r').read())
conn = my.connect(**args)

storyre = re.compile('#(\d+)')

def import_commit(repo,payload):
    for commit in payload['payload']['commits']:
        sres = storyre.search(commit['message'])
        fstoryid=None
        if sres:
            storyid = sres.group(1)
            c = conn.cursor()
            res = c.execute("select id from projects_story where id=%s",storyid)
            row = c.fetchone()
            if row:
                fstoryid = row[0]
                print 'found story id by direct method'
            else:
                #try to look by tag
                c.execute("select id from projects_storytag where name=%s","pivotal id %s"%storyid)
                res = c.fetchone()
                if res: 
                    tagid = res[0]
                    c.execute("select story_id from projects_storytagging where tag_id=%s",tagid)
                    res = c.fetchone()
                    if res:
                        fstoryid = res[0]
                        print 'found story %s by looking for pivotal tag %s'%(fstoryid,storyid)
            if fstoryid:
                print('want to tie this commit\'s story %s -> %s'%(storyid,fstoryid))
                userid=1
                import dateutil.parser
                pdate = dateutil.parser.parse(commit['timestamp'])
                message = commit['message']
                c.execute("select count(*) from threadedcomments_threadedcomment where user_id=%s and object_id=%s and comment=%s",(userid,fstoryid,message))
                excom = c.fetchone()[0]
                if not excom:
                    cres = c.execute("""insert into threadedcomments_threadedcomment (
                    content_type_id
                    ,object_id
                        ,user_id
                        ,date_submitted
                        ,comment
                        ,markup
                        ,is_public,is_approved,date_modified
                       ) values(
                        35 -- content type id
                        ,%s
                        ,%s -- user
                        ,%s -- date submitted
                        ,%s -- comment
                        ,5 -- markup
                        ,1 -- is public
                        ,0 -- is approved
                        ,%s
                        )""",(fstoryid,userid,pdate,message,pdate))
                    assert cres
                    print 'inserted commit comment %s -> %s'%(message,fstoryid)
                else:
                    print 'comment already exists.'
            else:
                print 'story %s from message "%s" does not match any scrumdo story'%(storyid,commit['message'])
